"""Lightweight data classes describing Workday security objects.

These mirror the concepts you see in the Workday UI reports:

* Security groups -- who gets access.
* Domain security policies -- access to data/tasks (View / Modify).
* Business process security policies -- who can initiate/approve/view a BP.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SecurityGroup:
    """A Workday security group and (optionally) its members."""

    id: str
    name: str
    type: Optional[str] = None
    members: List[str] = field(default_factory=list)


@dataclass
class DomainSecurityPolicy:
    """Access granted to a security domain.

    ``view_groups`` and ``modify_groups`` list the security group names that
    have View and Get/Put (Modify) access respectively.
    """

    domain: str
    functional_area: Optional[str] = None
    view_groups: List[str] = field(default_factory=list)
    modify_groups: List[str] = field(default_factory=list)


@dataclass
class BusinessProcessSecurityPolicy:
    """Security policy for a business process type."""

    business_process: str
    functional_area: Optional[str] = None
    # Maps an action (e.g. "Initiate", "Approve", "View") -> security groups.
    permissions: dict = field(default_factory=dict)
