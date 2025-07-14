import os
import time
from typing import Type
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import BaseTool

# Load environment variables (for non-LinkUp settings)
load_dotenv()

# Try to import LinkupClient with error handling
try:
    from linkup import LinkupClient

    LINKUP_AVAILABLE = True
except ImportError as e:
    print(f"Warning: LinkupClient import failed: {e}")
    print("Please install linkup-sdk: pip install linkup-sdk")
    LINKUP_AVAILABLE = False


def get_llm_client():
    """Initialize and return the Gemini LLM client with enhanced settings for longer content"""
    return LLM(
        model="gemini/gemini-2.5-pro",
        api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.4,  # Slightly higher for more varied content
        max_tokens=4000,  # Increased from 1500 to allow longer responses
        request_timeout=120,  # Increased timeout for longer processing
        max_retries=3,
    )


# Define LinkUp Search Tool with enhanced result handling
class LinkUpSearchInput(BaseModel):
    """Input schema for LinkUp Search Tool."""
    query: str = Field(description="The search query to perform")
    depth: str = Field(default="standard",
                       description="Depth of search: 'standard' or 'deep'")
    output_type: str = Field(
        default="searchResults", description="Output type: 'searchResults', 'sourcedAnswer', or 'structured'")


# Global search counter - increased limit for more comprehensive research
_global_search_count = 0
_max_searches = 5  # Increased from 3 to 5 for more thorough research


def reset_search_counter():
    """Reset the global search counter for a new research session"""
    global _global_search_count
    _global_search_count = 0


def increment_search_counter():
    """Increment and return the current search count"""
    global _global_search_count
    _global_search_count += 1
    return _global_search_count


def get_search_count():
    """Get the current search count"""
    global _global_search_count
    return _global_search_count


class LinkUpSearchTool(BaseTool):
    name: str = "LinkUp Search"
    description: str = "Search the web for information using LinkUp and return comprehensive results (max 5 searches per session)"
    args_schema: Type[BaseModel] = LinkUpSearchInput

    def __init__(self):
        super().__init__()
        if not LINKUP_AVAILABLE:
            raise ImportError("LinkupClient is not available. Please install linkup-sdk: pip install linkup-sdk")

    def _run(self, query: str, depth: str = "standard", output_type: str = "searchResults") -> str:
        """Execute LinkUp search with enhanced result handling for comprehensive research."""
        if not LINKUP_AVAILABLE:
            return "Error: LinkupClient is not available. Please install linkup-sdk: pip install linkup-sdk"

        # Enforce search limit using global counter
        current_count = get_search_count()
        if current_count >= _max_searches:
            return f"Maximum search limit ({_max_searches}) reached. Please analyze existing results."

        try:
            # Check if API key is available
            api_key = os.getenv("LINKUP_API_KEY")
            if not api_key:
                return "Error: LINKUP_API_KEY environment variable not set"

            # Initialize LinkUp client with API key from environment variables
            linkup_client = LinkupClient(api_key=api_key)

            # Add delay to prevent rate limiting
            time.sleep(1.5)

            # Perform search - use deep search for every 3rd query for more comprehensive results
            search_depth = "deep" if (current_count + 1) % 3 == 0 else "standard"

            search_response = linkup_client.search(
                query=query,
                depth=search_depth,
                output_type=output_type
            )

            # Increment counter and get new count
            new_count = increment_search_counter()

            # Enhanced result handling - keep more content but still prevent overflow
            response_str = str(search_response)
            if len(response_str) > 4000:  # Increased from 2000 to 4000 for more content
                response_str = response_str[
                               :4000] + f"\n... [Results truncated at 4000 chars for efficiency, search {new_count} using {search_depth} depth]"

            return f"Search {new_count}/{_max_searches} ({search_depth} depth):\n{response_str}"

        except Exception as e:
            return f"Error occurred while searching: {str(e)}"


