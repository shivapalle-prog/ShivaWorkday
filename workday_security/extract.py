"""Turn RaaS report rows into the security model objects.

Report field names differ per tenant (they are whatever the report writer
named the columns), so each extractor takes a small ``FieldMap`` you can adjust
to match your report. Defaults follow common Workday naming conventions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .models import (
    BusinessProcessSecurityPolicy,
    DomainSecurityPolicy,
    SecurityGroup,
)


def _as_list(value: Any) -> List[str]:
    """Normalise a RaaS cell into a list of display strings.

    Workday multi-instance fields arrive as a list of ``{"Descriptor": ...}``
    dicts; single values as a string; blanks as ``None``.
    """
    if value is None or value == "":
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [value.get("Descriptor") or value.get("value") or str(value)]
    if isinstance(value, list):
        out: List[str] = []
        for item in value:
            out.extend(_as_list(item))
        return out
    return [str(value)]


def _first(row: Dict[str, Any], *keys: str, default: str = "") -> str:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            values = _as_list(row[key])
            if values:
                return values[0]
    return default


def extract_security_groups(rows: List[Dict[str, Any]]) -> List[SecurityGroup]:
    """Map rows from a 'Security Group Membership'-style report."""
    groups: List[SecurityGroup] = []
    for row in rows:
        groups.append(
            SecurityGroup(
                id=_first(row, "Security_Group_ID", "ID"),
                name=_first(row, "Security_Group", "Security_Group_Name", "Name"),
                type=_first(row, "Security_Group_Type", "Type") or None,
                members=_as_list(row.get("Members") or row.get("Member")),
            )
        )
    return groups


def extract_domain_policies(rows: List[Dict[str, Any]]) -> List[DomainSecurityPolicy]:
    """Map rows from a 'Domain Security Policies'-style report."""
    policies: List[DomainSecurityPolicy] = []
    for row in rows:
        policies.append(
            DomainSecurityPolicy(
                domain=_first(row, "Domain", "Security_Domain", "Domain_Name"),
                functional_area=_first(row, "Functional_Area") or None,
                view_groups=_as_list(
                    row.get("View_Only_Security_Groups") or row.get("View_Groups")
                ),
                modify_groups=_as_list(
                    row.get("View_Modify_Security_Groups") or row.get("Modify_Groups")
                ),
            )
        )
    return policies


def extract_bp_policies(rows: List[Dict[str, Any]]) -> List[BusinessProcessSecurityPolicy]:
    """Map rows from a 'Business Process Security Policies'-style report.

    Each row is expected to describe one (business process, action) grant; rows
    are folded together per business process into an action -> groups map.
    """
    by_bp: Dict[str, BusinessProcessSecurityPolicy] = {}
    for row in rows:
        bp = _first(row, "Business_Process", "Business_Process_Type", "Name")
        if not bp:
            continue
        policy = by_bp.setdefault(
            bp,
            BusinessProcessSecurityPolicy(
                business_process=bp,
                functional_area=_first(row, "Functional_Area") or None,
            ),
        )
        action = _first(row, "Action", "Step", "Security_Group_Action") or "Access"
        groups = _as_list(row.get("Security_Groups") or row.get("Security_Group"))
        policy.permissions.setdefault(action, [])
        for group in groups:
            if group not in policy.permissions[action]:
                policy.permissions[action].append(group)
    return list(by_bp.values())
