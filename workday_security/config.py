"""Connection settings for a Workday tenant.

Credentials are read from environment variables so nothing sensitive lives in
the repository. For local development, copy ``.env.example`` to ``.env`` and
export the values (e.g. ``set -a; source .env; set +a``).
"""

from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigError(RuntimeError):
    """Raised when required connection settings are missing."""


@dataclass(frozen=True)
class WorkdayConfig:
    """Everything needed to reach a Workday tenant.

    Attributes:
        tenant: The tenant name (the segment in your Workday URL, e.g.
            ``acme_dpt1`` for ``https://impl.workday.com/acme_dpt1``).
        host: The Workday host, without scheme
            (e.g. ``impl-services1.workday.com`` or ``wd2-impl-services1.workday.com``).
        username: Integration System User (ISU) name. For WWS this is usually
            ``ISU_NAME@tenant``; the ``@tenant`` suffix is appended automatically
            if you do not include it.
        password: The ISU password.
        wws_version: Workday Web Services version, e.g. ``v43.0``.
    """

    tenant: str
    host: str
    username: str
    password: str
    wws_version: str = "v43.0"

    @classmethod
    def from_env(cls) -> "WorkdayConfig":
        """Build a config from ``WORKDAY_*`` environment variables.

        Required: ``WORKDAY_TENANT``, ``WORKDAY_HOST``, ``WORKDAY_USERNAME``,
        ``WORKDAY_PASSWORD``. Optional: ``WORKDAY_WWS_VERSION``.
        """
        missing = [
            name
            for name in ("WORKDAY_TENANT", "WORKDAY_HOST", "WORKDAY_USERNAME", "WORKDAY_PASSWORD")
            if not os.environ.get(name)
        ]
        if missing:
            raise ConfigError(
                "Missing required environment variables: " + ", ".join(missing)
            )
        return cls(
            tenant=os.environ["WORKDAY_TENANT"],
            host=os.environ["WORKDAY_HOST"],
            username=os.environ["WORKDAY_USERNAME"],
            password=os.environ["WORKDAY_PASSWORD"],
            wws_version=os.environ.get("WORKDAY_WWS_VERSION", "v43.0"),
        )

    @property
    def wws_username(self) -> str:
        """Username formatted for WWS basic auth (``user@tenant``)."""
        return self.username if "@" in self.username else f"{self.username}@{self.tenant}"

    def raas_base_url(self) -> str:
        """Base URL for custom-report RaaS endpoints for this tenant."""
        return f"https://{self.host}/ccx/service/customreport2/{self.tenant}"

    def wws_url(self, service: str) -> str:
        """SOAP endpoint URL for a given WWS service (e.g. ``Identity_Management``)."""
        return f"https://{self.host}/ccx/service/{self.tenant}/{service}/{self.wws_version}"