def create_research_crew(query: str):
    """Create and configure the research crew for comprehensive 2-3 page reports"""

    # Check if LinkUp is available
    if not LINKUP_AVAILABLE:
        raise ImportError("LinkupClient is not available. Please install linkup-sdk: pip install linkup-sdk")

    # Check if API keys are available
    if not os.getenv("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY environment variable not set")

    if not os.getenv("LINKUP_API_KEY"):
        raise ValueError("LINKUP_API_KEY environment variable not set")

    # Initialize tools
    linkup_search_tool = LinkUpSearchTool()

    # Get LLM client
    client = get_llm_client()

    # Enhanced web searcher agent for comprehensive research
    web_searcher = Agent(
        role="Comprehensive Web Researcher",
        goal="Conduct thorough research using 5 strategic searches to gather comprehensive information.",
        backstory="You are an expert researcher who conducts systematic, multi-angle investigations. You search for overview, details, recent developments, statistics, and expert opinions to build a complete picture.",
        verbose=True,  # Enabled for better tracking
        allow_delegation=False,
        tools=[linkup_search_tool],
        llm=client,
        max_execution_time=300,  # Increased from 180 to 300 seconds
        max_iter=3,  # Increased iterations for thoroughness
    )

    # Enhanced research analyst and writer for longer content
    research_writer = Agent(
        role="Comprehensive Research Writer",
        goal="Create detailed, well-structured research reports of 2-3 pages from search results.",
        backstory="You are a skilled research writer who creates comprehensive, well-organized reports. You excel at synthesizing multiple sources into coherent, detailed analyses with proper structure and citations.",
        verbose=True,  # Enabled for better tracking
        allow_delegation=False,
        tools=[],
        llm=client,
        max_execution_time=240,  # Increased from 120 to 240 seconds
        max_iter=2,  # Allow for revision
    )

    # Enhanced search task for comprehensive research
    search_task = Task(
        description=f"""
        Conduct comprehensive research about: {query}

        Execute 5 strategic searches covering:
        1. Main topic overview and background
        2. Current statistics, data, and trends
        3. Recent developments and news
        4. Expert opinions and analysis
        5. Detailed aspects and implications

        For each search:
        - Use specific, targeted queries
        - Focus on authoritative sources
        - Gather both quantitative and qualitative data
        - Note publication dates and source credibility
        - Collect supporting evidence and examples

        Ensure comprehensive coverage of the topic from multiple angles.
        """,
        agent=web_searcher,
        expected_output="Comprehensive search results from 5 strategic searches covering different aspects of the topic with detailed information and credible sources.",
        tools=[linkup_search_tool],
        max_execution_time=300
    )

    # Enhanced analysis task for detailed report
    analysis_writing_task = Task(
        description=f"""
        Create a comprehensive research report about: {query}

        Requirements:
        - Target length: 1500-2000 words (2-3 pages)
        - Use ALL provided search results effectively
        - Create a well-structured report with clear sections:
          * Executive Summary (150-200 words)
          * Introduction and Background (300-400 words)
          * Key Findings and Analysis (600-800 words)
          * Current Trends and Developments (300-400 words)
          * Conclusion and Implications (200-300 words)

        Content guidelines:
        - Include specific data, statistics, and examples
        - Cite sources appropriately throughout
        - Provide balanced analysis with multiple perspectives
        - Use clear headings and subheadings
        - Include relevant quotes from experts (if available)
        - Maintain professional, informative tone
        - Ensure logical flow between sections

        Format as markdown with proper headings and formatting.
        """,
        agent=research_writer,
        expected_output="A comprehensive 1500-2000 word research report with clear structure, detailed analysis, and proper citations.",
        context=[search_task],
        max_execution_time=240
    )

    # Create the crew with enhanced settings
    crew = Crew(
        agents=[web_searcher, research_writer],
        tasks=[search_task, analysis_writing_task],
        verbose=True,  # Enabled for better tracking
        process=Process.sequential,
        max_execution_time=600,  # Increased from 360 to 600 seconds (10 minutes)
        memory=False,
    )

    return crew


def run_research(query: str):
    """Run the enhanced research process for comprehensive 2-3 page reports"""
    max_retries = 3
    retry_delay = 3  # Increased delay for stability

    for attempt in range(max_retries):
        try:
            # Reset search counter for new research session
            reset_search_counter()

            # Add delay between attempts
            if attempt > 0:
                time.sleep(retry_delay * attempt)

            crew = create_research_crew(query)
            result = crew.kickoff()

            # Ensure we have substantial content
            if len(result.raw) < 500:
                return f"Research completed but content seems limited. Here's what was found:\n\n{result.raw}\n\n[Note: For more comprehensive results, try refining your query or checking API limits]"

            return result.raw

        except Exception as e:
            error_msg = str(e).lower()

            # Check for rate limiting or overload errors
            if "overloaded" in error_msg or "rate limit" in error_msg or "quota" in error_msg:
                if attempt < max_retries - 1:
                    print(f"Rate limit encountered, waiting {retry_delay * (attempt + 1)} seconds...")
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    return f"API Rate Limited: The Gemini API is currently overloaded. Please try again in a few minutes. For comprehensive research, consider:\n\n1. Breaking your query into smaller, more specific questions\n2. Trying again during off-peak hours\n3. Using more specific search terms"

            # Handle other errors
            if attempt < max_retries - 1:
                print(f"Error on attempt {attempt + 1}, retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                continue
            else:
                if "ImportError" in str(type(e)):
                    return f"Import Error: {str(e)}\nPlease install linkup-sdk: pip install linkup-sdk"
                elif "ValueError" in str(type(e)):
                    return f"Configuration Error: {str(e)}"
                else:
                    return f"Error: {str(e)}\n\nTroubleshooting tips:\n1. Try simplifying your query\n2. Check your API key configurations\n3. Ensure stable internet connection\n4. Try breaking complex queries into smaller parts"

    return "Maximum retries exceeded. Please try again later or contact support if the issue persists."