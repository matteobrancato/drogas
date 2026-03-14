"""
TestRail REST API client.

Handles authentication, pagination, and rate-limit retries for the
TestRail v2 API used by the Drogas AQA Dashboard.
"""

from __future__ import annotations

import time
from typing import Any

import requests
from requests.auth import HTTPBasicAuth


class TestRailAPIError(Exception):
    """Raised when the TestRail API returns a non-recoverable error."""


class TestRailClient:
    """Low-level HTTP client for the TestRail API v2."""

    _MAX_PAGE_SIZE = 250
    _RATE_LIMIT_RETRIES = 3

    def __init__(self, base_url: str, user: str, api_key: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_url = f"{self._base_url}/index.php?/api/v2"
        self._session = requests.Session()
        self._session.auth = HTTPBasicAuth(user, api_key)
        self._session.headers.update({"Content-Type": "application/json"})

    # ------------------------------------------------------------------
    # Internal HTTP helpers
    # ------------------------------------------------------------------

    def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        """Execute a GET request with automatic rate-limit retry."""
        url = f"{self._api_url}/{endpoint}"
        for attempt in range(self._RATE_LIMIT_RETRIES):
            resp = self._session.get(url, params=params, timeout=30)
            if resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After", 3))
                time.sleep(wait)
                continue
            if resp.status_code == 401:
                raise TestRailAPIError(
                    "Authentication failed. Check TESTRAIL_USER and TESTRAIL_API_KEY."
                )
            if resp.status_code == 400:
                body = resp.json() if resp.content else {}
                raise TestRailAPIError(
                    f"Bad request: {body.get('error', resp.text)}"
                )
            resp.raise_for_status()
            return resp.json()
        raise TestRailAPIError("Rate limit exceeded after retries.")

    def _get_paginated(
        self, endpoint: str, key: str, params: dict[str, Any] | None = None
    ) -> list[dict]:
        """Fetch all pages of a paginated endpoint.

        TestRail cloud returns ``{<key>: [...], "size": N, ...}``.
        Older on-premise instances may return a plain list instead.
        """
        all_items: list[dict] = []
        offset = 0
        extra = dict(params) if params else {}

        while True:
            extra["limit"] = self._MAX_PAGE_SIZE
            extra["offset"] = offset
            data = self._get(endpoint, params=extra)

            if isinstance(data, list):
                # Non-paginated (older API)
                all_items.extend(data)
                break

            items = data.get(key, [])
            all_items.extend(items)

            if data.get("size", 0) < self._MAX_PAGE_SIZE:
                break
            offset += self._MAX_PAGE_SIZE

        return all_items

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def get_plan(self, plan_id: int) -> dict:
        """Return the full test plan including entries and runs."""
        return self._get(f"get_plan/{plan_id}")

    def get_tests(self, run_id: int) -> list[dict]:
        """Return every test in a run (handles pagination)."""
        return self._get_paginated(f"get_tests/{run_id}", key="tests")

    def get_statuses(self) -> list[dict]:
        """Return all status definitions (built-in + custom)."""
        data = self._get("get_statuses")
        return data if isinstance(data, list) else data.get("statuses", data)

    def get_case_fields(self) -> list[dict]:
        """Return custom field definitions for test cases."""
        data = self._get("get_case_fields")
        return data if isinstance(data, list) else data.get("case_fields", data)

    def get_users(self) -> list[dict]:
        """Return all users (best-effort; some instances restrict access)."""
        try:
            data = self._get("get_users")
            if isinstance(data, list):
                return data
            return data.get("users", [])
        except Exception:
            return []
