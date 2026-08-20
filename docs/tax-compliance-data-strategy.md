# Data Strategy for Tax Compliance Use Cases

> **Status:** Draft v1.0 · **Owner:** Data & Platform · **Last updated:** 2026-08-20
> **Audience:** Data engineering, data governance, product, tax content, compliance, and security stakeholders.

---

## 1. Executive Summary

Tax compliance is a **data-intensive, high-stakes, low-error-tolerance** domain. A single
mis-classified product, a stale tax rate, or an unmapped jurisdiction can produce an incorrect
filing, an under- or over-collection of tax, and downstream audit exposure for the business and
its customers.

This strategy defines how we **acquire, model, govern, secure, and serve** the data required to
power tax compliance products — determination, returns, exemption management, nexus, and audit
defense — with the accuracy, auditability, and latency those use cases demand.

**Guiding outcomes:**

| Outcome | Target |
|---|---|
| Determination accuracy | Correct rate & taxability for every transaction, every jurisdiction |
| Content freshness | Rate/rule changes reflected before their statutory effective date |
| Auditability | Every filed number reconstructable to source, rule version, and time |
| Latency | Real-time determination at checkout; batch for returns & reconciliation |
| Trust | Data lineage, quality SLAs, and access controls provable to auditors |

---

## 2. Why Tax Compliance Data Is Different

Design decisions must respect these domain properties:

1. **Temporality is first-class.** Rates and rules have *effective dates* and *expiry dates*. A
   transaction is taxed by the rule in force **on the transaction date**, not today. Everything is
   bitemporal: *valid time* (when the rule applies in the real world) and *system time* (when we
   learned it).
2. **Point-in-time reproducibility is mandatory.** During an audit years later, we must reproduce
   the exact determination using the exact content version that was live at that time.
3. **Jurisdictional explosion.** ~13,000+ US sales-tax jurisdictions plus global VAT/GST regimes.
   Boundaries do not follow ZIP codes — rooftop/geospatial precision matters.
4. **Regulatory volatility.** Thousands of rate and rule changes per year, arriving in
   inconsistent formats from thousands of authorities.
5. **Correctness over availability trade-off is inverted vs. typical apps.** A wrong answer is worse
   than a slow answer or a controlled fallback.

---

## 3. Core Use Cases (and their data needs)

| # | Use case | Primary data needs | Latency |
|---|---|---|---|
| U1 | **Real-time tax determination** (checkout, invoicing) | Product taxability, jurisdiction rates/rules, address→jurisdiction resolution, customer exemptions | < 100 ms p99 |
| U2 | **Returns preparation & filing** | Aggregated transactions, jurisdiction registrations, filing calendars, form templates | Batch (daily/monthly) |
| U3 | **Exemption & resale certificate management** | Certificate images/metadata, validity by jurisdiction, customer↔cert mapping, expiry | Near-real-time |
| U4 | **Nexus determination & registration** | Economic/physical nexus thresholds, rolling sales & transaction counts by jurisdiction | Daily |
| U5 | **Audit defense & reconciliation** | Immutable transaction ledger, determination provenance, rule versions, documents | On demand |
| U6 | **Tax content management** | Rates, rules, boundaries, product taxability matrices, sourcing rules | Continuous ingest |
| U7 | **Reporting & analytics** | Liability by jurisdiction, exemption leakage, filing accuracy, anomaly detection | Batch + interactive |
| U8 | **Cross-border / VAT-GST** | VAT rates, reverse charge, place-of-supply, EU OSS/IOSS, HS/commodity codes | Real-time + batch |

---

## 4. Guiding Principles

1. **Immutability & append-only.** Transactions and determinations are never mutated; corrections
   are new versioned records. The ledger is the source of truth for audit.
2. **Bitemporal by default.** Model both valid time and system time for all content.
3. **Content as versioned, governed product.** Tax content is a data product with owners, SLAs,
   quality gates, and semantic versioning.
