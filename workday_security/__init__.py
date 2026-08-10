"""Workday security configuration extraction toolkit.

This package pulls security configuration out of a Workday tenant so it can be
inspected, audited, or diffed as code. Two transports are supported:

* RaaS (Reports-as-a-Service) -- consume any custom/standard report published
  as a REST endpoint. Simplest path; returns JSON/CSV.
* SOAP Web Services (WWS) -- call the delivered ``Get_*`` operations directly.
  Used here for security groups via the Identity Management service.

See ``README.md`` for setup and usage.
"""

from .config import WorkdayConfig
from .models import (
    BusinessProcessSecurityPolicy,
    DomainSecurityPolicy,
    SecurityGroup,
)
from .raas_client import RaaSClient
from .soap_client import SoapClient

__all__ = [
    "WorkdayConfig",
    "RaaSClient",
    "SoapClient",
    "SecurityGroup",
    "DomainSecurityPolicy",
    "BusinessProcessSecurityPolicy",
]

__version__ = "0.1.0"
