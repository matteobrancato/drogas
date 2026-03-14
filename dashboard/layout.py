"""
Main dashboard layout — assembles all components.

The test plan contains **4 runs** with configs combining device and country:
``desktop LV``, ``desktop LT``, ``mobile LV``, ``mobile LT``.
The dashboard provides filters and breakdowns for both dimensions.
"""

from __future__ import annotations

import streamlit as st

from config import (
    CATEGORY_COLORS,
    PAGE_ICON,
    PAGE_LAYOUT,
    PAGE_TITLE,
    TESTRAIL_API_KEY,
    TESTRAIL_PLAN_ID,
    TESTRAIL_PLAN_URL_TPL,
    TESTRAIL_URL,
    TESTRAIL_USER,
)
from dashboard.charts import (
    render_category_bar,
    render_country_comparison,
    render_coverage_by_group,
    render_coverage_heatmap,
    render_device_comparison,
    render_gauge_chart,
    render_progress_bar,
    render_status_pie,
)
from dashboard.filters import render_filters
from dashboard.tables import (
    render_backlog_table,
    render_blocked_table,
    render_drilldown_table,
)
from data.data_loader import load_test_plan_data
from data.data_processing import compute_group_stats, compute_kpis, enrich_dataframe


# ------------------------------------------------------------------
# Page setup
# ------------------------------------------------------------------

def _configure_page() -> None:
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=PAGE_ICON,
        layout=PAGE_LAYOUT,
        initial_sidebar_state="expanded",
    )


def _inject_css() -> None:
    st.markdown(
        """
        <style>
        /* KPI cards */
        div[data-testid="stMetric"] {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 12px 16px;
        }
        div[data-testid="stMetric"] label {
            font-size: .85rem !important;
            color: #6c757d;
        }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            font-size: 1.8rem !important;
            font-weight: 700;
        }
        .section-hdr {
            font-size: 1.15rem;
            font-weight: 600;
            color: #343a40;
            margin-bottom: .5rem;
            padding-bottom: .3rem;
            border-bottom: 2px solid #28A745;
        }
        section[data-testid="stSidebar"] { background: #f8f9fa; }
        footer { visibility: hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------

def _render_sidebar_header() -> None:
    st.sidebar.title(f"{PAGE_ICON} {PAGE_TITLE}")
    plan_url = TESTRAIL_PLAN_URL_TPL.format(plan_id=TESTRAIL_PLAN_ID)
    st.sidebar.markdown(f"**Test Plan:** [{TESTRAIL_PLAN_ID}]({plan_url})")
    st.sidebar.markdown("**Project:** Drogas Website")
    st.sidebar.markdown("**Configs:** Desktop LV / LT, Mobile LV / LT")


def _render_refresh_button() -> None:
    st.sidebar.markdown("---")
    if st.sidebar.button("Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# ------------------------------------------------------------------
# Section helpers
# ------------------------------------------------------------------

def _section(title: str) -> None:
    st.markdown(f'<p class="section-hdr">{title}</p>', unsafe_allow_html=True)


# ------------------------------------------------------------------
# KPI row
# ------------------------------------------------------------------

def _render_kpis(kpis: dict) -> None:
    _section("Key Metrics")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Test Cases", f"{kpis['total']:,}")
    c2.metric("Automated", f"{kpis['automated']:,}")
    c3.metric("Coverage", f"{kpis['automation_pct']}%")
    c4.metric("Backlog", f"{kpis['backlog']:,}")
    c5.metric("Blocked", f"{kpis['blocked']:,}")
    c6.metric("In Progress", f"{kpis['in_progress']:,}")


# ------------------------------------------------------------------
# Progress section
# ------------------------------------------------------------------

def _render_progress(kpis: dict) -> None:
    _section("Automation Progress")
    left, right = st.columns([2, 1])
    with left:
        render_progress_bar(kpis)
    with right:
        render_gauge_chart(kpis["automation_pct"])


# ------------------------------------------------------------------
# Distribution section
# ------------------------------------------------------------------

def _render_distribution(df) -> None:
    _section("Status Distribution")
    left, right = st.columns(2)
    with left:
        st.markdown("**Execution Status**")
        render_status_pie(df)
    with right:
        st.markdown("**Automation Categories**")
        render_category_bar(df)


# ------------------------------------------------------------------
# Country & device comparison
# ------------------------------------------------------------------

def _render_comparisons(df, country_stats, device_stats) -> None:
    _section("Country & Device Comparison")

    # Coverage charts
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Coverage by Country**")
        render_coverage_by_group(country_stats, "country")
    with c2:
        st.markdown("**Coverage by Device**")
        render_coverage_by_group(device_stats, "device")
    with c3:
        st.markdown("**Coverage Heatmap**")
        render_coverage_heatmap(df)

    # Category breakdown
    left, right = st.columns(2)
    with left:
        st.markdown("**Categories by Country**")
        render_country_comparison(df)
    with right:
        st.markdown("**Categories by Device**")
        render_device_comparison(df)

    # Per-country KPI cards
    if not country_stats.empty:
        cols = st.columns(len(country_stats))
        for i, (_, row) in enumerate(country_stats.iterrows()):
            with cols[i]:
                st.markdown(f"**{row['country']}**")
                sc = st.columns(3)
                sc[0].metric("Total", int(row["total"]))
                sc[1].metric("Automated", int(row["automated"]))
                sc[2].metric("Backlog", int(row["backlog"]))


# ------------------------------------------------------------------
# Drill-down section
# ------------------------------------------------------------------

def _render_drilldown(df) -> None:
    _section("Test Case Details")
    tabs = st.tabs(["All Test Cases", "Backlog Summary", "Blocked Cases"])
    with tabs[0]:
        render_drilldown_table(df)
    with tabs[1]:
        render_backlog_table(df)
    with tabs[2]:
        render_blocked_table(df)


# ------------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------------

def render_dashboard() -> None:
    """Assemble and render the full dashboard."""
    _configure_page()
    _inject_css()
    _render_sidebar_header()
    _render_refresh_button()

    # --- Load data ---
    try:
        raw_df = load_test_plan_data()
    except Exception as exc:
        st.error(f"Failed to load data from TestRail: {exc}")
        st.info(
            "Verify your credentials in the Streamlit Secrets (or `.env` file) "
            "and that the plan ID is correct."
        )
        st.code(
            f"TESTRAIL_URL  = {TESTRAIL_URL}\n"
            f"TESTRAIL_USER = {'(set)' if TESTRAIL_USER else '(empty!)'}\n"
            f"TESTRAIL_KEY  = {'(set)' if TESTRAIL_API_KEY else '(empty!)'}\n"
            f"PLAN_ID       = {TESTRAIL_PLAN_ID}",
            language="text",
        )
        return

    if raw_df.empty:
        st.warning("No test data found in the specified test plan.")
        st.info(
            "The API connection succeeded but returned no usable data. "
            "Check the diagnostic messages above (if any) for run/config details."
        )
        return

    enriched_df = enrich_dataframe(raw_df)

    # --- Filters ---
    filtered_df = render_filters(enriched_df)

    # --- Compute metrics ---
    kpis = compute_kpis(filtered_df)
    country_stats = compute_group_stats(filtered_df, "country")
    device_stats = compute_group_stats(filtered_df, "device")

    # --- Render sections ---
    _render_kpis(kpis)
    st.markdown("")
    _render_progress(kpis)
    st.markdown("")
    _render_distribution(filtered_df)
    st.markdown("")
    _render_comparisons(filtered_df, country_stats, device_stats)
    st.markdown("")
    _render_drilldown(filtered_df)