4. **Lineage end-to-end.** Every served value traces to source document → transform → rule version.
5. **Determination is deterministic & reproducible.** Given the same inputs + content version, the
   output is identical, forever.
6. **Privacy & least privilege.** Transaction and customer data is sensitive (PII, financial);
   minimize, encrypt, and restrict.
7. **Fail safe, not silent.** On uncertainty, surface confidence and fall back to conservative,
   auditable behavior — never a silent guess.
8. **Separation of content and computation.** Tax logic (rules) is data, not code, wherever
   possible, so content changes don't require deployments.

---

## 5. Data Domains & Taxonomy

Organize the estate into governed domains, each with a clear owner:

- **Tax Content** — rates, rules, taxability matrices, sourcing rules, boundaries, filing calendars,
  forms. *(Owner: Tax Content Engineering)*
- **Geospatial / Jurisdiction** — address normalization, rooftop geocoding, jurisdiction
  assignment, boundary polygons. *(Owner: Geo/Platform)*
- **Transactions** — line-item sales/purchase events and their determinations. *(Owner: Core Platform)*
- **Customer & Entity** — registrations, nexus profiles, exemption certificates, org hierarchy.
  *(Owner: Customer Data / MDM)*
- **Product / Item** — item catalog, tax codes, mapping & classification. *(Owner: Product Content)*
- **Filing & Remittance** — returns, payments, filing status, reconciliations. *(Owner: Returns)*
- **Reference / Master Data** — currencies, FX, country/region codes, HS codes, calendars.
- **Operational & Audit** — lineage, quality metrics, access logs, change history.

---

## 6. Reference Architecture

A layered **medallion-style** architecture with a real-time serving path:

```
                          ┌──────────────────────────────────────────────┐
  SOURCES                 │                INGESTION                       │
  ─ Tax authority feeds ─▶│  Batch (files/APIs) · Streaming (CDC/events)   │
  ─ Rate/rule vendors   ─▶│  Schema validation · dedup · quarantine        │
  ─ Boundary/geo data   ─▶│                                                │
  ─ Customer txns (API) ─▶└───────────────┬────────────────────────────────┘
  ─ Cert uploads (docs)                    │
                                           ▼
   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
   │ BRONZE (raw)  │──▶│ SILVER        │──▶│ GOLD          │──▶│ SERVING        │
   │ immutable     │   │ conformed,    │   │ curated data  │   │ low-latency    │
   │ landing zone  │   │ validated,    │   │ products:     │   │ stores:        │
   │ full history  │   │ bitemporal    │   │ determination │   │ ─ rate/rule KV │
   │               │   │               │   │ content, agg  │   │ ─ geo index    │
   └───────────────┘   └───────────────┘   │ returns marts │   │ ─ feature store│
                                           └───────────────┘   └───────────────┘
                                                                        │
                             ┌──────────────────────────────────────────┤
                             ▼                        ▼                   ▼
                    Determination Engine      Returns/Reporting     ML/Anomaly
                    (real-time API)           (batch marts)         detection

  CROSS-CUTTING: Catalog & Lineage · Data Quality · Governance/Access · Observability · Audit ledger
```

### 6.1 Ingestion
- **Batch** for vendor rate files, boundary datasets, filing calendars (validated, schema-checked,
  quarantined on failure).
- **Streaming/CDC** for transaction events and certificate uploads.
- **Contract-first**: every source has a published schema/data contract; breaking changes are
  versioned and gated.
- **Quarantine, don't drop**: bad records are isolated with reason codes for remediation, never
  silently discarded.

### 6.2 Storage (medallion)
- **Bronze** — immutable raw landing, full fidelity, replayable.
- **Silver** — conformed, deduplicated, validated, bitemporal.
- **Gold** — curated **data products** ready for consumption (determination content, returns marts,
  nexus rollups).
