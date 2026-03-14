"""
Plotly chart components for the Drogas AQA Dashboard.

Every public function renders one self-contained chart section inside a
Streamlit container.  All charts use the project colour palette defined
in :mod:`config`.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import CATEGORY_COLORS, CATEGORY_ORDER, STATUS_COLORS


# ------------------------------------------------------------------
# Gauge
# ------------------------------------------------------------------

def render_gauge_chart(pct: float, title: str = "Automation Coverage") -> None:
    """Semi-circular gauge showing overall automation coverage %."""
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=pct,
            number={"suffix": "%", "font": {"size": 42}},
            title={"text": title, "font": {"size": 15}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": "#28A745"},
                "bgcolor": "white",
                "steps": [
                    {"range": [0, 33], "color": "#FFEBEE"},
                    {"range": [33, 66], "color": "#FFF3E0"},
                    {"range": [66, 100], "color": "#E8F5E9"},
                ],
                "threshold": {
                    "line": {"color": "#28A745", "width": 4},
                    "thickness": 0.75,
                    "value": pct,
                },
            },
        )
    )
    fig.update_layout(height=270, margin=dict(l=20, r=20, t=50, b=10))
    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------------
# Segmented progress bar
# ------------------------------------------------------------------

def render_progress_bar(kpis: dict) -> None:
    """Horizontal stacked bar showing category breakdown of actionable tests."""
    total = kpis["actionable_total"]
    if total == 0:
        st.info("No actionable test cases found.")
        return

    segments = [
        ("Automated", kpis["automated"]),
        ("In Progress", kpis["in_progress"]),
        ("Failed", kpis["failed"]),
        ("Blocked", kpis["blocked"]),
        ("Backlog", kpis["backlog"]),
    ]

    fig = go.Figure()
    for name, count in segments:
        pct = count / total * 100
        fig.add_trace(
            go.Bar(
                x=[pct],
                y=["Progress"],
                orientation="h",
                name=f"{name} ({count})",
                marker_color=CATEGORY_COLORS.get(name, "#999"),
                text=f"{pct:.1f}%" if pct > 4 else "",
                textposition="inside",
                hovertemplate=f"{name}: {count} ({pct:.1f}%)<extra></extra>",
            )
        )

    fig.update_layout(
        barmode="stack",
        height=90,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False, range=[0, 100]),
        yaxis=dict(visible=False),
        legend=dict(
            orientation="h", yanchor="top", y=-0.5,
            xanchor="center", x=0.5, font=dict(size=11),
        ),
        showlegend=True,
    )
    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------------
# Status distribution – pie
# ------------------------------------------------------------------

def render_status_pie(df: pd.DataFrame) -> None:
    """Donut chart of execution-status distribution."""
    if df.empty:
        st.info("No data.")
        return

    counts = df["status"].value_counts().reset_index()
    counts.columns = ["Status", "Count"]

    fig = px.pie(
        counts,
        values="Count",
        names="Status",
        color="Status",
        color_discrete_map=STATUS_COLORS,
        hole=0.45,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(
        height=400,
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(
            orientation="h", yanchor="top", y=-0.05,
            xanchor="center", x=0.5, font=dict(size=11),
        ),
    )
    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------------
# Automation category – vertical bar
# ------------------------------------------------------------------

def render_category_bar(df: pd.DataFrame) -> None:
    """Bar chart of automation-category counts."""
    if df.empty:
        st.info("No data.")
        return

    counts = df["automation_category"].value_counts().reset_index()
    counts.columns = ["Category", "Count"]
    # enforce display order
    order = [c for c in CATEGORY_ORDER if c in counts["Category"].values]
    counts["Category"] = pd.Categorical(counts["Category"], categories=order, ordered=True)
    counts = counts.sort_values("Category")

    fig = px.bar(
        counts, x="Category", y="Count",
        color="Category", color_discrete_map=CATEGORY_COLORS,
        text="Count",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=400,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_title="", yaxis_title="Test Cases",
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------------
# Country comparison – grouped bar
# ------------------------------------------------------------------

def render_country_comparison(df: pd.DataFrame) -> None:
    """Grouped bar chart: automation categories split by country."""
    if df.empty:
        st.info("No data.")
        return

    grouped = (
        df.groupby(["country", "automation_category"])
        .size()
        .reset_index(name="Count")
    )
    order = [c for c in CATEGORY_ORDER if c in grouped["automation_category"].values]
    grouped["automation_category"] = pd.Categorical(
        grouped["automation_category"], categories=order, ordered=True
    )
    grouped = grouped.sort_values("automation_category")

    fig = px.bar(
        grouped,
        x="automation_category", y="Count",
        color="country", barmode="group",
        text="Count",
        color_discrete_sequence=["#1f77b4", "#ff7f0e"],
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=400,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_title="", yaxis_title="Test Cases",
        legend_title="Country",
    )
    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------------
# Coverage by group – horizontal bar
# ------------------------------------------------------------------

def render_coverage_by_group(
    stats_df: pd.DataFrame, group_col: str, title: str = ""
) -> None:
    """Bar chart showing automation coverage % per group value."""
    if stats_df.empty:
        st.info("No data.")
        return

    fig = px.bar(
        stats_df,
        x=group_col, y="automation_pct",
        color=group_col,
        text=stats_df["automation_pct"].apply(lambda v: f"{v:.1f}%"),
        color_discrete_sequence=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"],
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=350,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_title="", yaxis_title="Coverage (%)",
        yaxis_range=[0, max(stats_df["automation_pct"].max() * 1.3, 10)],
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------------
# Device comparison – grouped bar
# ------------------------------------------------------------------

def render_device_comparison(df: pd.DataFrame) -> None:
    """Grouped bar chart: automation categories split by device type."""
    if df.empty:
        st.info("No data.")
        return

    grouped = (
        df.groupby(["device", "automation_category"])
        .size()
        .reset_index(name="Count")
    )
    order = [c for c in CATEGORY_ORDER if c in grouped["automation_category"].values]
    grouped["automation_category"] = pd.Categorical(
        grouped["automation_category"], categories=order, ordered=True
    )
    grouped = grouped.sort_values("automation_category")

    fig = px.bar(
        grouped,
        x="automation_category", y="Count",
        color="device", barmode="group",
        text="Count",
        color_discrete_sequence=["#2ca02c", "#9467bd"],
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=400,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_title="", yaxis_title="Test Cases",
        legend_title="Device",
    )
    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------------
# Heatmap – country × device coverage
# ------------------------------------------------------------------

def render_coverage_heatmap(df: pd.DataFrame) -> None:
    """Heatmap of automation coverage % for each country-device combination."""
    if df.empty:
        st.info("No data.")
        return

    pivot = (
        df.groupby(["country", "device"])
        .apply(lambda g: _quick_pct(g), include_groups=False)
        .reset_index()
    )
    pivot.columns = ["country", "device", "coverage"]
    matrix = pivot.pivot(index="country", columns="device", values="coverage").fillna(0)

    fig = go.Figure(
        go.Heatmap(
            z=matrix.values,
            x=matrix.columns.tolist(),
            y=matrix.index.tolist(),
            colorscale=[[0, "#FFEBEE"], [0.5, "#FFF3E0"], [1, "#28A745"]],
            text=[[f"{v:.1f}%" for v in row] for row in matrix.values],
            texttemplate="%{text}",
            textfont={"size": 16},
            hovertemplate="Country: %{y}<br>Device: %{x}<br>Coverage: %{text}<extra></extra>",
            zmin=0, zmax=100,
        )
    )
    fig.update_layout(
        height=250,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_title="", yaxis_title="",
    )
    st.plotly_chart(fig, use_container_width=True)


def _quick_pct(group: pd.DataFrame) -> float:
    total = len(group)
    na = (group["automation_category"] == "Not Applicable").sum()
    automated = (group["automation_category"] == "Automated").sum()
    actionable = total - na
    return round(automated / actionable * 100, 1) if actionable else 0.0
