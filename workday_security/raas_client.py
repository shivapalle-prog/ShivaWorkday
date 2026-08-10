"""Consume Workday RaaS (Reports-as-a-Service) endpoints.

RaaS is the easiest way to extract security configuration: build a custom
report in Workday over the delivered security data sources (e.g. "Domain
Security Policies", "Business Process Security Policies", "Security Group
Membership"), enable it as a web service, and read the JSON here.

This keeps the *what to extract* decision in Workday (where report writers
live) and the *how to consume it* decision in code.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

from .config import WorkdayConfig

DEFAULT_TIMEOUT = 120


class RaaSClient:
    """Thin client for custom-report RaaS endpoints."""

    def __init__(self, config: WorkdayConfig, session: Optional[requests.Session] = None):
        self._config = config
        self._session = session or requests.Session()

    def fetch_report(
        self,
        report_owner: str,
        report_name: str,
        params: Optional[Dict[str, Any]] = None,
        fmt: str = "json",
    ) -> Any:
        """Fetch a RaaS report.

        Args:
            report_owner: The username that owns the report (the path segment
                after the tenant in the RaaS URL).
            report_name: The report's web-service name.
            params: Optional report prompt parameters (become query string args).
            fmt: Output format -- ``json`` (parsed) or ``csv``/``xml`` (raw text).

        Returns:
            Parsed JSON (dict/list) for ``json``, otherwise the raw response text.
        """
        url = f"{self._config.raas_base_url()}/{report_owner}/{report_name}"
        query: Dict[str, Any] = {"format": fmt}
        if params:
            query.update(params)

        resp = self._session.get(
            url,
            params=query,
            auth=(self._config.wws_username, self._config.password),
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
        if fmt == "json":
            return resp.json()
        return resp.text

    @staticmethod
    def report_rows(payload: Any) -> List[Dict[str, Any]]:
        """Extract the data rows from a Workday RaaS JSON payload.

        Workday wraps rows under a top-level ``Report_Entry`` key. This helper
        tolerates either the wrapped form or a bare list.
        """
        if isinstance(payload, dict):
            return payload.get("Report_Entry", []) or []
        if isinstance(payload, list):
            return payload
        return []
