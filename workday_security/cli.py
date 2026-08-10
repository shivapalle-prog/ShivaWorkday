"""Command-line entry point for extracting Workday security configuration.

Examples:
    # Pull a domain-security-policy report and print parsed policies as JSON
    python -m workday_security domains --owner ISU_Security --report Domain_Security_Policies

    # Pull raw JSON from any RaaS report
    python -m workday_security raas --owner ISU_Security --report Security_Group_Membership

    # Call a WWS Get_* operation (SOAP) and print the returned XML
    python -m workday_security wws --service Identity_Management --operation Get_Workday_Accounts
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from dataclasses import asdict
from typing import List

from .config import ConfigError, WorkdayConfig
from .extract import (
    extract_bp_policies,
    extract_domain_policies,
    extract_security_groups,
)
from .raas_client import RaaSClient
from .soap_client import SoapClient, SoapFault


def _print_json(data) -> None:
    json.dump(data, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")


def _add_raas_args(sub: argparse.ArgumentParser) -> None:
    sub.add_argument("--owner", required=True, help="Report owner username (RaaS path segment)")
    sub.add_argument("--report", required=True, help="Report web-service name")
    sub.add_argument(
        "--param",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Report prompt parameter (repeatable)",
    )


def _params(pairs: List[str]) -> dict:
    out = {}
    for pair in pairs:
        if "=" not in pair:
            raise SystemExit(f"Invalid --param '{pair}', expected KEY=VALUE")
        key, value = pair.split("=", 1)
        out[key] = value
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="workday_security",
        description="Extract security configuration from a Workday tenant.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_raas = subparsers.add_parser("raas", help="Fetch a raw RaaS report as JSON")
    _add_raas_args(p_raas)

    p_domains = subparsers.add_parser("domains", help="Fetch + parse domain security policies")
    _add_raas_args(p_domains)

    p_bp = subparsers.add_parser("bp", help="Fetch + parse business process security policies")
    _add_raas_args(p_bp)

    p_groups = subparsers.add_parser("groups", help="Fetch + parse security groups / membership")
    _add_raas_args(p_groups)

    p_wws = subparsers.add_parser("wws", help="Call a WWS Get_* operation (SOAP)")
    p_wws.add_argument("--service", required=True, help="WWS service, e.g. Identity_Management")
    p_wws.add_argument("--operation", required=True, help="Operation, e.g. Get_Workday_Accounts")
    p_wws.add_argument("--page", type=int, default=1)
    p_wws.add_argument("--count", type=int, default=100)

    args = parser.parse_args(argv)

    try:
        config = WorkdayConfig.from_env()
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    try:
        if args.command == "wws":
            client = SoapClient(config)
            body = client.call(args.service, args.operation, page=args.page, count=args.count)
            sys.stdout.write(ET.tostring(body, encoding="unicode"))
            sys.stdout.write("\n")
            return 0

        raas = RaaSClient(config)
        payload = raas.fetch_report(args.owner, args.report, params=_params(args.param))
        rows = RaaSClient.report_rows(payload)

        if args.command == "raas":
            _print_json(payload)
        elif args.command == "domains":
            _print_json([asdict(p) for p in extract_domain_policies(rows)])
        elif args.command == "bp":
            _print_json([asdict(p) for p in extract_bp_policies(rows)])
        elif args.command == "groups":
            _print_json([asdict(g) for g in extract_security_groups(rows)])
        return 0
    except SoapFault as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 -- surface any transport error cleanly
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
