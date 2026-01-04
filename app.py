"""BrandGuard: Autonomous Marketing Content Generator

A Streamlit UI for the BrandGuard autonomous agent.
Features an editorial, sophisticated dark-mode aesthetic.
"""

import asyncio
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

import streamlit as st

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.runner import run_with_guardrails, analyze_run
from src.rag.ingest import ingest_documents

# ============================================================================
# Page Configuration & Styling
# ============================================================================

st.set_page_config(
    page_title="BrandGuard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for editorial aesthetic
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&display=swap');

    /* Root variables */
    :root {
        --bg-primary: #0a0a0b;
        --bg-secondary: #111113;
        --bg-tertiary: #18181b;
        --bg-hover: #1f1f23;
        --text-primary: #fafafa;
        --text-secondary: #a1a1aa;
        --text-muted: #52525b;
        --accent: #10b981;
        --accent-hover: #34d399;
        --warning: #f59e0b;
        --error: #ef4444;
        --border: #27272a;
        --border-light: #3f3f46;
    }

    /* Global overrides */
    .stApp {
        background: var(--bg-primary);
        font-family: 'DM Sans', sans-serif;
    }

    /* Hide default Streamlit elements */
    #MainMenu, footer, header {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Main container */
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1400px;
    }

    /* Typography */
    h1, h2, h3 {
        font-family: 'Instrument Serif', serif !important;
        font-weight: 400 !important;
        letter-spacing: -0.02em;
    }

    h1 {
        font-size: 2.75rem !important;
        color: var(--text-primary) !important;
        margin-bottom: 0.25rem !important;
    }

    h2 {
        font-size: 1.75rem !important;
        color: var(--text-primary) !important;
    }

    h3 {
        font-size: 1.25rem !important;
        color: var(--text-secondary) !important;
    }

    p, label, .stMarkdown {
        color: var(--text-secondary) !important;
        font-size: 0.9rem;
    }

    /* Input styling */
    .stTextInput input, .stTextArea textarea, .stDateInput input, .stSelectbox select {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
        font-family: 'DM Sans', sans-serif !important;
        padding: 0.75rem 1rem !important;
    }

    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.15) !important;
    }

    /* Multiselect */
    .stMultiSelect > div > div {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
    }

    .stMultiSelect span[data-baseweb="tag"] {
        background: var(--accent) !important;
        border-radius: 4px !important;
    }

    /* Buttons */
    .stButton > button {
        background: var(--accent) !important;
        color: var(--bg-primary) !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        font-family: 'DM Sans', sans-serif !important;
        transition: all 0.2s ease !important;
        width: 100%;
    }

    .stButton > button:hover {
        background: var(--accent-hover) !important;
        transform: translateY(-1px);
    }

    .stButton > button[kind="secondary"] {
        background: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-secondary);
        border-radius: 8px;
        padding: 4px;
        gap: 4px;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: var(--text-secondary);
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }

    .stTabs [aria-selected="true"] {
        background: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
        font-weight: 500;
    }

    .streamlit-expanderContent {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
    }

    /* Metrics */
    .stMetric {
        background: var(--bg-secondary);
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid var(--border);
    }

    .stMetric label {
        color: var(--text-muted) !important;
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }

    .stMetric [data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
        font-family: 'Instrument Serif', serif !important;
        font-size: 2rem !important;
    }

    /* Custom components */
    .brand-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 2rem;
        padding-bottom: 1.5rem;
        border-bottom: 1px solid var(--border);
    }

    .brand-logo {
        width: 48px;
        height: 48px;
        background: linear-gradient(135deg, var(--accent) 0%, #059669 100%);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
    }

    .brand-title {
        font-family: 'Instrument Serif', serif;
        font-size: 1.75rem;
        color: var(--text-primary);
        margin: 0;
    }

    .brand-subtitle {
        font-size: 0.875rem;
        color: var(--text-muted);
        margin: 0;
    }

    .score-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.875rem;
    }

    .score-high {
        background: rgba(16, 185, 129, 0.15);
        color: var(--accent);
    }

    .score-medium {
        background: rgba(245, 158, 11, 0.15);
        color: var(--warning);
    }

    .score-low {
        background: rgba(239, 68, 68, 0.15);
        color: var(--error);
    }

    .content-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }

    .content-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid var(--border);
    }

    .channel-icon {
        width: 32px;
        height: 32px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
    }

    .channel-linkedin { background: #0077b5; }
    .channel-facebook { background: #1877f2; }
    .channel-email { background: #6366f1; }
    .channel-web { background: #8b5cf6; }

    .tool-sequence {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        padding: 1rem;
        background: var(--bg-tertiary);
        border-radius: 8px;
    }

    .tool-badge {
        padding: 0.375rem 0.75rem;
        background: var(--bg-primary);
        border: 1px solid var(--border);
        border-radius: 4px;
        font-size: 0.75rem;
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-secondary);
    }

    .tool-arrow {
        color: var(--text-muted);
        align-self: center;
    }

    .claim-verified {
        color: var(--accent);
    }

    .claim-unverified {
        color: var(--error);
    }

    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 500;
    }

    .status-success {
        background: rgba(16, 185, 129, 0.15);
        color: var(--accent);
    }

    .status-warning {
        background: rgba(245, 158, 11, 0.15);
        color: var(--warning);
    }

    .status-error {
        background: rgba(239, 68, 68, 0.15);
        color: var(--error);
    }

    /* Code blocks */
    .stCodeBlock {
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
    }

    /* Divider */
    hr {
        border: none;
        border-top: 1px solid var(--border);
        margin: 2rem 0;
    }

    /* Image styling */
    .stImage {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid var(--border);
    }

    /* Spinner */
    .stSpinner > div {
        border-color: var(--accent) !important;
    }

    /* DataFrame */
    .stDataFrame {
        background: var(--bg-secondary);
        border-radius: 8px;
        overflow: hidden;
    }

    .stDataFrame thead th {
        background: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
    }

    .stDataFrame tbody td {
        color: var(--text-secondary) !important;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# Sample Data
# ============================================================================

SAMPLE_EVENTS = [
    {
        "title": "Zero Trust Security Webinar",
        "description": "Join our expert panel to learn practical strategies for implementing Zero Trust architecture in your organization. We'll cover identity verification, micro-segmentation, and continuous monitoring.",
        "date": date(2026, 2, 15),
        "audience": "IT Security professionals, CISOs, and Security Architects",
        "messages": "Zero Trust is essential for modern security\nImplementation doesn't have to be complex\nReal-world case studies from Fortune 500 companies",
        "channels": ["linkedin", "email"],
        "urls": "Register Now | https://example.com/zerotrust-webinar"
    },
    {
        "title": "AI & Machine Learning Summit 2026",
        "description": "The premier event for AI practitioners. Two days of hands-on workshops, keynotes from industry leaders, and networking opportunities with the AI community.",
        "date": date(2026, 3, 20),
        "audience": "Data Scientists, ML Engineers, and AI Product Managers",
        "messages": "Learn from top AI researchers\nHands-on workshops with real datasets\nNetwork with 500+ AI practitioners",
        "channels": ["linkedin", "facebook", "email", "web"],
        "urls": "Get Tickets | https://example.com/ai-summit\nView Agenda | https://example.com/ai-summit/agenda"
    },
    {
        "title": "Cloud Migration Masterclass",
        "description": "A comprehensive workshop on migrating legacy applications to the cloud. Learn best practices for AWS, Azure, and GCP migrations with minimal downtime.",
        "date": date(2026, 4, 10),
        "audience": "DevOps Engineers, Cloud Architects, and IT Managers",
        "messages": "Reduce migration risk by 80%\nHands-on labs with real infrastructure\nGet certified in cloud migration",
        "channels": ["linkedin", "email", "web"],
        "urls": "Enroll Now | https://example.com/cloud-masterclass"
    }
]


# ============================================================================
# Helper Functions
# ============================================================================

def get_score_class(score: int) -> str:
    """Get CSS class based on score value."""
    if score >= 7:
        return "score-high"
    elif score >= 5:
        return "score-medium"
    return "score-low"


def get_channel_icon(channel: str) -> str:
    """Get emoji icon for channel."""
    icons = {
        "linkedin": "💼",
        "facebook": "📘",
        "email": "✉️",
        "web": "🌐"
    }
    return icons.get(channel, "📄")


def strip_citations(text: str) -> str:
    """Remove [source: chunk_xxx] citations for clean copy."""
    import re
    return re.sub(r'\s*\[source:\s*\w+\]', '', text)


def parse_urls(urls_text: str) -> list[dict]:
    """Parse URLs from 'Label | URL' format."""
    urls = []
    for line in urls_text.strip().split("\n"):
        if "|" in line:
            parts = line.split("|", 1)
            if len(parts) == 2:
                urls.append({
                    "label": parts[0].strip(),
                    "url": parts[1].strip()
                })
    return urls


async def generate_content(event_brief: dict) -> dict:
    """Run the agent and return results."""
    return await run_with_guardrails(event_brief)


# ============================================================================
# Main App
# ============================================================================

def main():
    # Header
    st.markdown("""
    <div class="brand-header">
        <div class="brand-logo">🛡️</div>
        <div>
            <p class="brand-title">BrandGuard</p>
            <p class="brand-subtitle">Autonomous Marketing Content Generator</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Initialize session state
    if "result" not in st.session_state:
        st.session_state.result = None
    if "sample_data" not in st.session_state:
        st.session_state.sample_data = None

    # Two-column layout
    col_input, col_output = st.columns([1, 1.5], gap="large")

    # ========================================================================
    # Input Column
    # ========================================================================
    with col_input:
        st.markdown("## Event Details")
        st.markdown("*Fill in the details for your marketing content*")

        # Sample data button
        sample_cols = st.columns([1, 1, 1])
        with sample_cols[0]:
            if st.button("🎲 Sample 1", use_container_width=True, type="secondary"):
                st.session_state.sample_data = SAMPLE_EVENTS[0]
                st.rerun()
        with sample_cols[1]:
            if st.button("🎲 Sample 2", use_container_width=True, type="secondary"):
                st.session_state.sample_data = SAMPLE_EVENTS[1]
                st.rerun()
        with sample_cols[2]:
            if st.button("🎲 Sample 3", use_container_width=True, type="secondary"):
                st.session_state.sample_data = SAMPLE_EVENTS[2]
                st.rerun()

        st.markdown("---")

        # Get default values from sample data
        sample = st.session_state.sample_data or {}

        # Event Title
        event_title = st.text_input(
            "Event Title",
            value=sample.get("title", ""),
            placeholder="e.g., Annual Security Conference 2026"
        )

        # Event Description
        event_description = st.text_area(
            "Event Description",
            value=sample.get("description", ""),
            placeholder="Describe what the event is about...",
            height=100
        )

        # Event Date
        event_date = st.date_input(
            "Event Date",
            value=sample.get("date", date.today())
        )

        # Target Audience
        target_audience = st.text_input(
            "Target Audience",
            value=sample.get("audience", ""),
            placeholder="e.g., IT professionals, Marketing managers"
        )

        # Key Messages
        key_messages = st.text_area(
            "Key Messages (one per line)",
            value=sample.get("messages", ""),
            placeholder="Enter key points to communicate...",
            height=100
        )

        # Channels
        channels = st.multiselect(
            "Marketing Channels",
            options=["linkedin", "facebook", "email", "web"],
            default=sample.get("channels", ["linkedin", "email"]),
            format_func=lambda x: {"linkedin": "💼 LinkedIn", "facebook": "📘 Facebook", "email": "✉️ Email", "web": "🌐 Web"}[x]
        )

        # URLs
        urls_text = st.text_area(
            "URLs for CTAs (format: Label | URL)",
            value=sample.get("urls", ""),
            placeholder="Register Now | https://example.com/register",
            height=80
        )

        st.markdown("---")

        # Generate button
        generate_disabled = not (event_title and event_description and channels)

        if st.button("✨ Generate Content", disabled=generate_disabled, use_container_width=True):
            # Build event brief
            event_brief = {
                "event_title": event_title,
                "event_description": event_description,
                "event_date": event_date.isoformat() if event_date else None,
                "target_audience": target_audience,
                "key_messages": [m.strip() for m in key_messages.split("\n") if m.strip()],
                "channels": channels,
                "relevant_urls": parse_urls(urls_text)
            }

            with st.spinner("🤖 Agent is generating content..."):
                try:
                    # Run the async function
                    result = asyncio.run(generate_content(event_brief))
                    st.session_state.result = result
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    # ========================================================================
    # Output Column
    # ========================================================================
    with col_output:
        result = st.session_state.result

        if result is None:
            # Empty state
            st.markdown("""
            <div style="
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 400px;
                background: var(--bg-secondary);
                border: 1px dashed var(--border);
                border-radius: 12px;
                text-align: center;
            ">
                <div style="font-size: 4rem; margin-bottom: 1rem; opacity: 0.3;">🛡️</div>
                <p style="color: var(--text-muted); font-size: 1rem;">
                    Fill in the event details and click<br/>
                    <strong style="color: var(--text-secondary);">Generate Content</strong> to get started
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Show results
            output = result.get("result", {})
            success = result.get("success", False)
            iterations = result.get("iterations", 0)
            flags = result.get("flags", [])

            # Status header
            status_class = "status-success" if success else "status-warning"
            status_text = "Generation Complete" if success else "Completed with Warnings"

            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                <h2 style="margin: 0;">Generated Content</h2>
                <span class="status-indicator {status_class}">
                    {'✓' if success else '⚠'} {status_text}
                </span>
            </div>
            """, unsafe_allow_html=True)

            if output:
                # Scorecard
                scorecard = output.get("scorecard", {})
                if scorecard:
                    st.markdown("### Quality Scorecard")
                    score_cols = st.columns(len(scorecard))

                    for i, (channel, scores) in enumerate(scorecard.items()):
                        with score_cols[i]:
                            icon = get_channel_icon(channel)
                            brand_score = scores.get("brand_voice_score", scores.get("brand_voice", 0))
                            cta_score = scores.get("cta_clarity_score", scores.get("cta_clarity", 0))
                            passed = scores.get("passed", brand_score >= 7 and cta_score >= 7)

                            st.markdown(f"""
                            <div class="content-card" style="text-align: center;">
                                <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{icon}</div>
                                <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.75rem; text-transform: capitalize;">{channel}</div>
                                <div style="display: flex; justify-content: center; gap: 0.5rem;">
                                    <span class="score-badge {get_score_class(brand_score)}">Voice: {brand_score}</span>
                                    <span class="score-badge {get_score_class(cta_score)}">CTA: {cta_score}</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                st.markdown("---")

                # Content tabs
                content = output.get("content", {})
                if content:
                    st.markdown("### Content by Channel")

                    tabs = st.tabs([f"{get_channel_icon(ch)} {ch.capitalize()}" for ch in content.keys()])

                    for tab, (channel, channel_content) in zip(tabs, content.items()):
                        with tab:
                            if isinstance(channel_content, dict):
                                # Headline/Subject
                                headline = channel_content.get("headline") or channel_content.get("subject_line") or channel_content.get("subject")
                                if headline:
                                    st.markdown(f"**{'Subject' if channel == 'email' else 'Headline'}**")
                                    st.code(strip_citations(headline), language=None)

                                # Body
                                body = channel_content.get("body", "")
                                if body:
                                    st.markdown("**Body**")
                                    st.code(strip_citations(body), language=None)

                                # CTA
                                cta = channel_content.get("cta", "")
                                if cta:
                                    st.markdown("**Call to Action**")
                                    st.code(strip_citations(cta), language=None)

                                # Hashtags
                                hashtags = channel_content.get("hashtags", [])
                                if hashtags:
                                    st.markdown("**Hashtags**")
                                    st.code(" ".join(hashtags), language=None)

                                # Copy button
                                full_content = f"{headline or ''}\n\n{body}\n\n{cta}"
                                if hashtags:
                                    full_content += f"\n\n{' '.join(hashtags)}"

                                st.text_area(
                                    "Copy-ready content",
                                    value=strip_citations(full_content),
                                    height=150,
                                    key=f"copy_{channel}",
                                    label_visibility="collapsed"
                                )

                # Images
                images = output.get("images", {})
                if images:
                    st.markdown("---")
                    st.markdown("### Generated Images")

                    img_cols = st.columns(len(images))
                    for i, (channel, img_path) in enumerate(images.items()):
                        with img_cols[i]:
                            if img_path and Path(img_path).exists():
                                st.image(img_path, caption=f"{channel.capitalize()}", use_container_width=True)
                            else:
                                st.markdown(f"""
                                <div style="
                                    background: var(--bg-tertiary);
                                    border: 1px dashed var(--border);
                                    border-radius: 8px;
                                    padding: 2rem;
                                    text-align: center;
                                    color: var(--text-muted);
                                ">
                                    {get_channel_icon(channel)}<br/>
                                    No image generated
                                </div>
                                """, unsafe_allow_html=True)

                # Claims table
                claims_table = output.get("claims_table", [])
                if claims_table:
                    st.markdown("---")
                    with st.expander("📋 Claims Verification Table"):
                        for claim in claims_table:
                            if isinstance(claim, dict):
                                supported = claim.get("supported", False)
                                status_icon = "✓" if supported else "✗"
                                status_class = "claim-verified" if supported else "claim-unverified"

                                st.markdown(f"""
                                <div style="
                                    padding: 0.75rem 1rem;
                                    background: var(--bg-tertiary);
                                    border-radius: 6px;
                                    margin-bottom: 0.5rem;
                                    display: flex;
                                    gap: 1rem;
                                    align-items: flex-start;
                                ">
                                    <span class="{status_class}" style="font-size: 1.25rem;">{status_icon}</span>
                                    <div style="flex: 1;">
                                        <div style="color: var(--text-primary); margin-bottom: 0.25rem;">{claim.get('claim', 'Unknown claim')}</div>
                                        <div style="font-size: 0.75rem; color: var(--text-muted);">
                                            Source: {claim.get('source_id', 'None')} | Similarity: {claim.get('similarity', 0):.2f}
                                        </div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

            # Agent observability section
            st.markdown("---")
            with st.expander("🔍 Agent Observability"):
                # Iterations and flags
                obs_cols = st.columns([1, 2])

                with obs_cols[0]:
                    st.metric("Iterations", iterations)

                with obs_cols[1]:
                    if flags:
                        st.markdown("**Flags**")
                        for flag in flags:
                            st.markdown(f"- `{flag}`")
                    else:
                        st.markdown("**Flags**: None")

                # Tool sequence
                audit_log = result.get("audit_log", {})
                all_tool_calls = audit_log.get("all_tool_calls", [])

                if all_tool_calls:
                    st.markdown("**Tool Sequence**")

                    tools = [call.get("tool", "unknown") for call in all_tool_calls if call.get("tool")]

                    tool_html = '<div class="tool-sequence">'
                    for i, tool in enumerate(tools):
                        if i > 0:
                            tool_html += '<span class="tool-arrow">→</span>'
                        tool_html += f'<span class="tool-badge">{tool}</span>'
                    tool_html += '</div>'

                    st.markdown(tool_html, unsafe_allow_html=True)

                # Full audit log
                st.markdown("**Full Audit Log**")
                st.json(audit_log)

    # ========================================================================
    # Sidebar - Corpus Management
    # ========================================================================
    with st.sidebar:
        st.markdown("## ⚙️ Settings")

        st.markdown("### Corpus Management")

        if st.button("🔄 Re-index Corpus", use_container_width=True):
            with st.spinner("Indexing..."):
                try:
                    result = ingest_documents(force_reingest=True)
                    st.success(f"Indexed: {result}")
                except Exception as e:
                    st.error(f"Error: {e}")

        # List corpus files
        corpus_dir = Path("corpus")
        if corpus_dir.exists():
            st.markdown("**Corpus Files**")
            for file in corpus_dir.glob("*.md"):
                with st.expander(file.name):
                    try:
                        content = file.read_text()[:500]
                        st.code(content + "..." if len(file.read_text()) > 500 else content)
                    except:
                        st.write("Could not read file")

        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: var(--text-muted); font-size: 0.75rem;">
            BrandGuard v0.1.0<br/>
            Claude Agent SDK
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
