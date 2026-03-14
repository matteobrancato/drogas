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

# Shared Plotly layout defaults — clean, airy, no clutter
_LAYOUT_DEFAULTS = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, system-ui, sans-serif", color="#2D3748"),
    hoverlabel=dict(bgcolor="white", font_size=12, bordercolor="#e2e6ea"),
)


def _base_layout(**kwargs) -> dict:
    out = dict(_LAYOUT_DEFAULTS)
    out.update(kwargs)
    return out


# ------------------------------------------------------------------
# Gauge
# ------------------------------------------------------------------

def render_gauge_chart(pct: float, title: str = "Automation Coverage") -> None:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=pct,
            number={"suffix": "%", "font": {"size": 40, "color": "#2D3748"}},
            title={"text": title, "font": {"size": 14, "color": "#718096"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#CBD5E0"},
                "bar": {"color": "#34B78F", "thickness": 0.75},
                "bgcolor": "#EDF2F7",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 33], "color": "#FFF5F5"},
                    {"range": [33, 66], "color": "#FFFAF0"},
                    {"range": [66, 100], "color": "#F0FFF4"},
                ],
            },
        )
    )
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=50, b=10),
                      **_LAYOUT_DEFAULTS)
    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------------
# Segmented progress bar
# ------------------------------------------------------------------

def render_progress_bar(kpis: dict) -> None:
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
                x=[pct], y=["Progress"],
                orientation="h",
                name=f"{name} ({count})",
                marker_color=CATEGORY_COLORS.get(name, "#999"),
                text=f"{pct:.1f}%" if pct > 4 else "",
                textposition="inside",
                textfont=dict(color="white", size=11),
                hovertemplate=f"{name}: {count} ({pct:.1f}%)<extra></extra>",
            )
        )

    fig.update_layout(
        **_base_layout(
            barmode="stack",
            height=85,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(visible=False, range=[0, 100]),
            yaxis=dict(visible=False),
            legend=dict(
                orientation="h", yanchor="top", y=-0.6,
                xanchor="center", x=0.5, font=dict(size=11),
            ),
            showlegend=True,
        )
    )
    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------------
# Status distribution — donut
# ------------------------------------------------------------------

