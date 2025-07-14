import streamlit as st
from agents import run_research
import os
from datetime import datetime
import base64
from io import BytesIO
import markdown
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import re
import time

st.set_page_config(
    page_title="🔍 Agentic Deep Researcher",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "linkup_api_key" not in st.session_state:
    st.session_state.linkup_api_key = ""
if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = ""
if "messages" not in st.session_state:
    st.session_state.messages = []


def reset_chat():
    st.session_state.messages = []


def estimate_word_count(content):
    clean_content = re.sub(r'[*#`]', '', content)
    clean_content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean_content)
    words = clean_content.split()
    return len(words)


def create_download_link(content, filename, file_format="txt"):
    if file_format == "txt":
        clean_content = re.sub(r'[*#`]', '', content)
        clean_content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean_content)
        b64 = base64.b64encode(clean_content.encode()).decode()
        href = f'<a href="data:text/plain;base64,{b64}" download="{filename}.txt">📄 Download as Text</a>'
    elif file_format == "md":
        b64 = base64.b64encode(content.encode()).decode()
        href = f'<a href="data:text/markdown;base64,{b64}" download="{filename}.md">📝 Download as Markdown</a>'
    return href


def create_pdf_report(content, query):
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=30,
                                     textColor='#0066cc')
        heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=14, spaceAfter=12,
                                       textColor='#0066cc')

        story = [
            Paragraph("Agentic Deep Research Report", title_style),
            Spacer(1, 12),
            Paragraph(f"<b>Research Query:</b> {query}", styles['Normal']),
            Spacer(1, 12),
            Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']),
            Paragraph(f"<b>Word Count:</b> {estimate_word_count(content)} words", styles['Normal']),
            Spacer(1, 20),
            Paragraph("Research Results:", heading_style),
            Spacer(1, 12)
        ]

        for line in content.split('\n'):
            if line.strip():
                if line.startswith('# '):
                    story.append(Paragraph(line[2:], heading_style))
                    story.append(Spacer(1, 12))
                elif line.startswith('## '):
                    story.append(Paragraph(line[3:], styles['Heading3']))
                    story.append(Spacer(1, 8))
                elif line.startswith('### '):
                    story.append(Paragraph(line[4:], styles['Heading4']))
                    story.append(Spacer(1, 6))
                else:
                    clean_line = re.sub(r'[*#`]', '', line)
                    clean_line = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean_line)
                    story.append(Paragraph(clean_line.strip(), styles['Normal']))
                    story.append(Spacer(1, 8))

        doc.build(story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"❌ PDF generation failed: {e}")
        return BytesIO(b"PDF generation failed. Please try again.")


def display_download_options(content, query):
    st.markdown("---")
    word_count = estimate_word_count(content)
    char_count = len(content)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Word Count", f"{word_count:,}")
    with col2:
        st.metric("📄 Characters", f"{char_count:,}")
    with col3:
        st.metric("📖 Estimated Pages", max(1, round(word_count / 500)))

    st.subheader("📅 Download Report")
    col1, col2, col3 = st.columns(3)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"research_report_{timestamp}"

    with col1:
        st.markdown(create_download_link(content, filename, "txt"), unsafe_allow_html=True)
    with col2:
        st.markdown(create_download_link(content, filename, "md"), unsafe_allow_html=True)
    with col3:
        pdf_buffer = create_pdf_report(content, query)
        pdf_data = pdf_buffer.getvalue()
        if pdf_data:
            st.download_button(
                label="📄 Download as PDF",
                data=pdf_data,
                file_name=f"{filename}.pdf",
                mime="application/pdf"
            )
        else:
            st.error("❌ Failed to generate PDF. Please try again.")