- **Serving** — purpose-built low-latency stores: a rate/rule key-value/cache layer, a geospatial
  index for jurisdiction assignment, and a feature store for ML.

### 6.3 Processing
- **Streaming** for real-time determination inputs and event enrichment.
- **Batch** for returns aggregation, nexus rollups, reconciliation, and content publication.
- **Lakehouse** table format (ACID, time travel, schema evolution) so history and point-in-time
  queries are native.

### 6.4 Serving
- Determination engine reads from an in-memory/replicated content cache keyed by
  `(jurisdiction, tax_type, effective_date, product_tax_code)`.
- Content is **published as versioned snapshots**; the engine pins a version so a mid-request
  content update never changes an in-flight determination.

---

## 7. Data Modeling for Tax

### 7.1 Bitemporal content
Every content row carries:
`valid_from`, `valid_to` (real-world effective window) **and**
`system_from`, `system_to` (when we knew it) **and** `content_version` / `source_ref`.

Determination always queries: *"the rule where `valid_from ≤ txn_date < valid_to`, as known at
`system_time = determination_time`."*

### 7.2 Determination provenance (immutable)
Each determination record stores the **inputs**, the **content version** used, the **rule IDs**
fired, the **jurisdiction stack** resolved, and the **result** — enough to reproduce it exactly.

### 7.3 Key relationships
- Transaction → Determination (1:many corrections, append-only)
- Customer → Exemption Certificate → Jurisdiction (validity windows)
- Product → Tax Code → Taxability (per jurisdiction, bitemporal)
- Address → Jurisdiction Stack (country/state/county/city/special districts)

### 7.4 Master data (MDM)
Golden records for **Customer/Entity** and **Product/Item** with survivorship rules,
de-duplication, and stable surrogate keys — critical because exemptions and taxability hang off
these entities.

---

## 8. Data Governance

| Pillar | Practice |
|---|---|
| **Catalog & discovery** | Central catalog; every data product documented, owned, discoverable |
| **Lineage** | Automated column-level lineage source→serving; required for audit |
| **Quality** | Contracted expectations (see §9) with block/warn gates and SLAs |
| **Master data** | Golden records for customer & product; survivorship + stewardship |
| **Retention** | Statute-driven retention (typically 7–10+ yrs); legal-hold support |
| **Change management** | Content changes reviewed, versioned, effective-dated, auditable |
| **Access** | RBAC/ABAC, least privilege, data classification-driven |

---

## 9. Data Quality Framework

Tax accuracy = content accuracy × mapping accuracy × jurisdiction accuracy. Instrument all three.

**Dimensions & example checks:**
- **Accuracy** — rate values within plausible bounds; regression tests vs. known-good scenarios.
- **Completeness** — no jurisdiction missing a rate for an active tax type.
- **Timeliness** — rate change ingested before `valid_from`; SLA alarms on lag.
- **Consistency** — jurisdiction hierarchy sums correctly; no overlapping effective windows.
- **Validity** — codes conform to reference sets (jurisdiction, tax type, product tax code).
- **Uniqueness** — no duplicate active rules for the same key/period.

**Controls:**
- **Golden test suite** of canonical transactions with expected results, run on every content publish.
- **Shadow / champion-challenger** comparison of new vs. current content before promotion.
- **Anomaly detection** on rate deltas (e.g., a "7% → 70%" typo blocked automatically).
- **Quarantine + steward workflow** for failures; publish is **gated** on quality pass.

---

## 10. Security & Privacy

- **Classification:** transactions and certificates contain PII and financial data → *Restricted*.
- **Encryption** in transit and at rest; field/column-level encryption or tokenization for PII.
- **Access:** least-privilege RBAC/ABAC; break-glass access logged and reviewed.
- **Data minimization & residency:** collect only what determination/filing needs; honor
  cross-border data residency (esp. EU/UK) for VAT data.
