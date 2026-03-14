"""Shared utility functions."""

from __future__ import annotations

import re


def extract_jira_key(text: str) -> str:
    """Extract a Jira issue key (e.g. ``EE20-12345``) from arbitrary text."""
    if not text:
        return ""
    match = re.search(r"[A-Z][A-Z0-9]+-\d+", text)
    return match.group(0) if match else ""


def fmt_pct(value: float, decimals: int = 1) -> str:
    """Format a number as a percentage string."""
    return f"{value:.{decimals}f}%"


def truncate(text: str, max_len: int = 80) -> str:
    """Truncate *text* with an ellipsis when it exceeds *max_len*."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."
