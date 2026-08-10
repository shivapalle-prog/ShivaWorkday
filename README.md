# Workday Security Configuration Extractor

Pull **security configuration** out of a Workday tenant so it can be inspected,
audited, or diffed as code. This answers the practical question *"how do I
identify the security configurations in Workday?"* by extracting them
programmatically.

## What it extracts

| Concept | Workday meaning | Command |
|---|---|---|
| **Security groups** | Who gets access (Role-Based, User-Based, etc.) and their members | `groups` |
| **Domain security policies** | Access to data/tasks — View vs. Modify per group | `domains` |
| **Business process security policies** | Who can Initiate / Approve / View a business process | `bp` |
| **Any report** | Raw JSON from any RaaS report | `raas` |
| **Any `Get_*` op** | Raw XML from a SOAP Web Service operation | `wws` |

## How it works

Two transports, matching the two ways Workday exposes this data:

1. **RaaS (Reports-as-a-Service)** — *recommended*. In Workday, build a custom
   report over the delivered security data sources (e.g. **Domain Security
   Policies**, **Business Process Security Policies**, **Security Group
   Membership**), enable it as a web service, and read its JSON here. Report
   writers decide *what* to expose; this tool decides *how* to consume it.
2. **SOAP Web Services (WWS)** — call delivered `Get_*` operations directly
   (e.g. `Identity_Management / Get_Workday_Accounts`) with WS-Security auth.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env      # fill in tenant, host, ISU credentials
set -a; source .env; set +a
```

Credentials come from a Workday **Integration System User (ISU)** granted a
security group with **View** access to the security-administration domains you
report on. Nothing sensitive is stored in the repo — `.env` is git-ignored.

## Usage

```bash
# Parsed domain security policies
python -m workday_security domains --owner ISU_Security --report Domain_Security_Policies

# Parsed business process security policies
python -m workday_security bp --owner ISU_Security --report BP_Security_Policies

# Parsed security groups + membership
python -m workday_security groups --owner ISU_Security --report Security_Group_Membership

# Raw report JSON (any report), with a prompt parameter
python -m workday_security raas --owner ISU_Security --report My_Report --param Effective_Date=2026-08-10

# A SOAP Get_* operation
python -m workday_security wws --service Identity_Management --operation Get_Workday_Accounts
```

Report **field names vary per tenant** (they are whatever the report writer
named the columns). The extractors in `workday_security/extract.py` try common
names first; adjust them to match your report if a field comes back empty.

## Doing it in the Workday UI (no code)

If you just need to *look*, these delivered reports/tasks identify security
config directly in the tenant:

- `View Security Group`, `Security Groups for User`
- `View Security for Securable Item` — what secures a given report/task/field
- `Domain Security Policies for Functional Area`
- `Business Process Security Policies for Functional Area`
- `Security Analysis for Securable Item and Account`

## Tests

```bash
python -m pytest        # or: python -m unittest discover -s tests
```

Tests cover the pure config/parsing logic and require no network access.
