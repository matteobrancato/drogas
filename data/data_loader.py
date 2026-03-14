"""
Data loader — fetches and assembles the raw dataset from TestRail.

The test plan (ID from config) contains 4 runs with configs that combine
device type and country:  desktop LV, desktop LT, mobile LV, mobile LT.
Each run holds the same set of test cases executed under that configuration.
"""

from __future__ import annotations

import re

import pandas as pd
import streamlit as st

from api.testrail_client import TestRailClient
from config import (
    CACHE_TTL_SECONDS,
    COUNTRY_TOKENS,
    CUSTOM_FIELDS,
    DEVICE_TOKENS,
    JIRA_BASE_URL,
    SUPPORTED_COUNTRIES,
    TESTRAIL_API_KEY,
    TESTRAIL_CASE_URL_TPL,
    TESTRAIL_PLAN_ID,
    TESTRAIL_URL,
    TESTRAIL_USER,
)


# ------------------------------------------------------------------
# Client factory
# ------------------------------------------------------------------

def _get_client() -> TestRailClient:
    return TestRailClient(TESTRAIL_URL, TESTRAIL_USER, TESTRAIL_API_KEY)


# ------------------------------------------------------------------
# Reference-data builders
# ------------------------------------------------------------------

def _build_status_map(client: TestRailClient) -> dict[int, str]:
    """Map status_id → human-readable label."""
    return {s["id"]: s["label"] for s in client.get_statuses()}


def _build_user_map(client: TestRailClient) -> dict[int, str]:
    """Map user_id → display name."""
    users = client.get_users()
    return {
        u["id"]: u.get("name") or u.get("email", "Unknown")
        for u in users
    }


def _build_dropdown_maps(client: TestRailClient) -> dict[str, dict[int, str]]:
    """Build id→label maps for every custom dropdown field."""
    maps: dict[str, dict[int, str]] = {}
    try:
        for field in client.get_case_fields():
            if field.get("type_id") != 6:  # 6 = Dropdown
                continue
            sys_name = field.get("system_name", "")
            items_map: dict[int, str] = {}
            for cfg in field.get("configs", []):
                items_str = cfg.get("options", {}).get("items", "")
                for line in items_str.strip().splitlines():
                    parts = line.split(",", 1)
                    if len(parts) == 2:
                        items_map[int(parts[0].strip())] = parts[1].strip()
            if items_map:
                maps[sys_name] = items_map
    except Exception:
        pass
    return maps


# ------------------------------------------------------------------
# Config parser
# ------------------------------------------------------------------

def _parse_run_config(config_str: str) -> tuple[str, str]:
    """Parse a run config string like ``'desktop LV'`` into (device, country).

    Returns (device_display, country_display).  Falls back to
    ``("Unknown", "Unknown")`` for unrecognised tokens.
    """
    if not config_str:
        return ("Unknown", "Unknown")

    lower = config_str.lower()
    device = "Unknown"
    country = "Unknown"

    for token, label in DEVICE_TOKENS.items():
        if token in lower:
            device = label
            break

    for token, label in COUNTRY_TOKENS.items():
        if token in config_str:          # case-sensitive for country codes
            country = label
            break

    return device, country


# ------------------------------------------------------------------
# Field helpers
# ------------------------------------------------------------------

def _resolve_dropdown(value, dropdown_map: dict[int, str]) -> str:
    if value is None:
        return ""
    if isinstance(value, int) and dropdown_map:
        return dropdown_map.get(value, str(value))
    return str(value) if value else ""


def _best_jira_link(row: dict) -> str:
    """Pick the first non-empty Jira reference and return a full URL."""
    for key in ("jira_task_drg", "jira_task_testim", "jira_task_testim_mobile"):
        val = str(row.get(key, "")).strip()
        if val and val.lower() not in ("", "nan", "none"):
            if val.startswith("http"):
                return val
            return f"{JIRA_BASE_URL}/{val}"
    return ""


# ------------------------------------------------------------------
# Main loader (cached)
# ------------------------------------------------------------------

@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner="Fetching data from TestRail...")
def load_test_plan_data(plan_id: int = TESTRAIL_PLAN_ID) -> pd.DataFrame:
    """Fetch and return the full test dataset for the given plan.

    Returns a DataFrame with one row per (test, run-config) combination.
    Columns include *country*, *device*, *status*, and all relevant custom
    fields ready for downstream processing.
    """
    client = _get_client()

    status_map = _build_status_map(client)
    user_map = _build_user_map(client)
    dropdown_maps = _build_dropdown_maps(client)

    plan = client.get_plan(plan_id)

    desktop_dd = dropdown_maps.get(
        CUSTOM_FIELDS["automation_status_desktop"], {}
    )
    mobile_dd = dropdown_maps.get(
        CUSTOM_FIELDS["automation_status_mobile"], {}
    )

    rows: list[dict] = []

    for entry in plan.get("entries", []):
        suite_name = entry.get("name", "")
        for run in entry.get("runs", []):
            run_id = run["id"]
            run_name = run.get("name", "")
            config_str = run.get("config", "")
            device, country = _parse_run_config(config_str)

            if country not in SUPPORTED_COUNTRIES:
                continue

            tests = client.get_tests(run_id)
            for t in tests:
                case_id = t.get("case_id", 0)
                sid = t.get("status_id")
                status_label = status_map.get(sid, "Untested") if sid else "Untested"

                aid = t.get("assignedto_id")
                assigned = user_map.get(aid, "") if aid else ""

                jira_drg = t.get(CUSTOM_FIELDS["jira_task_drg"], "") or ""
                jira_testim = t.get(CUSTOM_FIELDS["jira_task_testim"], "") or ""
                jira_testim_mob = t.get(CUSTOM_FIELDS["jira_task_testim_mobile"], "") or ""
                auto_reason = t.get(CUSTOM_FIELDS["automation_reason"], "") or ""

                auto_desktop = _resolve_dropdown(
                    t.get(CUSTOM_FIELDS["automation_status_desktop"]), desktop_dd
                )
                auto_mobile = _resolve_dropdown(
                    t.get(CUSTOM_FIELDS["automation_status_mobile"]), mobile_dd
                )

                row = {
                    "test_id": t.get("id"),
                    "case_id": case_id,
                    "title": t.get("title", ""),
                    "status_id": sid,
                    "status": status_label,
                    "country": country,
                    "device": device,
                    "run_id": run_id,
                    "run_name": run_name,
                    "suite_name": suite_name,
                    "config": config_str,
                    "assigned_to": assigned,
                    "jira_task_drg": jira_drg,
                    "jira_task_testim": jira_testim,
                    "jira_task_testim_mobile": jira_testim_mob,
                    "automation_status_desktop": auto_desktop,
                    "automation_status_mobile": auto_mobile,
                    "automation_reason": auto_reason,
                    "testrail_link": TESTRAIL_CASE_URL_TPL.format(case_id=case_id),
                }
                row["jira_link"] = _best_jira_link(row)
                rows.append(row)

    return pd.DataFrame(rows)