- **Regulatory alignment:** SOC 2, GDPR/CCPA (subject rights, retention limits vs. tax retention
  obligations — reconcile explicitly), PCI scope kept out of the tax data path where possible.
- **Audit logging:** immutable access and change logs; tamper-evident.

---

## 11. AI / ML Opportunities

| Opportunity | Data leveraged | Value |
|---|---|---|
| **Product tax-code classification** | Item catalog + taxability history | Reduce manual mapping, improve accuracy |
| **Rate/rule change extraction (NLP)** | Authority bulletins, statutes | Faster, cheaper content updates |
| **Anomaly/error detection** | Transaction & determination streams | Catch mis-collections, exemption leakage |
| **Audit-risk scoring** | Filing + transaction patterns | Prioritize review, reduce exposure |
| **Certificate OCR/validation** | Uploaded certificate documents | Automate exemption intake |

**Guardrails:** ML *assists* content and classification but final tax logic remains deterministic,
auditable, and human-reviewable. Every ML-derived value carries a confidence score and provenance;
low-confidence cases route to human review. Use a **feature store** for consistent train/serve
features and reproducibility.

---

## 12. Operating Model

- **Data product ownership** per domain (§5), each with an accountable owner and SLA.
- **Federated governance**: central standards (contracts, quality, security), domain-level execution.
- **Roles:** Data Product Owners, Data Stewards (esp. tax content), Platform/Data Engineering,
  Governance/Privacy, ML Engineering.
- **Publish workflow:** content change → validate → quality gate → shadow compare → version →
  effective-date → promote → notify consumers.

---

## 13. Metrics & KPIs

| Category | KPI |
|---|---|
| Accuracy | Determination accuracy vs. golden set; audit adjustment rate |
| Freshness | % rate changes live before effective date; content lag (hrs) |
| Quality | % records passing quality gates; quarantine rate & MTTR |
| Coverage | % jurisdictions/tax types with complete active content |
| Reliability | Determination API p99 latency; availability |
| Governance | % data products cataloged with lineage; access review completion |
| Business | Exemption leakage $, filing accuracy %, audit findings count |

---

## 14. Phased Roadmap

**Phase 0 — Foundations (0–3 mo)**
Data contracts, catalog, classification, bronze landing, immutable transaction ledger, baseline
lineage and access controls.

**Phase 1 — Content & determination core (3–6 mo)**
Bitemporal content model, versioned content publishing, golden test suite + quality gates,
low-latency serving cache, determination provenance.

**Phase 2 — Compliance breadth (6–12 mo)**
Returns/nexus marts, exemption certificate pipeline, geospatial jurisdiction assignment, reporting
& reconciliation, VAT/GST cross-border modeling.

**Phase 3 — Intelligence (12+ mo)**
Feature store, ML classification & rate-change extraction, anomaly & audit-risk scoring, continuous
optimization.

---

## 15. Key Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Stale/incorrect content → wrong tax | Quality gates, anomaly detection, effective-date SLAs, golden tests |
| Non-reproducible audits | Bitemporal content + immutable determination provenance + version pinning |
| Jurisdiction mis-assignment | Rooftop geocoding, boundary polygons, address normalization |
| PII/financial data exposure | Classification, encryption/tokenization, least privilege, audit logs |
| Regulatory retention vs. privacy conflict | Explicit retention policy reconciling tax law with GDPR/CCPA |
| Content change breaks consumers | Data contracts, semantic versioning, shadow deploys, consumer notifications |
| Latency SLA breaches at checkout | Replicated content cache, version pinning, fail-safe fallbacks |

---

## 16. Summary

Treat **tax content and transactions as governed, versioned, bitemporal data products** served
through a layered architecture with **immutable provenance, strong quality gates, and end-to-end
lineage**. This delivers the three things tax compliance cannot compromise on: **accuracy,
auditability, and reproducibility** — while enabling real-time determination, efficient filing, and
ML-driven improvement over time.
