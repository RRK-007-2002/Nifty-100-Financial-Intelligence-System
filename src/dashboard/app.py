
from pathlib import Path

import streamlit as st


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Nifty 100 | Financial Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# 2. PROJECT PATHS
# app.py: nifty100/src/dashboard/app.py
# ============================================================
BASE_DIR = Path(__file__).resolve().parents[2]

LOGO_PATH = BASE_DIR / "blue_stock.jpg"
BANNER_PATH = BASE_DIR / "dashboard.png"
HEATMAP_PATH = BASE_DIR / "reports" / "correlation_heatmap.png"


# ============================================================
# 3. CUSTOM CSS
# ============================================================
st.markdown(
    """
    <style>
    /* Main page spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2.5rem;
        max-width: 1500px;
    }

    /* Main heading */
    .hero-title {
        font-size: clamp(2rem, 3vw, 2.8rem);
        font-weight: 800;
        letter-spacing: -1.2px;
        line-height: 1.2;
        margin-bottom: 0.6rem;
    }

    .hero-subtitle {
        font-size: 1.05rem;
        line-height: 1.8;
        color: #9CA3AF;
        max-width: 900px;
        margin-bottom: 1.2rem;
    }

    /* Section headings */
    .section-heading {
        font-size: 1.4rem;
        font-weight: 750;
        margin-top: 1.3rem;
        margin-bottom: 0.3rem;
    }

    .section-description {
        color: #9CA3AF;
        font-size: 0.95rem;
        margin-bottom: 1rem;
    }

    /* Summary metric cards */
    div[data-testid="stMetric"] {
        padding: 1.1rem;
        border: 1px solid rgba(128, 128, 128, 0.22);
        border-radius: 14px;
        background: rgba(128, 128, 128, 0.06);
        min-height: 125px;
    }

    div[data-testid="stMetricLabel"] {
        font-weight: 600;
    }

    /* Feature cards */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 14px;
    }

    /* Sidebar branding */
    .sidebar-version {
        text-align: center;
        font-size: 0.78rem;
        color: #9CA3AF;
        margin-top: 0.5rem;
        line-height: 1.6;
    }

    .sidebar-description {
        font-size: 0.88rem;
        line-height: 1.7;
        color: #9CA3AF;
    }

    /* Small labels */
    .eyebrow {
        text-transform: uppercase;
        letter-spacing: 2px;
        font-size: 0.75rem;
        font-weight: 750;
        color: #7C9CFF;
        margin-bottom: 0.5rem;
    }

    /* Footer */
    .app-footer {
        text-align: center;
        color: #9CA3AF;
        font-size: 0.82rem;
        padding: 0.8rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 4. SIDEBAR BRANDING
# ============================================================
with st.sidebar:

    if LOGO_PATH.is_file():
        # No sizing arguments: avoids image API compatibility errors.
        st.image(str(LOGO_PATH))
    else:
        st.markdown("## 📊 Nifty 100 Analytics")

    st.markdown(
        """
        <div class="sidebar-version">
            FINANCIAL INTELLIGENCE PLATFORM<br>
            Version 1.0
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.subheader("Explore the Platform")

    st.markdown(
        """
        <div class="sidebar-description">
        Navigate through the available pages to explore company
        fundamentals, screen stocks, compare peers, analyze
        financial trends, and review reports.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.caption("Available modules")

    st.markdown(
        """
        - Home
        - Profile
        - Screener
        - Peers
        - Trends
        - Sectors
        - Capital Allocation
        - Reports
        """
    )

    st.divider()

    st.caption("Built for financial data exploration and analysis.")


# ============================================================
# 5. HERO HEADER
# ============================================================
st.markdown(
    '<div class="eyebrow">FINANCIAL ANALYTICS WORKSPACE</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-title">
        Nifty 100 Financial Intelligence Platform
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-subtitle">
        A unified workspace to explore company fundamentals,
        evaluate financial performance, compare peers, and
        uncover trends across the Nifty 100 universe.
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 6. HERO / DASHBOARD BANNER
# Displayed directly below the main heading and subtitle.
# ============================================================
if BANNER_PATH.is_file():
    st.image(
        str(BANNER_PATH),
        caption="Nifty 100 Financial Analytics",
    )
else:
    st.warning(
        f"Dashboard banner not found: {BANNER_PATH}"
    )


# ============================================================
# 7. NAVIGATION OVERVIEW
# ============================================================
st.markdown(
    '<div class="section-heading">Welcome to Your Workspace</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="section-description">
        Start with an overview, then select a module from the
        sidebar to explore the available analytical tools.
    </div>
    """,
    unsafe_allow_html=True,
)

with st.container(border=True):

    st.info(
        "**How to navigate the platform**\n\n"
        "**Home** — Platform overview and key highlights.  \n"
        "**Profile** — Individual company information and fundamentals.  \n"
        "**Screener** — Filter companies using financial criteria.  \n"
        "**Peers** — Compare companies within peer groups.  \n"
        "**Trends** — Explore historical financial patterns.  \n"
        "**Sectors** — Examine sector-level financial performance.  \n"
        "**Capital Allocation** — Review investment, operating, "
        "and financing activities.  \n"
        "**Reports** — Access available analytical reports."
    )


# ============================================================
# 8. EXECUTIVE SUMMARY
# These represent platform scope, not live market statistics.
# ============================================================
st.markdown(
    '<div class="section-heading">Platform Overview</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="section-description">
        An at-a-glance overview of the platform's analytical scope.
    </div>
    """,
    unsafe_allow_html=True,
)

metric1, metric2, metric3 = st.columns(3)

with metric1:
    st.metric(
        label="Company Universe",
        value="Nifty 100",
        help="Designed for financial analysis of Nifty 100 companies.",
    )

with metric2:
    st.metric(
        label="Analytical Focus",
        value="Financial Intelligence",
        help="Company fundamentals, financial ratios, trends, and comparisons.",
    )

with metric3:
    st.metric(
        label="Platform Modules",
        value="8",
        help=(
            "Home, Profile, Screener, Peers, Trends, Sectors, "
            "Capital Allocation, and Reports."
        ),
    )


# ============================================================
# 9. PLATFORM HIGHLIGHTS
# ============================================================
st.markdown(
    '<div class="section-heading">Platform Highlights</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="section-description">
        Explore the core capabilities designed to turn financial
        data into structured analysis and useful visual insights.
    </div>
    """,
    unsafe_allow_html=True,
)

left_col, right_col = st.columns(2, gap="large")


# ------------------------------------------------------------
# LEFT COLUMN
# ------------------------------------------------------------
with left_col:

    with st.container(border=True):
        st.markdown("### 🏢 Company Financial Analysis")

        st.write(
            "Explore profit and loss statements, balance sheets, "
            "cash flows, financial ratios, and historical company "
            "performance."
        )

        st.caption("Fundamentals · Ratios · Financial Statements")

    with st.container(border=True):
        st.markdown("### 🔎 Smart Stock Screener")

        st.write(
            "Filter companies using financial metrics and evaluate "
            "businesses against selected analytical criteria."
        )

        st.caption("Screening · Filtering · Financial Criteria")

    with st.container(border=True):
        st.markdown("### ⚖️ Peer Comparison")

        st.write(
            "Compare companies across profitability, growth, "
            "financial ratios, and other available performance "
            "indicators."
        )

        st.caption("Comparative Analysis · Relative Performance")


# ------------------------------------------------------------
# RIGHT COLUMN
# ------------------------------------------------------------
with right_col:

    with st.container(border=True):
        st.markdown("### 📈 Trends & Sector Insights")

        st.write(
            "Explore historical financial patterns, sector-level "
            "differences, and relationships between financial "
            "variables."
        )

        st.caption("Historical Trends · Sector Analysis")

    with st.container(border=True):
        st.markdown("### 💰 Capital Allocation")

        st.write(
            "Analyze how companies use capital through investment, "
            "operating, and financing activities."
        )

        st.caption("Cash Flows · Investments · Financing")

    with st.container(border=True):
        st.markdown("### 📑 Reports & Visualizations")

        st.write(
            "Communicate analytical findings through charts, "
            "structured reports, and visual summaries."
        )

        st.caption("Reporting · Visualization · Insights")


# ============================================================
# 10. FINANCIAL CORRELATION ANALYSIS
# ============================================================
st.markdown(
    '<div class="section-heading">Financial Correlation Analysis</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="section-description">
        Explore relationships between financial variables through
        the correlation heatmap generated by your analytics workflow.
    </div>
    """,
    unsafe_allow_html=True,
)

if HEATMAP_PATH.is_file():

    st.image(
        str(HEATMAP_PATH),
        caption="Correlation Analysis of Financial Variables",
    )

else:

    st.info(
        "The correlation heatmap is not available yet. "
        "Generate the report to display the visualization here."
    )


# ============================================================
# 11. FOOTER
# ============================================================
st.divider()

st.markdown(
    """
    <div class="app-footer">
        Nifty 100 Financial Intelligence Platform
        &nbsp;·&nbsp; Version 1.0
        <br>
        Financial data exploration, analysis, and visualization
    </div>
    """,
    unsafe_allow_html=True,
)