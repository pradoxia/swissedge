# Handoff to ChatGPT (Product Architect) — 2026-06-10

From: Claude (verification engineer / Cowork session), approved and directed by Dani.
Purpose: inform ChatGPT of implemented changes, exercised guardrail approvals, and
decisions needed. Source-of-truth docs affected are listed per item.

## 1. What was implemented (Dani explicitly approved each scope)

### 1.1 Detection Quick Wins (backend, scanner behavior change — Dani-approved)

Files: `backend/services/investment/sources/sec_edgar.py`, `routing_engine.py`,
`sec_detection.py`, new `sec_company_facts.py`, new tests
`backend/tests/test_detection_quick_wins.py` (76/76 detection-related tests pass).

- 8-K item-code parsing from EFTS (`Items:` in summary): Item 1.03 → bankruptcy
  (HIGH), 3.01 → delisting (MEDIUM), 5.01 → merger/change_of_control (MEDIUM).
  Item codes take precedence over keyword matching.
- Candidate-only persistence: classified filings with HIGH/MEDIUM confidence on
  report forms (DEFM14A, PREM14A, S-4, SC 14D9, 13E-3, Form 25) now create
  `SpecialSituation` records flagged `creation_context.candidate_only=true`
  with `creation_reason`, instead of dying as summary rows. Strict allowlist
  creation behavior is unchanged. Dedupe applies to both paths.
- New forms queried: `SC 13E3` (going-private) and `25-NSE` (Form 25 delisting).
  New situation type `delisting` (detection_only scope, no playbook).
- EFTS query fix: removed spurious `keys` param (form name was sent as a
  full-text term); `q` is now used only for explicit full-text sweeps.
- Full-text sweeps per scan: "odd lot" (all forms), "plan of liquidation" (8-K),
  "dutch auction" (all forms); results join the same parse/lookback/dedupe
  pipeline; new subtype `odd_lot_provision` via keyword.
- Market context enrichment (best-effort, official source only): SEC XBRL
  `dei:EntityPublicFloat` per created situation (max 10 lookups/run, throttled),
  plus an explainable `competition_lens.small_company_flag` (< $300M float).
  Explicitly labeled "prioritization context only, not investment advice".
- Amendment dedupe (`SC TO-T/A` ↔ `SC TO-T`) and a silent-breakage warning when
  a scan returns 0 raw hits across all forms.

Not changed: cron schedule, `/scan` triggers, promotion, publishing, live AI,
evaluator status, buy/sell guardrails, human approval gates.

### 1.2 PRD updated to v0.3.1

`docs/product/PRD.md` §17.1 "Curated Human Source Registry": 9 curated human
sources (SSI, InsideArbitrage, Odd Lot Special Situations, YAVB, Clark Street
Value, Alluvial, PETITION, VIC, Stock Spinoff Investing) with tiers and intake
guardrails (manual-only in MVP, no scraping without approved sprint + TOS review,
source attribution required, per-source CANDIDATE-yield measurement).

### 1.3 UI consolidation phase 1 (frontend only)

- Mission Control (`frontend/app/page.tsx`): removed Campus hero (claimed
  "live logs / real time" — not operational truth per PRD §18), removed the
  hardcoded system-status strip (stale "Cron V2 Disabled"-style claims) in favor
  of a link to Radar Status, promoted Research Inbox to CORE in primary
  operations, demoted Intelligence KPIs to supporting, moved Campus to Paused.
- Watchlist (`/investment/watchlist`): retargeted from legacy Evaluations flow to
  current flow (rows link to `/investment/situations/{id}`, header points to
  Research Inbox, labeled as legacy surface).

## 2. Verification status

- Backend: 76/76 tests pass (incl. 20 new). One legacy assertion updated in
  `test_sec_edgar_429.py` (asserted the removed `keys` param; now asserts `forms`).
- Frontend: changes reviewed; Dani must run `npm run build` locally before deploy
  (Claude's sandbox had unreliable file views for recently changed files; phantom
  errors observed in files Claude did not touch: `lib/api.ts`,
  `SecDocumentAcquisitionPanel.tsx` — likely Codex's local M1 work; please verify).
- Deploy: `backend/services/investment/sec_company_facts.py` is NEW and must be
  added to the `scripts/deploy_backend_files.ps1` allowlist.

## 3. Decisions requested from ChatGPT

1. **PRD/MVP_SCOPE sync for quick wins**: candidate-only creation, new forms,
   `delisting` situation type, sweeps, and market context enrichment should be
   reflected in PRD §8/§9 and MVP_SCOPE "Scheduled Detection Boundary" (the
   boundary currently says "metadata-only SpecialSituation triage candidates" —
   still true, but the candidate set is broader now). Draft changelog entries.
2. **UI consolidation phase 2 needs a PRD §11.2 amendment**: proposal is to slim
   `/agent-ops` to health + runs + proposals and move Executive Office/rooms/XP
   surfaces out of MVP requirements (consistent with PRD v0.3.0 making governance
   "supporting only"). Today §11.2 still mandates all panels. Please spec.
3. **Route consolidation sprint**: fold `/investment/watchlist` into Research
   Inbox as a filter (data-model note: inbox lists ResearchCases, watchlist lists
   Situations — needs a unified queue definition); retire `/investment/evaluations`
   (legacy v1) and `/agents` (duplicate of Agent Ops registry); decide Campus fate.
4. **Price connector decision (MVP v3 Sprint M5)**: choose provider for daily
   closes (Stooq vs yfinance vs other; TOS review), confirm `PriceSnapshot`
   entity and spread/ADV fields per `docs/product/MVP_V3_PROPOSAL.md`.
5. **Study Guide mapping**: new situation types (`delisting`,
   `bankruptcy_or_receivership`, `change_of_control`, `odd_lot_provision`) have no
   course chapter mapping and will correctly show "No chapter reference mapped
   yet". Decide whether Playbook Scribe mapping work should cover them.
6. **Noise watch**: candidate-only creation will increase Kanban volume
   (bounded by 20/form/run + dedupe). If noisy in the first cron week, options:
   per-form caps, confidence floor HIGH-only, or a separate inbox lane for
   `candidate_only=true`.

## 4. Related documents

- `docs/product/MVP_V3_PROPOSAL.md` (v0.2.0) — full plan and rationale.
- `docs/product/PRD.md` (v0.3.1), `docs/product/MVP_SCOPE.md`, `docs/product/ROADMAP.md`.
- `docs/governance/GUARDRAILS.md` — no guardrail was weakened; scanner-behavior
  change was explicitly Dani-approved in session.
