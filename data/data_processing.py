"""
Data processing layer — enrichment, computed fields, and KPI calculation.

Transforms the raw DataFrame produced by :mod:`data.data_loader` into
analysis-ready structures consumed by the dashboard components.
"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

from config import (
    AUTOMATED_STATUSES,
    BACKLOG_STATUSES,
    BLOCKED_STATUSES,
    CATEGORY_ORDER,
    FAILED_STATUSES,
    IN_PROGRESS_STATUSES,
    JIRA_BASE_URL,
    NOT_APPLICABLE_STATUSES,
)


# ------------------------------------------------------------------
# Automation category classifier
# ------------------------------------------------------------------

def _classify_automation(row: pd.Series) -> str:
    """Assign a lifecycle category based on run status + automation fields."""
    status = row["status"]

    if status in AUTOMATED_STATUSES:
        return "Automated"
    if status in FAILED_STATUSES:
        return "Failed"
    if status in BLOCKED_STATUSES:
        return "Blocked"
    if status in NOT_APPLICABLE_STATUSES:
        return "Not Applicable"

    # Check custom automation-status fields for "in progress" / "automated"
    for field in ("automation_status_desktop", "automation_status_mobile"):
        val = str(row.get(field, "")).lower()
        if "automated" in val:
            return "Automated"
        if "in progress" in val:
            return "In Progress"

    if status in IN_PROGRESS_STATUSES:
        return "In Progress"

    return "Backlog"


# ------------------------------------------------------------------
# Enrichment
# ------------------------------------------------------------------

def enrich_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Add computed columns used by charts and tables."""
    if df.empty:
        return df

    out = df.copy()
    out["automation_category"] = out.apply(_classify_automation, axis=1)
    out["jira_id"] = out["jira_link"].apply(_extract_jira_id)
    out["case_id_display"] = out["case_id"].apply(lambda x: f"C{x}")
    return out


def _extract_jira_id(link: str) -> str:
    if not link:
        return ""
    match = re.search(r"[A-Z][A-Z0-9]+-\d+", link)
    return match.group(0) if match else link.rstrip("/").split("/")[-1]


# ------------------------------------------------------------------
# KPI computation
# ------------------------------------------------------------------

def compute_kpis(df: pd.DataFrame) -> dict[str, Any]:
    """Return a dict of high-level KPI values for the (possibly filtered) df."""
    total = len(df)
    if total == 0:
        return _empty_kpis()

    cats = df["automation_category"].value_counts()
    automated = int(cats.get("Automated", 0))
    in_progress = int(cats.get("In Progress", 0))
    blocked = int(cats.get("Blocked", 0))
    failed = int(cats.get("Failed", 0))
    not_applicable = int(cats.get("Not Applicable", 0))
    backlog = int(cats.get("Backlog", 0))

    actionable = total - not_applicable
    pct = (automated / actionable * 100) if actionable > 0 else 0.0

    return {
        "total": total,
        "automated": automated,
        "automation_pct": round(pct, 1),
        "in_progress": in_progress,
        "blocked": blocked,
        "failed": failed,
        "not_applicable": not_applicable,
        "backlog": backlog,
        "actionable_total": actionable,
    }


def _empty_kpis() -> dict[str, Any]:
    return {k: 0 for k in (
        "total", "automated", "automation_pct", "in_progress",
        "blocked", "failed", "not_applicable", "backlog", "actionable_total",
    )}


# ------------------------------------------------------------------
# Grouped statistics
# ------------------------------------------------------------------

def compute_group_stats(
    df: pd.DataFrame, group_col: str
) -> pd.DataFrame:
    """Compute KPIs grouped by *group_col* (e.g. ``'country'`` or ``'device'``)."""
    if df.empty:
        return pd.DataFrame()

    rows: list[dict] = []
    for value in sorted(df[group_col].unique()):
        subset = df[df[group_col] == value]
        kpis = compute_kpis(subset)
        kpis[group_col] = value
        rows.append(kpis)

    return pd.DataFrame(rows)
