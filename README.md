# Agentic Deep Researcher

We're building an MCP-powered multi-agent deep researcher, it can perform deep web searches using [Linkup](https://www.linkup.so/) amd the agents are orchestrated using CrewAI.

We use:

- [LinkUp](https://www.linkup.so/) (Search Tool)
- CrewAI (Agentic design)
- Gemini (LLM)
- Streamlit to wrap the logic in an interactive UI

### SetUp

Run these commands in project root

```
uv sync
```


### Run the Application

Run the application with:

```bash
streamlit run app.py
```

### Use as MCP server

```json
{
  "mcpServers": {
    "crew_research": {
      "command": "uv",
      "args": [
        "--directory",
        "./Multi-Agent-deep-researcher-mcp-windows-linux",
        "run",
        "server.py"
      ],
      "env": {
        "LINKUP_API_KEY": "your_linkup_api_key_here",
        "GEMINI_API_KEY": "your_gEMINI_API_KEY"
      }
    }
  }
}
```
[Get your Linkup API keys here](https://www.linkup.so/)
