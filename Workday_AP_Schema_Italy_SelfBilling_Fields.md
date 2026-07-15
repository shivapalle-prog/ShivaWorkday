# Workday AP Schema — Fields Required for Italy Self‑Billing (UBL Mapping)

**Purpose:** Identify the fields that must be present/added in the **Workday Accounts Payable (Supplier Invoice) schema in Connector Studio** so they can be mapped to the corresponding **UBL** elements required for the **Italy Self‑Billing (autofattura / reverse‑charge integration)** flow.

**Reference payload:** `selfinvoice_Italy.xml` (UBL 2.1 Invoice, PEPPOL BIS Billing 3.0 + `en16931` + FatturaPA extension).

---

## 1. Why these fields are special

In an Italy **self‑billing** scenario the *buyer* (the Italian Workday tenant) issues the tax document on behalf of, or in place of, the *supplier* (often a foreign vendor). This is driven from **Accounts Payable** data (supplier invoice), not from a normal sales invoice. Standard Workday AP extracts do **not** natively carry the Italian e‑invoicing / FatturaPA fields, so those must be added to the AP schema in Connector Studio and mapped to UBL.

The payload uses **`TD16`** (`TipoDocumento`), which is the FatturaPA code for a reverse‑charge / self‑invoice integration document. This single value is the master indicator that the AP document must be routed through the self‑billing template.

Legend for the **Category** column:
- **NEW (Italy)** — Italy‑self‑billing–specific field that typically must be **added** to the AP schema.
- **AP** — usually already available in the standard Workday Supplier Invoice extract (confirm it is exposed in the schema).
- **Const/Derived** — a constant or value derived by the connector; no Workday source field needed.

---

## 2. Document / Header level

| # | Proposed Workday AP Schema field | UBL / FatturaPA path | Sample value | Category | Notes |
|---|----------------------------------|----------------------|--------------|----------|-------|
| 1 | `ItalyDocumentTypeCode` (TipoDocumento) | `ext:UBLExtensions/ext:UBLExtension[ExtensionURI='urn:fdc:agid.gov.it:fatturapa:TipoDocumento']/ext:ExtensionContent/cbc:TypeCode` | `TD16` | **NEW (Italy)** | **Master self‑billing indicator.** TD16/TD17/TD18/TD19 select the reverse‑charge / self‑invoice sub‑scenario. Must be added and populated from AP (e.g. supplier‑invoice attribute / custom worktag / document‑type mapping). |
| 2 | `UBLVersionID` | `cbc:UBLVersionID` | `2.1` | Const/Derived | Fixed. |
| 3 | `CustomizationID` | `cbc:CustomizationID` | `urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0` | Const/Derived | Fixed for the profile. |
| 4 | `ProfileID` | `cbc:ProfileID` | `urn:fdc:peppol.eu:2017:poacc:billing:01:1.0` | Const/Derived | Fixed for the profile. |
| 5 | `InvoiceNumber` | `cbc:ID` | `Ab123` | AP | Self‑invoice document number (may need a dedicated self‑billing numbering series). |
| 6 | `InvoiceIssueDate` | `cbc:IssueDate` | `2026-01-01` | AP | Date the self‑invoice is issued. |
| 7 | `DueDate` | `cbc:DueDate` | `2026-12-31` | AP | Payment due date. |
| 8 | `InvoiceTypeCode` | `cbc:InvoiceTypeCode` | `380` | Const/Derived | UNCL1001 code (380 = commercial invoice). |
| 9 | `DocumentCurrencyCode` | `cbc:DocumentCurrencyCode` | `EUR` | AP | Document currency. |

---

## 3. Supplier party — `cac:AccountingSupplierParty` (the foreign vendor)

In self‑billing the **supplier = the vendor** on the AP invoice. Foreign‑vendor tax identification must be supported.

| # | Proposed Workday AP Schema field | UBL path | Sample value | Category | Notes |
|---|----------------------------------|----------|--------------|----------|-------|
| 10 | `SupplierName` | `cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name` | `Vendor` | AP | Vendor name. |
| 11 | `SupplierStreetName` | `.../cac:PostalAddress/cbc:StreetName` | `Via Roma 1` | AP | |
| 12 | `SupplierCityName` | `.../cac:PostalAddress/cbc:CityName` | `MILANO` | AP | |
| 13 | `SupplierPostalZone` | `.../cac:PostalAddress/cbc:PostalZone` | `20124` | AP | |
| 14 | `SupplierCountryCode` | `.../cac:PostalAddress/cac:Country/cbc:IdentificationCode` | `FR` | AP | **Foreign country supported** (drives TD16/TD17/TD18/TD19 logic). |
| 15 | `SupplierVATId` (Partita IVA / foreign VAT) | `.../cac:PartyTaxScheme/cbc:CompanyID` | `FR98765432100` | AP | Vendor VAT number incl. country prefix. |
| 16 | `SupplierTaxRegimeCode` (Regime Fiscale) | `.../cac:PartyTaxScheme/cbc:TaxLevelCode` | `RF01` | **NEW (Italy)** | FatturaPA RegimeFiscale (RF01–RF19). Add to AP schema. |
| 17 | `SupplierTaxSchemeID` | `.../cac:PartyTaxScheme/cac:TaxScheme/cbc:ID` | `VAT` | Const/Derived | |
| 18 | `SupplierLegalRegistrationName` | `.../cac:PartyLegalEntity/cbc:RegistrationName` | `Vendor` | AP | |