# Updated CSS with better content rendering
st.markdown("""
<style>
    .main-content { max-width: none; }
    .stChatMessage { max-width: none; }
    .research-content {
        max-height: 600px;
        overflow-y: auto;
        padding: 20px;
        background-color: #f8f9fa;
        border-radius: 10px;
        margin: 10px 0;
        white-space: pre-wrap;
        word-wrap: break-word;
        line-height: 1.6;
    }
    .status-indicator {
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
        font-weight: bold;
    }
    .status-success {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    .status-warning {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.image("https://avatars.githubusercontent.com/u/175112039?s=200&v=4", width=65)
    st.header("Configuration")
    st.write("API Keys Setup")

    st.markdown("---")
    st.markdown("### 🔧 Research Settings")
    st.info("Enhanced reports with comprehensive searches")

    st.markdown("### Linkup API")
    st.markdown("[Get your Linkup API key](https://app.linkup.so/sign-up)", unsafe_allow_html=True)
    linkup_api_key = st.text_input("Enter your Linkup API Key", type="password")
    if linkup_api_key:
        st.session_state.linkup_api_key = linkup_api_key
        os.environ["LINKUP_API_KEY"] = linkup_api_key
        st.success("Linkup API Key stored successfully!")

    st.markdown("### Gemini API")
    st.markdown("[Get your Gemini API key](https://aistudio.google.com/app/apikey)", unsafe_allow_html=True)
    gemini_api_key = st.text_input("Enter your Gemini API Key", type="password")
    if gemini_api_key:
        st.session_state.gemini_api_key = gemini_api_key
        os.environ["GEMINI_API_KEY"] = gemini_api_key
        st.success("Gemini API Key stored successfully!")

    st.markdown("---")
    st.markdown("### 💡 Tips for Better Results")
    st.markdown("""
    - Be specific in your queries
    - Include context or time frames
    - Ask for analysis, not just facts
    - Research may take 2-5 minutes
    - Reports target 1500-2000 words
    """)

col1, col2 = st.columns([6, 1])
with col1:
    st.markdown("<h2 style='color: #0066cc;'>🔍 Agentic Deep Researcher</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='color: #666;'>Enhanced for Comprehensive Reports</h4>", unsafe_allow_html=True)
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 10px; margin-top: 5px;'>
        <span style='font-size: 16px; color: #666;'>Powered by</span>
        <img src="https://cdn.prod.website-files.com/66cf2bfc3ed15b02da0ca770/66d07240057721394308addd_Logo%20(1).svg" width="60"> 
        <span style='font-size: 16px; color: #666;'>and</span>
        <img src="https://framerusercontent.com/images/wLLGrlJoyqYr9WvgZwzlw91A8U.png?scale-down-to=512" width="80">
        <span style='font-size: 16px; color: #666;'>with</span>
        <img src="https://upload.wikimedia.org/wikipedia/commons/8/8a/Google_Gemini_logo.svg" width="60">
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.button("Clear ↺", on_click=reset_chat)

st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

# Fixed message display loop
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant" and len(message["content"]) > 1000:
            # Fixed: Use expander for better UX and proper content rendering
            with st.expander("📄 View Full Report", expanded=True):
                st.markdown(message["content"])
        else:
            st.markdown(message["content"])

if prompt := st.chat_input("Ask a research question for a comprehensive 2-3 page report..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if not st.session_state.linkup_api_key:
        response = "⚠️ Please enter your Linkup API Key in the sidebar to start research."
    elif not st.session_state.gemini_api_key:
        response = "⚠️ Please enter your Gemini API Key in the sidebar to start research."
    else:
        with st.spinner("🔍 Conducting comprehensive research... This may take 2-5 minutes for a detailed report..."):
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                status_text.text("🔍 Initializing research system...")
                progress_bar.progress(20)

                status_text.text("🌐 Conducting web searches...")
                progress_bar.progress(40)

                result = run_research(prompt)

                status_text.text("📝 Analyzing and writing report...")
                progress_bar.progress(80)

                response = result

                status_text.text("✅ Research complete!")
                progress_bar.progress(100)

                time.sleep(1)
                progress_bar.empty()
                status_text.empty()

            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                response = f"❌ An error occurred during research: {str(e)}"

    # Fixed assistant response display
    with st.chat_message("assistant"):
        if len(response) > 1000:
            word_count = estimate_word_count(response)
            if word_count >= 1000:
                st.markdown(
                    f'<div class="status-indicator status-success">✅ Comprehensive report generated: {word_count:,} words</div>',
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div class="status-indicator status-warning">⚠️ Report generated but may be shorter than expected: {word_count:,} words</div>',
                    unsafe_allow_html=True)

            # Fixed: Use expander for better UX and remove html.escape
            with st.expander("📄 View Full Report", expanded=True):
                st.markdown(response)
        else:
            st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})

    if (response and not response.startswith("⚠️") and not response.startswith("❌") and len(response) > 500):
        display_download_options(response, prompt)