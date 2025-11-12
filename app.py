"""
Investment Analyst Research Tool - Streamlit Web Interface
"""
import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
from src.llm_service import InvestmentAnalystLLM
from src.web_scraper import scrape_urls
from src.analyst_layer2 import InvestmentAnalystLayer2

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="Investment Analyst Research Tool",
    page_icon="🌏",
    layout="wide",
)

# Custom CSS - Apple-inspired Glassmorphism Design
st.markdown("""
<style>
    /* Import modern fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

    /* Global styles */
    * {
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'SF Pro Display', 'Segoe UI', system-ui, sans-serif !important;
    }

    /* Dark background gradient */
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #0f0f0f 100%);
        color: #ffffff;
    }

    /* Main container */
    .main {
        background: transparent;
    }

    /* Headers */
    .main-header {
        font-size: 2.5rem;
        font-weight: 300;
        letter-spacing: -0.5px;
        margin-bottom: 0.5rem;
        color: #ffffff;
    }

    .sub-header {
        font-size: 1rem;
        font-weight: 400;
        color: #a0a0a0;
        margin-bottom: 2rem;
        letter-spacing: 0.3px;
    }

    /* Glassmorphism form container */
    [data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px;
        padding: 2rem !important;
    }

    /* Buttons - thin borders, sharp corners */
    .stButton>button {
        width: 100%;
        background: rgba(255, 255, 255, 0.05);
        color: #ffffff;
        font-weight: 400;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        letter-spacing: 0.5px;
    }

    .stButton>button:hover {
        background: rgba(255, 255, 255, 0.1);
        border-color: rgba(255, 255, 255, 0.4);
        box-shadow: 0 8px 32px rgba(255, 255, 255, 0.1);
        transform: translateY(-2px);
    }

    .stButton>button:active {
        transform: translateY(0px);
    }

    /* Input fields - glass effect */
    .stTextInput>div>div>input,
    .stSelectbox>div>div>div,
    .stTextArea>div>div>textarea {
        background: rgba(255, 255, 255, 0.05) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease !important;
    }

    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus {
        border-color: rgba(255, 255, 255, 0.3) !important;
        box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.1) !important;
        background: rgba(255, 255, 255, 0.08) !important;
    }

    /* Placeholder text */
    .stTextInput>div>div>input::placeholder,
    .stTextArea>div>div>textarea::placeholder {
        color: rgba(255, 255, 255, 0.3) !important;
    }

    /* Labels */
    label {
        color: #a0a0a0 !important;
        font-weight: 400 !important;
        letter-spacing: 0.3px !important;
        font-size: 0.9rem !important;
    }

    /* Success box - glass with green tint */
    .success-box {
        padding: 1.5rem;
        background: rgba(40, 167, 69, 0.1);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(40, 167, 69, 0.3);
        border-radius: 8px;
        margin: 1rem 0;
        color: #ffffff;
    }

    /* Error box - glass with red tint */
    .error-box {
        padding: 1.5rem;
        background: rgba(220, 53, 69, 0.1);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(220, 53, 69, 0.3);
        border-radius: 8px;
        margin: 1rem 0;
        color: #ffffff;
    }

    /* Streamlit info/success/warning boxes */
    .stAlert {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px;
        color: #ffffff !important;
    }

    [data-testid="stNotificationContentInfo"],
    [data-testid="stNotificationContentSuccess"],
    [data-testid="stNotificationContentWarning"] {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px;
    }

    /* Metric cards */
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-weight: 300;
    }

    [data-testid="stMetricLabel"] {
        color: #a0a0a0 !important;
        font-size: 0.9rem !important;
    }

    [data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 1rem;
    }

    /* Expander - glass effect */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        color: #ffffff !important;
        transition: all 0.3s ease;
    }

    .streamlit-expanderHeader:hover {
        background: rgba(255, 255, 255, 0.08) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
    }

    [data-testid="stExpander"] {
        border: none !important;
        background: transparent !important;
    }

    /* Divider */
    hr {
        border-color: rgba(255, 255, 255, 0.1) !important;
        margin: 2rem 0;
    }

    /* Links */
    a {
        color: #8ab4f8 !important;
        text-decoration: none;
        transition: all 0.3s ease;
    }

    a:hover {
        color: #adc6ff !important;
    }

    /* Code blocks */
    code {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 4px;
        padding: 0.2rem 0.4rem;
        color: #ffffff !important;
    }

    /* JSON viewer */
    .stJson {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px;
    }

    /* Columns - add glass effect */
    [data-testid="column"] {
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(5px);
        border-radius: 8px;
        padding: 1rem;
    }

    /* Markdown text */
    .stMarkdown {
        color: #ffffff !important;
    }

    /* Smooth scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.02);
    }

    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.2);
    }

    /* Select box dropdown */
    [data-baseweb="popover"] {
        background: rgba(10, 10, 10, 0.95) !important;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px;
    }

    /* Dropdown options */
    [data-baseweb="select"] > div {
        background: rgba(255, 255, 255, 0.05) !important;
        border-color: rgba(255, 255, 255, 0.1) !important;
    }

    /* Hover states for dropdown */
    [role="option"]:hover {
        background: rgba(255, 255, 255, 0.1) !important;
    }

    /* Text color for all elements */
    p, span, div {
        color: #ffffff !important;
    }

    /* Make sure headings are styled */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 300 !important;
        letter-spacing: -0.3px;
    }
</style>
""", unsafe_allow_html=True)