---

## 4. Customer party — `cac:AccountingCustomerParty` (the Italian self‑billing entity / Workday tenant)

In self‑billing the **customer = your own Italian company** that receives the goods/services and self‑issues the document.

| # | Proposed Workday AP Schema field | UBL path | Sample value | Category | Notes |
|---|----------------------------------|----------|--------------|----------|-------|
| 19 | `CustomerEndpointID` (Codice Destinatario / SDI) | `cac:AccountingCustomerParty/cac:Party/cbc:EndpointID` | `WSGICQN` | **NEW (Italy)** | SDI recipient / routing endpoint. Add to AP schema. |
| 20 | `CustomerEndpointSchemeID` | `cac:.../cbc:EndpointID/@schemeID` | `0205` | **NEW (Italy)** | Scheme qualifier for the endpoint (attribute). |
| 21 | `CustomerName` | `.../cac:PartyName/cbc:Name` | `TEST IDs` | AP | Your company name (from company/legal entity setup). |
| 22 | `CustomerStreetName` | `.../cac:PostalAddress/cbc:StreetName` | `Via Roma 1` | AP | |
| 23 | `CustomerCityName` | `.../cac:PostalAddress/cbc:CityName` | `MILANO` | AP | |
| 24 | `CustomerPostalZone` | `.../cac:PostalAddress/cbc:PostalZone` | `20124` | AP | |
| 25 | `CustomerCountryCode` | `.../cac:PostalAddress/cac:Country/cbc:IdentificationCode` | `IT` | AP | |
| 26 | `CustomerVATId` (Partita IVA) | `.../cac:PartyTaxScheme/cbc:CompanyID` | `IT15844561009` | AP | Italian company VAT. |
| 27 | `CustomerTaxRegimeCode` (Regime Fiscale) | `.../cac:PartyTaxScheme/cbc:TaxLevelCode` | `RF01` | **NEW (Italy)** | Add to AP schema. |
| 28 | `CustomerTaxSchemeID` | `.../cac:PartyTaxScheme/cac:TaxScheme/cbc:ID` | `VAT` | Const/Derived | |
| 29 | `CustomerLegalRegistrationName` | `.../cac:PartyLegalEntity/cbc:RegistrationName` | `TEST ID2` | AP | |
| 30 | `CustomerFiscalCode` (Codice Fiscale) | `.../cac:PartyLegalEntity/cbc:CompanyID` | `CF:06377691008` | **NEW (Italy)** | Italian Codice Fiscale, distinct from Partita IVA. Add to AP schema. |

---

## 5. Tax — `cac:TaxTotal` / `cac:TaxSubtotal`

| # | Proposed Workday AP Schema field | UBL path | Sample value | Category | Notes |
|---|----------------------------------|----------|--------------|----------|-------|
| 31 | `TotalTaxAmount` | `cac:TaxTotal/cbc:TaxAmount` | `1100.00` | AP | Total VAT (the self‑assessed reverse‑charge VAT). |
| 32 | `TaxableAmount` | `cac:TaxSubtotal/cbc:TaxableAmount` | `5000.00` | AP | |
| 33 | `SubtotalTaxAmount` | `cac:TaxSubtotal/cbc:TaxAmount` | `1100.00` | AP | |
| 34 | `TaxCategoryCode` | `cac:TaxCategory/cbc:ID` | `I` | AP/NEW | UNCL5305 category; verify Italy category values are supported. |
| 35 | `TaxPercent` | `cac:TaxCategory/cbc:Percent` | `22` | AP | VAT rate. |
| 36 | `TaxSchemeID` | `cac:TaxCategory/cac:TaxScheme/cbc:ID` | `VAT` | Const/Derived | |
| 37 | `TaxExemptionReason` / `Natura` | `cac:TaxScheme/cbc:TaxExemptionReason` | `22 - 22% - GENERICO` | **NEW (Italy)** | Carries the FatturaPA **Natura** code / exemption reason (N1–N7) for zero/exempt/reverse‑charge lines. Critical for reverse charge — add to AP schema. |

---

## 6. Monetary totals — `cac:LegalMonetaryTotal`

