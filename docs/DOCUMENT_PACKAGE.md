# Document Package

Document Package is a deterministic checklist of expected documents for a `SpecialSituation` or `ResearchCase`.

It helps Dani see what documents are expected, found, suggested, missing, or need manual check before deeper research. It does not verify documents legally, approve investments, or replace manual judgment.

## What It Does

For each case, SwissEdge chooses a document template based on the situation type and compares that template against available metadata:

- `SpecialSituation` fields
- `ResearchCase` fields
- evidence links
- SEC acquisition metadata
- filing URL
- accession number
- form type
- source links

The result is a practical documentation map.

## Where It Appears

Document Package panels appear on:

- SpecialSituation detail
- ResearchCase detail

Operational View may also show compact document readiness fields such as missing required counts and top missing documents.

## Document Statuses

### `found`

SwissEdge has stored metadata that appears to match this document.

Important: found does not mean legally verified.

### `suggested`

SwissEdge has a candidate link or metadata hint that may match this document.

Suggested links require manual review before they are treated as evidence.

### `missing`

No matching stored or suggested metadata is available.

Dani should search SEC, company IR, court sources, or other appropriate sources manually.

### `needs_manual_check`

The item normally requires manual review outside stored SEC metadata.

Examples include company IR pages, court filings, or transaction pages that are not reliably discoverable from SEC metadata alone.

### `not_applicable`

The document is not relevant for the specific case.

This should be used conservatively.

## Readiness Language

Document Package readiness is about documentation usefulness, not investment approval.

`ready_for_manual_evaluation` means the documentation package may be useful enough for Dani to manually evaluate the case. It does not mean the investment is approved.

## Expected Documents By Situation Type

### Merger Arbitrage / Acquisition Tender

Expected documents include:

- SC TO-T
- Offer to Purchase
- Letter of Transmittal
- Schedule 14D-9
- Merger Agreement
- Press Release
- Company IR page
- SEC filing detail page
- Key exhibits

Focus first on required SEC documents and the transaction agreement.

### Issuer Tender Offer

Expected documents include:

- SC TO-I
- Offer to Purchase
- Letter of Transmittal
- Issuer tender offer statement
- Press Release
- SEC filing detail page
- Key exhibits

Focus first on offer terms, timing, proration mechanics, and official issuer materials.

### Spin-Off

Expected documents include:

- Form 10
- Information Statement
- Parent company press release
- Investor presentation
- Pro forma financials
- Separation agreement
- Tax Matters Agreement
- Transition Services Agreement
- SEC filing detail page

Focus first on Form 10, pro forma financials, separation terms, and tax constraints.

### Liquidation / Bankruptcy / Dissolution

Expected documents include:

- 8-K liquidation or dissolution disclosure
- Plan of Liquidation
- Proxy statement if shareholder approval is needed
- Court filings if bankruptcy
- Press release
- Asset sale agreements if applicable
- Estimated distribution documents
- SEC filing detail page

Focus first on official liquidation plan, court or SEC disclosures, and distribution estimates.

## How Dani Should Use It

Use the panel as a work queue:

1. Review missing required documents first.
2. Open suggested links manually and decide whether they are relevant.
3. Treat found links as metadata until manually verified.
4. Use manual next actions to guide searches.
5. Promote or evaluate only after Dani is comfortable with the source trail.

## What Not To Infer

Do not infer that:

- found equals legally verified
- suggested equals evidence
- document readiness equals investment approval
- missing documents make a case bad
- complete documents make a case good

Document Package only improves operational clarity.

## Guardrails

- No document is automatically verified.
- No investment recommendation is generated.
- No ResearchCase is created automatically.
- Dani remains the final decision maker.
