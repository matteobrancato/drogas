"""
Configuration module for the Drogas AQA Dashboard.

All settings, constants, color palettes, and field mappings are centralized here.

Credentials are resolved in this order:
  1. ``st.secrets``   (Streamlit Cloud — configured in the app dashboard)
  2. Environment vars (local dev — loaded from a ``.env`` file via python-dotenv)
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def _secret(key: str, default: str = "") -> str:
    """Read a secret from Streamlit Cloud first, then fall back to env vars."""
    try:
        import streamlit as st

        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)


# ---------------------------------------------------------------------------
# TestRail credentials
# ---------------------------------------------------------------------------
TESTRAIL_URL = _secret("TESTRAIL_URL", "https://elabaswatson.testrail.io")
TESTRAIL_USER = _secret("TESTRAIL_USER")
TESTRAIL_API_KEY = _secret("TESTRAIL_API_KEY")
TESTRAIL_PLAN_ID = int(_secret("TESTRAIL_PLAN_ID", "63084"))

# ---------------------------------------------------------------------------
# Jira
# ---------------------------------------------------------------------------
JIRA_BASE_URL = _secret(
    "JIRA_BASE_URL", "https://elab-aswatson.atlassian.net/browse"
)

# ---------------------------------------------------------------------------
# URL templates
# ---------------------------------------------------------------------------
TESTRAIL_CASE_URL_TPL = f"{TESTRAIL_URL}/index.php?/cases/view/{{case_id}}"
TESTRAIL_RUN_URL_TPL = f"{TESTRAIL_URL}/index.php?/runs/view/{{run_id}}"
TESTRAIL_PLAN_URL_TPL = f"{TESTRAIL_URL}/index.php?/plans/view/{{plan_id}}"

# ---------------------------------------------------------------------------
# Run configuration parsing
# ---------------------------------------------------------------------------
# The test plan contains 4 runs whose config names combine device + country:
#   desktop LV, desktop LT, mobile LV, mobile LT
# We parse each config string into (device, country).

COUNTRY_TOKENS = {
    "LT": "Lithuania",
    "LV": "Latvia",
    "Lithuania": "Lithuania",
    "Latvia": "Latvia",
}

DEVICE_TOKENS = {
    "desktop": "Desktop",
    "mobile": "Mobile",
}

SUPPORTED_COUNTRIES = ["Lithuania", "Latvia"]
SUPPORTED_DEVICES = ["Desktop", "Mobile"]

# ---------------------------------------------------------------------------
# Status colors  (execution status in the test run)
# Softer, eye-friendly palette — accessible on both light and dark backgrounds
# ---------------------------------------------------------------------------
STATUS_COLORS = {
    "Passed": "#34B78F",
    "Passed with Issue": "#6DC8A7",
    "Passed (stubbed)": "#E8C547",
    "Blocked": "#E8944A",
    "Failed": "#D96459",
    "Failed (Medium)": "#D96459",
    "Failed (Highest)": "#C0392B",
    "Not Applicable": "#A0A4AB",
    "To Do": "#8E7CC3",
    "No-Run": "#B8BCC5",
    "Untested": "#B8BCC5",
    "Retest": "#E6A06F",
}

# ---------------------------------------------------------------------------
# Automation lifecycle categories
# ---------------------------------------------------------------------------
AUTOMATED_STATUSES = ["Passed", "Passed with Issue", "Passed (stubbed)"]
IN_PROGRESS_STATUSES = ["Retest"]
BLOCKED_STATUSES = ["Blocked"]
FAILED_STATUSES = ["Failed", "Failed (Medium)", "Failed (Highest)"]
NOT_APPLICABLE_STATUSES = ["Not Applicable"]
BACKLOG_STATUSES = ["To Do", "No-Run", "Untested"]

CATEGORY_COLORS = {
    "Automated": "#34B78F",
    "In Progress": "#5BA4CF",
    "Blocked": "#E8944A",
    "Failed": "#D96459",
    "Not Applicable": "#A0A4AB",
    "Backlog": "#8E7CC3",
}

# Ordered list for consistent display
CATEGORY_ORDER = [
    "Automated",
    "In Progress",
    "Failed",
    "Blocked",
    "Not Applicable",
    "Backlog",
]

# ---------------------------------------------------------------------------
# Custom field system names (TestRail API returns custom_<system_name>)
# ---------------------------------------------------------------------------
CUSTOM_FIELDS = {
    "jira_task_drg": "custom_aqa_jira_task_drg",
    "jira_task_testim": "custom_aqa_jira_task_testim",
    "jira_task_testim_mobile": "custom_aqa_jira_task_testim_mobile",
    "automation_reason": "custom_automation_not_applicable_reason",
    "automation_status_desktop": "custom_automation_status_testim_desktop",
    "automation_status_mobile": "custom_automation_status_testim_mobile_view",
    "deprecated": "custom_deprecated",
    "device": "custom_device",
}

# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------
CACHE_TTL_SECONDS = 300  # 5 minutes

# ---------------------------------------------------------------------------
# Page settings
# ---------------------------------------------------------------------------
PAGE_TITLE = "Drogas AQA Dashboard"
PAGE_ICON = "\U0001F9EA"  # test tube emoji
PAGE_LAYOUT = "wide"