| # | Proposed Workday AP Schema field | UBL path | Sample value | Category |
|---|----------------------------------|----------|--------------|----------|
| 38 | `LineExtensionAmount` | `cbc:LineExtensionAmount` | `5000.00` | AP |
| 39 | `TaxExclusiveAmount` | `cbc:TaxExclusiveAmount` | `5000.00` | AP |
| 40 | `TaxInclusiveAmount` | `cbc:TaxInclusiveAmount` | `6100.00` | AP |
| 41 | `AllowanceTotalAmount` | `cbc:AllowanceTotalAmount` | `0` | AP |
| 42 | `ChargeTotalAmount` | `cbc:ChargeTotalAmount` | `0` | AP |
| 43 | `PayableAmount` | `cbc:PayableAmount` | `6100.00` | AP |

---

## 7. Invoice line — `cac:InvoiceLine`

| # | Proposed Workday AP Schema field | UBL path | Sample value | Category |
|---|----------------------------------|----------|--------------|----------|
| 44 | `LineID` | `cac:InvoiceLine/cbc:ID` | `1` | AP |
| 45 | `LineNote` | `cac:InvoiceLine/cbc:Note` | `Item1` | AP |
| 46 | `InvoicedQuantity` | `cbc:InvoicedQuantity` | `1.00000000` | AP |
| 47 | `UnitCode` | `cbc:InvoicedQuantity/@unitCode` | `EA` | AP |
| 48 | `LineExtensionAmount` | `cac:InvoiceLine/cbc:LineExtensionAmount` | `5000.00000000` | AP |
| 49 | `ItemDescription` | `cac:Item/cbc:Description` | `Item1` | AP |
| 50 | `ItemName` | `cac:Item/cbc:Name` | `Item1` | AP |
| 51 | `ItemClassificationCode` | `cac:CommodityClassification/cbc:ItemClassificationCode` | `Item1` | AP |
| 52 | `LineTaxCategoryCode` | `cac:ClassifiedTaxCategory/cbc:ID` | `S` | AP/NEW |
| 53 | `LineTaxPercent` | `cac:ClassifiedTaxCategory/cbc:Percent` | `22` | AP |
| 54 | `LineTaxSchemeID` | `cac:ClassifiedTaxCategory/cac:TaxScheme/cbc:ID` | `VAT` | Const/Derived |
| 55 | `PriceAmount` | `cac:Price/cbc:PriceAmount` | `5000.00000000` | AP |

---

## 8. Summary — fields to ADD to the Workday AP schema (Italy self‑billing specific)

These are the fields that most likely are **not** in a standard Workday AP extract and must be added to the AP schema in Connector Studio for the Italy self‑billing template:

| Field | UBL target | Why it is required for self‑billing |
|-------|-----------|--------------------------------------|
| `ItalyDocumentTypeCode` (TipoDocumento — TD16/TD17/TD18/TD19) | FatturaPA `TipoDocumento` extension `cbc:TypeCode` | Declares the reverse‑charge / self‑invoice scenario; drives template routing. |
| `SupplierTaxRegimeCode` (Regime Fiscale) | Supplier `PartyTaxScheme/cbc:TaxLevelCode` | Mandatory RegimeFiscale (RF01…) for the vendor. |
| `CustomerTaxRegimeCode` (Regime Fiscale) | Customer `PartyTaxScheme/cbc:TaxLevelCode` | Mandatory RegimeFiscale for the self‑billing entity. |
| `CustomerFiscalCode` (Codice Fiscale) | Customer `PartyLegalEntity/cbc:CompanyID` (`CF:` prefix) | Italian fiscal code, distinct from Partita IVA. |
| `CustomerEndpointID` + `CustomerEndpointSchemeID` (Codice Destinatario / SDI) | Customer `cbc:EndpointID` + `@schemeID` | SDI routing/recipient code required for delivery. |
| `TaxExemptionReason` / `Natura` code | `TaxScheme/cbc:TaxExemptionReason` | Nature/exemption code (N1–N7) needed for reverse‑charge tax treatment. |
| `SupplierCountryCode` (foreign) — verify | Supplier `Country/cbc:IdentificationCode` | Must accept non‑IT vendors to trigger self‑invoice logic. |
| `TaxCategoryCode` / `LineTaxCategoryCode` — verify Italy values | `TaxCategory/cbc:ID`, `ClassifiedTaxCategory/cbc:ID` | Ensure Italy category/nature values are supported. |

### Open items to confirm with the connector/tax team
1. **Source of `TipoDocumento`** in Workday — supplier‑invoice document type, a custom worktag, or a mapping table based on supplier country + tax rule.
2. **Party swap logic** — self‑billing swaps AP roles (your entity as customer, vendor as supplier); confirm which side each Workday attribute feeds.
3. **Self‑invoice numbering series** — whether a dedicated sequence is required for `cbc:ID`.
4. **Natura vs. Percent** — for pure reverse‑charge lines, whether VAT % is 0 with a Natura code, versus the sample here which self‑assesses 22%.
5. **Codice Fiscale format** — whether the `CF:` prefix is added by the connector or stored in the source field.