def render_status_pie(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No data.")
        return

    counts = df["status"].value_counts().reset_index()
    counts.columns = ["Status", "Count"]

    fig = px.pie(
        counts, values="Count", names="Status",
        color="Status", color_discrete_map=STATUS_COLORS,
        hole=0.5,
    )
    fig.update_traces(
        textposition="inside", textinfo="percent+label",
        textfont_size=11,
        marker=dict(line=dict(color="#FAFBFC", width=2)),
    )
    fig.update_layout(
        **_base_layout(
            height=380,
            margin=dict(l=10, r=10, t=20, b=10),
            legend=dict(
                orientation="h", yanchor="top", y=-0.05,
                xanchor="center", x=0.5, font=dict(size=11),
            ),
        )
    )
    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------------
# Automation category — vertical bar
# ------------------------------------------------------------------

def render_category_bar(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No data.")
        return

    counts = df["automation_category"].value_counts().reset_index()
    counts.columns = ["Category", "Count"]
    order = [c for c in CATEGORY_ORDER if c in counts["Category"].values]
    counts["Category"] = pd.Categorical(counts["Category"], categories=order, ordered=True)
    counts = counts.sort_values("Category")

    fig = px.bar(
        counts, x="Category", y="Count",
        color="Category", color_discrete_map=CATEGORY_COLORS,
        text="Count",
    )
    fig.update_traces(
        textposition="outside", textfont_size=12,
        marker_line_width=0,
    )
    fig.update_layout(
        **_base_layout(
            height=380,
            margin=dict(l=10, r=10, t=20, b=10),
            xaxis_title="", yaxis_title="Test Cases",
            yaxis=dict(gridcolor="#EDF2F7"),
            showlegend=False,
        )
    )
    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------------
# Country comparison — grouped bar
# ------------------------------------------------------------------

_COUNTRY_PALETTE = ["#5BA4CF", "#E8944A"]


def render_country_comparison(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No data.")
        return

    grouped = (
        df.groupby(["country", "automation_category"])
        .size().reset_index(name="Count")
    )
    order = [c for c in CATEGORY_ORDER if c in grouped["automation_category"].values]
    grouped["automation_category"] = pd.Categorical(
        grouped["automation_category"], categories=order, ordered=True
    )
    grouped = grouped.sort_values("automation_category")

    fig = px.bar(
        grouped, x="automation_category", y="Count",
        color="country", barmode="group", text="Count",
        color_discrete_sequence=_COUNTRY_PALETTE,
    )
    fig.update_traces(textposition="outside", textfont_size=11, marker_line_width=0)
    fig.update_layout(
        **_base_layout(
            height=380,
            margin=dict(l=10, r=10, t=20, b=10),
            xaxis_title="", yaxis_title="Test Cases",
            yaxis=dict(gridcolor="#EDF2F7"),
            legend_title="Country",
        )
    )
    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------------
# Coverage by group
# ------------------------------------------------------------------

def render_coverage_by_group(stats_df: pd.DataFrame, group_col: str) -> None:
    if stats_df.empty:
        st.info("No data.")
        return

    fig = px.bar(
        stats_df, x=group_col, y="automation_pct",
        color=group_col,
        text=stats_df["automation_pct"].apply(lambda v: f"{v:.1f}%"),
        color_discrete_sequence=["#5BA4CF", "#E8944A", "#34B78F", "#D96459"],
    )
    fig.update_traces(textposition="outside", textfont_size=12, marker_line_width=0)
    fig.update_layout(
        **_base_layout(
            height=340,
            margin=dict(l=10, r=10, t=20, b=10),
            xaxis_title="", yaxis_title="Coverage (%)",
            yaxis=dict(
                range=[0, max(stats_df["automation_pct"].max() * 1.3, 10)],
                gridcolor="#EDF2F7",
            ),
            showlegend=False,
        )
    )
    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------------
# Device comparison — grouped bar
# ------------------------------------------------------------------

_DEVICE_PALETTE = ["#34B78F", "#8E7CC3"]


def render_device_comparison(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No data.")
        return

    grouped = (
        df.groupby(["device", "automation_category"])
        .size().reset_index(name="Count")
    )
    order = [c for c in CATEGORY_ORDER if c in grouped["automation_category"].values]
    grouped["automation_category"] = pd.Categorical(
        grouped["automation_category"], categories=order, ordered=True
    )
    grouped = grouped.sort_values("automation_category")

    fig = px.bar(
        grouped, x="automation_category", y="Count",
        color="device", barmode="group", text="Count",
        color_discrete_sequence=_DEVICE_PALETTE,
    )
    fig.update_traces(textposition="outside", textfont_size=11, marker_line_width=0)
    fig.update_layout(
        **_base_layout(
            height=380,
            margin=dict(l=10, r=10, t=20, b=10),
            xaxis_title="", yaxis_title="Test Cases",
            yaxis=dict(gridcolor="#EDF2F7"),
            legend_title="Device",
        )
    )
    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------------
# Heatmap — country x device coverage
# ------------------------------------------------------------------

def render_coverage_heatmap(df: pd.DataFrame) -> None:
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
            colorscale=[
                [0, "#FFF5F5"], [0.25, "#FED7D7"],
                [0.5, "#FEFCBF"], [0.75, "#C6F6D5"],
                [1, "#34B78F"],
            ],
            text=[[f"{v:.1f}%" for v in row] for row in matrix.values],
            texttemplate="%{text}",
            textfont={"size": 16, "color": "#2D3748"},
            hovertemplate="Country: %{y}<br>Device: %{x}<br>Coverage: %{text}<extra></extra>",
            zmin=0, zmax=100,
            showscale=False,
        )
    )
    fig.update_layout(
        **_base_layout(
            height=240,
            margin=dict(l=10, r=10, t=20, b=10),
            xaxis_title="", yaxis_title="",
        )
    )
    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------------
# Run Overview — stacked horizontal bars (one per run)
# ------------------------------------------------------------------

def render_run_status_bars(df: pd.DataFrame) -> None:
    """Stacked horizontal bar chart showing category breakdown per run config."""
    if df.empty or "config" not in df.columns:
        return

    configs = sorted(df["config"].dropna().unique().tolist())
    if not configs:
        return

    cat_order = [c for c in CATEGORY_ORDER if c in df["automation_category"].unique()]

    fig = go.Figure()
    for cat in cat_order:
        counts = []
        for cfg in configs:
            n = ((df["config"] == cfg) & (df["automation_category"] == cat)).sum()
            counts.append(n)
        fig.add_trace(
            go.Bar(
                y=configs, x=counts,
                orientation="h",
                name=cat,
                marker_color=CATEGORY_COLORS.get(cat, "#999"),
                marker_line_width=0,
                text=[str(c) if c > 0 else "" for c in counts],
                textposition="inside",
                textfont=dict(color="white", size=11),
                hovertemplate=f"{cat}: %{{x}}<extra></extra>",
            )
        )

    fig.update_layout(
        **_base_layout(
            barmode="stack",
            height=200,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(title="Test Cases", gridcolor="#EDF2F7"),
            yaxis=dict(title="", autorange="reversed"),
            legend=dict(
                orientation="h", yanchor="top", y=-0.25,
                xanchor="center", x=0.5, font=dict(size=11),
            ),
        )
    )
    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _quick_pct(group: pd.DataFrame) -> float:
    total = len(group)
    na = (group["automation_category"] == "Not Applicable").sum()
    automated = (group["automation_category"] == "Automated").sum()
    actionable = total - na
    return round(automated / actionable * 100, 1) if actionable else 0.0
