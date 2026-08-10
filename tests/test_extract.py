"""Unit tests for the pure extraction/config logic (no network)."""

import os
import unittest

from workday_security.config import ConfigError, WorkdayConfig
from workday_security.extract import (
    extract_bp_policies,
    extract_domain_policies,
    extract_security_groups,
)
from workday_security.raas_client import RaaSClient


class ConfigTests(unittest.TestCase):
    def test_wws_username_appends_tenant(self):
        cfg = WorkdayConfig(tenant="acme", host="h", username="ISU", password="p")
        self.assertEqual(cfg.wws_username, "ISU@acme")

    def test_wws_username_preserves_explicit_tenant(self):
        cfg = WorkdayConfig(tenant="acme", host="h", username="ISU@acme", password="p")
        self.assertEqual(cfg.wws_username, "ISU@acme")

    def test_urls(self):
        cfg = WorkdayConfig(tenant="acme", host="h.workday.com", username="ISU", password="p")
        self.assertEqual(
            cfg.raas_base_url(),
            "https://h.workday.com/ccx/service/customreport2/acme",
        )
        self.assertEqual(
            cfg.wws_url("Identity_Management"),
            "https://h.workday.com/ccx/service/acme/Identity_Management/v43.0",
        )

    def test_from_env_missing(self):
        for key in ("WORKDAY_TENANT", "WORKDAY_HOST", "WORKDAY_USERNAME", "WORKDAY_PASSWORD"):
            os.environ.pop(key, None)
        with self.assertRaises(ConfigError):
            WorkdayConfig.from_env()


class ReportRowsTests(unittest.TestCase):
    def test_wrapped(self):
        payload = {"Report_Entry": [{"a": 1}]}
        self.assertEqual(RaaSClient.report_rows(payload), [{"a": 1}])

    def test_bare_list(self):
        self.assertEqual(RaaSClient.report_rows([{"a": 1}]), [{"a": 1}])

    def test_empty(self):
        self.assertEqual(RaaSClient.report_rows({}), [])
        self.assertEqual(RaaSClient.report_rows(None), [])


class ExtractTests(unittest.TestCase):
    def test_security_groups(self):
        rows = [
            {
                "Security_Group_ID": "SG1",
                "Security_Group": "HR Partner",
                "Security_Group_Type": "Role-Based",
                "Members": [{"Descriptor": "Alice"}, {"Descriptor": "Bob"}],
            }
        ]
        groups = extract_security_groups(rows)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].id, "SG1")
        self.assertEqual(groups[0].name, "HR Partner")
        self.assertEqual(groups[0].type, "Role-Based")
        self.assertEqual(groups[0].members, ["Alice", "Bob"])

    def test_domain_policies(self):
        rows = [
            {
                "Domain": "Worker Data: Personal",
                "Functional_Area": "Personal Data",
                "View_Only_Security_Groups": [{"Descriptor": "Auditor"}],
                "View_Modify_Security_Groups": [{"Descriptor": "HR Partner"}],
            }
        ]
        policies = extract_domain_policies(rows)
        self.assertEqual(policies[0].domain, "Worker Data: Personal")
        self.assertEqual(policies[0].functional_area, "Personal Data")
        self.assertEqual(policies[0].view_groups, ["Auditor"])
        self.assertEqual(policies[0].modify_groups, ["HR Partner"])

    def test_bp_policies_fold_actions(self):
        rows = [
            {
                "Business_Process": "Hire",
                "Functional_Area": "Staffing",
                "Action": "Initiate",
                "Security_Groups": [{"Descriptor": "HR Partner"}],
            },
            {
                "Business_Process": "Hire",
                "Action": "Approve",
                "Security_Groups": [{"Descriptor": "Manager"}, {"Descriptor": "Manager"}],
            },
        ]
        policies = extract_bp_policies(rows)
        self.assertEqual(len(policies), 1)
        self.assertEqual(policies[0].business_process, "Hire")
        self.assertEqual(policies[0].permissions["Initiate"], ["HR Partner"])
        # Duplicate group folded to a single entry.
        self.assertEqual(policies[0].permissions["Approve"], ["Manager"])


if __name__ == "__main__":
    unittest.main()