def save_results_to_file(results: dict, company_name: str, layer: str = "layer1") -> Path:
    """Save results to a JSON file in the outputs directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{company_name.replace(' ', '_')}_{layer}_{timestamp}.json"
    filepath = Path("outputs") / filename

    # Ensure outputs directory exists
    filepath.parent.mkdir(exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    return filepath


async def run_layer2_analysis(layer1_results: dict) -> dict:
    """
    Run Layer 2 analysis: scrape URLs and extract insights

    Args:
        layer1_results: Results from Layer 1 (link generation)

    Returns:
        Layer 2 analysis results
    """
    company_name = layer1_results["company_name"]
    general_objective = layer1_results["general_objective"]

    # Prepare data for Layer 2
    sub_objectives_with_content = []

    for research_result in layer1_results["research_results"]:
        sub_objective = research_result["sub_objective"]
        links = research_result["links"]

        # Scrape all URLs for this sub-objective
        st.info(f"🌐 Scraping {len(links)} URLs for: {sub_objective[:60]}...")

        scraped_contents = await scrape_urls(
            urls=links,
            max_concurrent=5,
            timeout=30000
        )

        st.success(f"✅ Scraped {len(scraped_contents)}/{len(links)} URLs successfully")

        sub_objectives_with_content.append({
            "sub_objective": sub_objective,
            "scraped_contents": scraped_contents
        })

    # Analyze with AI
    st.info("🤖 Analyzing scraped content with AI...")
    analyst = InvestmentAnalystLayer2()
    layer2_results = analyst.analyze_batch(
        company_name=company_name,
        general_objective=general_objective,
        sub_objectives_with_content=sub_objectives_with_content
    )

    return layer2_results


def main():
    # Header
    st.markdown('<div class="main-header">🌏 Investment Analyst Research Tool</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Generate research sources for professional investment analysis</div>',
        unsafe_allow_html=True
    )

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        st.error("⚠️ OpenAI API key not found. Please set OPENAI_API_KEY in your .env file.")
        st.info(
            "Create a `.env` file in the project root with:\n\n"
            "```\nOPENAI_API_KEY=your-api-key-here\n```"
        )
        st.stop()

    # Main form
    with st.form("research_form"):
        st.subheader("〄 Research Parameters")

        # Company name
        company_name = st.text_input(
            "Company Name",
            placeholder="e.g., Harvey AI, EvenUp, etc.",
            help="Enter the name of the company to research"
        )

        # General objective dropdown
        general_objective = st.selectbox(
            "General Objective",
            options=[
                "Market & Competition",
                "Technology & Product",
                "Business Model & Go-to-Market",
                "Founding Team & Talent",
                "Funding & Capital Structure",
            ],
            help="Select the primary focus area for the investment analysis"
        )

        st.markdown("---")
        st.subheader("⍥ Sub-Objectives")
        st.markdown("Define 4 specific sub-objectives that break down the general objective:")

        # Four sub-objective text areas
        col1, col2 = st.columns(2)

        with col1:
            sub_obj_1 = st.text_area(
                "Sub-Objective 1",
                placeholder="e.g., TAM/SAM/SOM for each company specifically",
                height=100,
            )
            sub_obj_3 = st.text_area(
                "Sub-Objective 3",
                placeholder="e.g., Market maturity and timing",
                height=100,
            )

        with col2:
            sub_obj_2 = st.text_area(
                "Sub-Objective 2",
                placeholder="e.g., Growth drivers and inflection points",
                height=100,
            )
            sub_obj_4 = st.text_area(
                "Sub-Objective 4",
                placeholder="e.g., Direct competitor mapping with market shares",
                height=100,
            )

        # Submit button
        submitted = st.form_submit_button("🚀 Generate Research Links", use_container_width=True)

    # Process form submission
    if submitted:
        # Validation
        sub_objectives = [sub_obj_1, sub_obj_2, sub_obj_3, sub_obj_4]
        sub_objectives = [obj.strip() for obj in sub_objectives if obj.strip()]

        if not company_name.strip():
            st.error("❌ Please enter a company name.")
            st.stop()

        if len(sub_objectives) != 4:
            st.error("❌ Please fill in all 4 sub-objectives.")
            st.stop()

        # Initialize LLM service
        try:
            llm = InvestmentAnalystLLM()
        except ValueError as e:
            st.error(f"❌ {str(e)}")
            st.stop()

        # ===== LAYER 1: Generate research links =====
        st.markdown("---")
        st.subheader("🔄 Layer 1: Generating Research Links")

        with st.spinner("🔍 Generating research links... This may take 1-2 minutes."):
            layer1_results = llm.generate_batch_research(
                company_name=company_name,
                general_objective=general_objective,
                sub_objectives=sub_objectives,
            )

        # Save Layer 1 results to file
        try:
            layer1_filepath = save_results_to_file(layer1_results, company_name, layer="layer1")
            st.success(f"✅ Layer 1 results saved to: `{layer1_filepath}`")
        except Exception as e:
            st.error(f"❌ Error saving Layer 1 results: {str(e)}")

        # ===== LAYER 2: Scrape and analyze content =====
        st.markdown("---")
        st.subheader("🔄 Layer 2: Analyzing Web Content")

        try:
            # Run Layer 2 asynchronously
            layer2_results = asyncio.run(run_layer2_analysis(layer1_results))

            # Save Layer 2 results
            layer2_filepath = save_results_to_file(layer2_results, company_name, layer="layer2")
            st.success(f"✅ Layer 2 analysis complete! Results saved to: `{layer2_filepath}`")

            # Store results in session state for display
            st.session_state['layer1_results'] = layer1_results
            st.session_state['layer2_results'] = layer2_results

        except Exception as e:
            st.error(f"❌ Error during Layer 2 analysis: {str(e)}")
            st.warning("Layer 1 results are still available below.")
            st.session_state['layer1_results'] = layer1_results
            st.session_state['layer2_results'] = None

    # Display results (check session state)
    if 'layer1_results' in st.session_state:
        layer1_results = st.session_state['layer1_results']
        layer2_results = st.session_state.get('layer2_results')

        # ===== LAYER 1 SUMMARY =====
        st.markdown("---")
        st.subheader("📈 Layer 1 Summary: Research Links")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Sub-Objectives", layer1_results["total_sub_objectives"])
        with col2:
            st.metric("Successful", layer1_results["successful"], delta=None)
        with col3:
            st.metric("Failed", layer1_results["failed"], delta=None, delta_color="inverse")

        # Display failed objectives if any
        if layer1_results["failed_objectives"]:
            st.warning(f"⚠️ Failed to generate links for: {', '.join(layer1_results['failed_objectives'])}")

        # Display Layer 1 detailed results
        with st.expander("🔗 View Layer 1 Research Links", expanded=False):
            for i, research in enumerate(layer1_results["research_results"], 1):
                st.markdown(f"### Sub-Objective {i}: {research['sub_objective']}")
                st.markdown(f"**Total Links:** {len(research['links'])}")

                for j, link in enumerate(research["links"], 1):
                    st.markdown(f"{j}. [{link}]({link})")

                st.markdown("---")

        # ===== LAYER 2 RESULTS =====
        if layer2_results:
            st.markdown("---")
            st.subheader("📊 Layer 2 Analysis: Extracted Insights")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Sub-Objectives", layer2_results["total_sub_objectives"])
            with col2:
                st.metric("Successfully Analyzed", layer2_results["successful"], delta=None)
            with col3:
                st.metric("Failed", layer2_results["failed"], delta=None, delta_color="inverse")

            # Display failed analyses if any
            if layer2_results["failed_sub_objectives"]:
                st.warning(f"⚠️ Failed to analyze: {', '.join(layer2_results['failed_sub_objectives'])}")

            # Display detailed Layer 2 results
            st.markdown("---")
            st.subheader("💡 Investment Insights by Sub-Objective")

            for i, analysis in enumerate(layer2_results["analysis_results"], 1):
                with st.expander(
                    f"**Sub-Objective {i}:** {analysis['sub_objective']} "
                    f"({len(analysis['information_pieces'])} insights from "
                    f"{analysis['scraped_sources_count']} sources)",
                    expanded=True
                ):
                    st.markdown(f"**General Objective:** {analysis['general_objective']}")
                    st.markdown(f"**Sources Scraped:** {analysis['scraped_sources_count']}")
                    st.markdown(f"**Insights Extracted:** {len(analysis['information_pieces'])}")
                    st.markdown("---")

                    # Display each information piece in a nice box
                    for j, piece in enumerate(analysis["information_pieces"], 1):
                        # Color code confidence score
                        if piece["confidence_score"] >= 90:
                            confidence_color = "🟢"
                        elif piece["confidence_score"] >= 70:
                            confidence_color = "🟡"
                        elif piece["confidence_score"] >= 50:
                            confidence_color = "🟠"
                        else:
                            confidence_color = "🔴"

                        st.markdown(
                            f"**Insight {j}** {confidence_color} "
                            f"**Confidence: {piece['confidence_score']}%**"
                        )

                        # Display the content in a nice box
                        st.info(piece["content"])

                        # Display source link
                        st.markdown(f"📎 **Source:** [{piece['source_url']}]({piece['source_url']})")
                        st.markdown("---")

        # Display raw JSON outputs
        st.markdown("---")
        with st.expander("📄 View Raw JSON Outputs"):
            st.markdown("### Layer 1 Output")
            st.json(layer1_results)

            if layer2_results:
                st.markdown("### Layer 2 Output")
                st.json(layer2_results)


if __name__ == "__main__":
    main()
