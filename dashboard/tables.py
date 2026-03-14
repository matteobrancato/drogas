"""
Data-table components for the drill-down section.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st


def render_drilldown_table(df: pd.DataFrame) -> None:
    """Full test-case table with clickable TestRail and Jira links."""
    if df.empty:
        st.info("No test cases match the current filters.")
        return

    display = df[
        [
            "case_id_display",
            "title",
            "country",
            "device",
            "status",
            "automation_category",
            "assigned_to",
            "jira_link",
            "testrail_link",
        ]
    ].rename(
        columns={
            "case_id_display": "Case ID",
            "title": "Title",
            "country": "Country",
            "device": "Device",
            "status": "Status",
            "automation_category": "Automation",
            "assigned_to": "Assigned To",
            "jira_link": "Jira",
            "testrail_link": "TestRail",
        }
    )

    st.dataframe(
        display,
        use_container_width=True,
        height=600,
        column_config={
            "Case ID": st.column_config.TextColumn(width="small"),
            "Title": st.column_config.TextColumn(width="large"),
            "Country": st.column_config.TextColumn(width="small"),
            "Device": st.column_config.TextColumn(width="small"),
            "Status": st.column_config.TextColumn(width="medium"),
            "Automation": st.column_config.TextColumn(width="medium"),
            "Assigned To": st.column_config.TextColumn(width="medium"),
            "Jira": st.column_config.LinkColumn(
                display_text=r"https?://.*?/browse/(.*)",
                width="small",
            ),
            "TestRail": st.column_config.LinkColumn(
                display_text="Open",
                width="small",
            ),
        },
        hide_index=True,
    )
    st.caption(f"Showing {len(display):,} test cases")


def render_backlog_table(df: pd.DataFrame) -> None:
    """Summary of backlog items grouped by assignee."""
    if df.empty:
        st.info("No backlog items.")
        return

    backlog = df[df["automation_category"] == "Backlog"]
    if backlog.empty:
        st.success("No remaining backlog items!")
        return

    summary = (
        backlog.groupby("assigned_to")
        .agg(
            count=("test_id", "size"),
            cases=(
                "title",
                lambda x: ", ".join(x.head(3)) + ("..." if len(x) > 3 else ""),
            ),
        )
        .reset_index()
        .rename(
            columns={
                "assigned_to": "Assigned To",
                "count": "Backlog Items",
                "cases": "Sample Cases",
            }
        )
        .sort_values("Backlog Items", ascending=False)
    )
    summary["Assigned To"] = summary["Assigned To"].replace("", "(Unassigned)")
    st.dataframe(summary, use_container_width=True, hide_index=True)


def render_blocked_table(df: pd.DataFrame) -> None:
    """Table of currently blocked test cases."""
    blocked = df[df["automation_category"] == "Blocked"]
    if blocked.empty:
        st.success("No blocked test cases!")
        return

    display = blocked[
        [
            "case_id_display",
            "title",
            "country",
            "device",
            "assigned_to",
            "automation_reason",
            "testrail_link",
        ]
    ].rename(
        columns={
            "case_id_display": "Case ID",
            "title": "Title",
            "country": "Country",
            "device": "Device",
            "assigned_to": "Assigned To",
            "automation_reason": "Reason",
            "testrail_link": "TestRail",
        }
    )
    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "TestRail": st.column_config.LinkColumn(display_text="Open", width="small"),
        },
    )
