"""
Sidebar filter components.

All filters update the downstream charts and tables by returning a
filtered copy of the enriched DataFrame.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd


def render_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Render sidebar filters and return the filtered DataFrame."""
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filters")

    # --- Country ---
    countries = sorted(df["country"].unique().tolist())
    sel_countries = st.sidebar.multiselect(
        "Country",
        options=countries,
        default=countries,
        key="f_country",
    )

    # --- Device ---
    devices = sorted(df["device"].unique().tolist())
    sel_devices = st.sidebar.multiselect(
        "Device",
        options=devices,
        default=devices,
        key="f_device",
    )

    # --- Execution status ---
    statuses = sorted(df["status"].unique().tolist())
    sel_statuses = st.sidebar.multiselect(
        "Execution Status",
        options=statuses,
        default=statuses,
        key="f_status",
    )

    # --- Automation category ---
    categories = sorted(df["automation_category"].unique().tolist())
    sel_categories = st.sidebar.multiselect(
        "Automation Category",
        options=categories,
        default=categories,
        key="f_category",
    )

    # --- Assigned To ---
    raw_assignees = sorted(df["assigned_to"].unique().tolist())
    assignees = [a if a else "(Unassigned)" for a in raw_assignees]
    sel_assignees = st.sidebar.multiselect(
        "Assigned To",
        options=assignees,
        default=[],
        key="f_assignee",
        placeholder="All assignees",
    )

    # --- Apply ---
    filtered = df.copy()

    if sel_countries:
        filtered = filtered[filtered["country"].isin(sel_countries)]
    if sel_devices:
        filtered = filtered[filtered["device"].isin(sel_devices)]
    if sel_statuses:
        filtered = filtered[filtered["status"].isin(sel_statuses)]
    if sel_categories:
        filtered = filtered[filtered["automation_category"].isin(sel_categories)]
    if sel_assignees:
        mapped = [("" if a == "(Unassigned)" else a) for a in sel_assignees]
        filtered = filtered[filtered["assigned_to"].isin(mapped)]

    return filtered
