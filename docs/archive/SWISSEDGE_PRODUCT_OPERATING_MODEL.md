Archived: superseded by docs/product/PRD.md and docs/governance/OPERATING_MODEL.md

# SwissEdge — Product Operating Model

> Version: 1.0 — 2026-05-14
> Audience: Product, engineering, and future Codex implementation sprints.
> Scope: Investment Research Desk only. Marketplace Assistant is preserved but paused.

---

## 1. General Application Proposal

SwissEdge is a private, modular AI research platform for structured special-situations investment research. It does **not** make investment recommendations. All output is educational research material produced by a human analyst supported by deterministic AI tools.

**Core value proposition:** Convert raw SEC EDGAR filing signals into structured, evidence-linked research briefs that can be reviewed, approved, and exported for educational publication — with a human in the loop at every non-trivial decision point.

**Core jobs:** detect special-situation signals, document the evidence trail, and evaluate/prepare an operational view for human review.

**Operating philosophy:**

- Detection is not evaluation. Evaluation is not recommendation. Publication requires manual approval.
- Every case moves forward only when a human explicitly promotes it.
- AI assists; it does not decide.
- The platform surfaces gaps, not conclusions.
- Dani makes the final investment decision outside the platform's automated workflow.

---

## 2. Rooms / Departments of the Application

The platform is organized into six functional rooms. Each room has a defined scope, a primary user surface, and a set of agents that support it.

| Room | Purpose | Primary Surface |
|---|---|---|
| **Detection Room** | Ingest and classify SEC EDGAR signals into `SpecialSituation` records | `/investment/situations` (Kanban) |
| **Research Room** | Deepen selected cases into structured `ResearchCase` briefs | `/investment/research/[id]` |
| **Evidence Room** | Link official sources, documents, and resource candidates to cases | Resource Scout, Evidence Links, Documentation Guide |
| **Historical Room** | Store and pattern-match against processed historical analogues | `/investment/historical-cases` |
| **Editorial Room** | Review, approve, and export research briefs for publication | `/investment/public-drafts/[id]` |
| **Agent Ops Room** | Monitor agent activity, review proposals, and audit platform health | `/agent-ops` |

### Room Boundaries

- A `SpecialSituation` lives in the Detection Room until manually promoted.
- A `ResearchCase` lives in the Research Room. It can reference Historical Room cases but does not inherit their status.
- A `PublicArticleDraft` lives in the Editorial Room. It is derived from a `ResearchCase` and has no write-back to research data.
- Agent Ops is read-mostly. Proposal review is the only mutation allowed from that room.

---

## 3. Agent Roles and Responsibilities

Agents are named observers and assistants. They do not execute autonomously. They produce proposals, reports, and diagnostics that a human reviews.

| Agent | Room | Role | Output Type |
|---|---|---|---|
| **SEC EDGAR Watcher** | Detection | Polls SEC EDGAR RSS/full-text search twice daily; classifies P1 signals | `SpecialSituation` detection records |
| **Methodology Analyst** | Detection → Research | Attaches checklist and required-resource templates to new detections | `methodology_workspace` snapshot on `SpecialSituation` |
| **Resource Scout** | Evidence | Identifies official SEC metadata candidates and generates manual search suggestions | `resource_candidates`, `search_suggestions` in workspace |
| **Missing Evidence Hunter** | Evidence | Surfaces documentation gaps across checklist, resources, and evidence links | Documentation Guide, Kanban badges |
| **Pattern Analyst** | Historical | Maps active cases to stored historical analogues by filing type and situation type | Historical analogues panel, Kanban labels |
| **Case Completion Coach** | Research | Scores case completeness and generates a blocking-items + improvement plan | Completion Workbench on case detail |
| **Intelligence Scorer** | Research | Produces a deterministic 0–100 IA Score across Detection, Structuring, and Risk Discipline | Intelligence Score card |
| **Source Intelligence Agent** | Research | Generates source enrichment proposals for `ResearchCase` and `HistoricalCase` | `SourceIntelligenceSuggestion` records (pending human approve/reject) |
| **Brief Generator** | Research | Drafts AI-assisted research brief sections on manual trigger | AI Brief Preview panel (apply is explicit) |
| **Quality Assist** | Research | Suggests `status` and `investment_readiness` values based on brief completeness | Quality Checklist panel (apply is explicit; `published` is hard-blocked) |
| **Document Analyst** | Research | Analyzes attached document metadata and returns enrichment suggestions | Document Analysis Preview (not saved automatically) |
| **Fontana** | Agent Ops | CTO-layer deterministic audit: surfaces bottlenecks, workload, and quality findings | Fontana Diagnostic Report (read-only) |
| **Editorial Reviewer** | Editorial | Validates draft for missing fields, buy/sell language, and disclaimer presence | Publishing Checklist, approval gate |

### Agent Constraints (all agents)

- No agent may autonomously write to `investment_sources`.
- No agent may trigger `/scan` or call the evaluator v2 globally.
- No agent may fetch document bodies, crawl URLs, or download PDFs without explicit scope approval.
- No agent output may contain buy/sell language, private notes, internal IDs, or VPS/infrastructure details.
- All AI-generated output is `saved_to_db: false` by default; a human must explicitly apply.

---

## 4. Detection States and Case Types

### SpecialSituation — Detection States

`SpecialSituation` is the initial detection object created by the SEC EDGAR Watcher. It is an automatically detected signal and triage object, not a durable deep research object.

| State | Meaning |
|---|---|
| `detected` | Signal found in EDGAR; no evaluation started |
| `under_review` | Analyst has opened the Kanban card and started checklist work |
| `evidence_gathering` | Resource Scout has identified candidates; evidence links being built |
| `ready_for_promotion` | Checklist and required resources sufficiently populated; manual promotion available |
| `promoted` | `research_case_id` stored; `ResearchCase` exists in Research Room |
| `closed` | Analyst dismissed; no ResearchCase created |

### ResearchCase — Research States

`ResearchCase` is created by manual promotion. It holds structured research in progress.

| State | Meaning |
|---|---|
| `under_investigation` | Active research in progress |
| `needs_more_work` | Analyst flagged as incomplete; blockers identified |
| `documented` | Brief substantially complete; evidence linked |
| `candidate` | Analyst marked as strong research candidate; eligible for editorial |
| `published` | Public draft approved and exported — **manual gate only** |
| `archived` | Closed; no publication |

> `investment_readiness` values on `ResearchCase`: `monitor`, `not_actionable`, `needs_more_work`, `candidate`. These are structural labels, not investment recommendations.
> Operational View uses `Candidate`, `Watchlist`, and `Reject` as human-review labels. `Watchlist` is a `ResearchCase` state/view label, not a separate entity. Candidate does not mean buy.

### PublicArticleDraft — Editorial States

| State | Meaning |
|---|---|
| `draft` | Initial creation from ResearchCase; not reviewed |
| `in_review` | Editorial review in progress |
| `approved` | Human approval gate passed; ready for manual export |
| `archived` | Closed without publication |

> Direct `draft → approved` is blocked. The flow is always `draft → in_review → approved`.

### HistoricalCase — Reconstruction States

| State | Meaning |
|---|---|
| `seed` | Initial record; notes only |
| `reconstructed` | Full reconstruction from processed materials |
| `lessons_extracted` | Key lessons and patterns extracted |
| `source_intel_applied` | Source intelligence suggestions reviewed and applied |

### P1 Signal Types (SEC EDGAR)

Only P1 signals create `SpecialSituation` records automatically:

| Filing Type | Situation Type |
|---|---|
| `SC TO-T` | Tender offer (third party) |
| `SC TO-I` | Tender offer (issuer self-tender) |
| `Form 10` | Spin-off / voluntary registration |
| `8-K` with liquidation/dissolution metadata | Liquidation or dissolution event |

---

## 5. State Transition Rules

All state transitions are **manual unless noted as automated**.

```
SEC EDGAR (cron, automated)
  └─ SpecialSituation [detected]
       └─ Analyst opens Kanban card → [under_review]
            └─ Evidence work begins → [evidence_gathering]
                 └─ Checklist + resources complete → [ready_for_promotion]
                      └─ Analyst triggers promote → ResearchCase [under_investigation]
                           └─ Research work → [needs_more_work | documented | candidate]
                                └─ [candidate] → PublicArticleDraft [draft]
                                     └─ [draft → in_review → approved]
                                          └─ Manual Markdown export for publication
```

### Promotion Gate (SpecialSituation → ResearchCase)

- Idempotent: one `ResearchCase` per `SpecialSituation`.
- Stores `research_case_id` in `evaluation.methodology_workspace`.
- Snapshots detection context and workspace into `ResearchCase.brief`.
- Creates conservative initial tasks and metadata-only sources.
- Does not evaluate, call AI, modify cron, or trigger the scanner.
- No automatic ResearchCase promotion exists unless explicitly approved in a future sprint.

### Editorial Gate (ResearchCase → PublicArticleDraft)

- Analyst must explicitly trigger draft creation.
- Draft creation is blocked if `ResearchCase` has no brief content.
- Approval is blocked if: title/body/disclaimer missing; buy/sell language detected.
- `published` status is hard-blocked from AI suggestion; it requires manual assignment only.

### Demotion / Bypass Rules

- A `ResearchCase` can move backward (e.g., `candidate → needs_more_work`) at any time.
- A `SpecialSituation` can be closed without promotion.
- A `PublicArticleDraft` can be archived from any state.
- No automated demotion exists.
- No automatic discard exists at the beginning of the funnel; early closure is a human decision.

---

## 6. Fontana (CTO) and Dani Weber (COO) — Executive Layer

The platform has a two-person executive layer. Their roles are distinct and non-overlapping in the product model.

### Fontana — CTO Layer (Deterministic Audit)

Fontana is the platform's internal CTO agent. It does not make business decisions. It surfaces engineering and operational findings.

**Scope:**

- Reads stored metadata across `SpecialSituation`, `ResearchCase`, `methodology_workspace`, Evidence Links, Documentation Guide, Intelligence Score, and Agent Ops activity.
- Produces a deterministic, read-only Fontana Diagnostic Report.
- Reports bottlenecks: rooms with stalled cases, agents with high error rates, missing documentation coverage.
- Focuses on technology, architecture, product coherence, technical debt, guardrails, and sprint recommendations.
- Does not write to any table. Does not trigger agents. Does not approve or reject anything.

**Fontana Report contents:**

| Section | What it surfaces |
|---|---|
| Preparation Quality | Checklist completion rate, missing required resources |
| Documentation Quality | Documentation Guide coverage across active cases |
| Evidence Coverage | Evidence Links per case, `evidence_found` vs total required |
| Workload Distribution | Cases per room, per phase, per agent |
| Bottlenecks | Cases stuck in a state for >N days (read from timestamps) |
| Manual Next Actions | Prioritized list of highest-impact human actions |

**Access:** Agent Ops → Fontana Diagnostic Report tab.

---

### Dani Weber — COO Layer (Human Approval Authority)

Dani is the sole human with approval authority over all non-reversible actions.

Dani Weber is the process governor. Dani focuses on funnel/process bottlenecks, promotion rate, documentation quality, noise reduction, and source/skill/process improvements.

| Decision | Approval Required? |
|---|---|
| Promote SpecialSituation → ResearchCase | Yes — manual trigger |
| Apply AI Brief suggestions | Yes — explicit apply per section |
| Approve Source Intelligence proposals | Yes — approve/reject per suggestion |
| Approve PublicArticleDraft | Yes — manual gate after `in_review` |
| Export Markdown for publication | Yes — manual copy after approval |
| Enable cron or change schedule | Yes — explicit instruction only |
| Trigger `/scan` | Yes — explicit instruction only |
| Enable evaluator v2 globally | Yes — explicit instruction only |
| Run database migrations | Yes — explicit instruction only |
| Deploy backend or frontend | Yes — explicit run of deploy script |
| Add new SEC signal type | Yes — explicit scope approval |

No agent, automation, or Codex sprint may bypass these gates.

Fontana and Dani Weber operate as a bidirectional executive feedback loop: Fontana surfaces product and technology findings; Dani accepts, rejects, or redirects process and improvement proposals.

---

## 7. Guardrails and Approval Model

### Hard Guardrails (never bypass)

These cannot be overridden by any sprint, prompt, or agent output:

- **No `/scan` without explicit instruction.** The scanner does not run on-demand.
- **No cron changes without explicit approval.** Current schedule: twice daily at 07:00 / 19:00 UTC.
- **No evaluator v2 global promotion.** v2 is manual-preview only; v1 is the production default.
- **No live AI during implementation.** AI calls belong at runtime, not in deploy scripts or migrations.
- **No database migrations without explicit approval.** Alembic runs only when Dani approves.
- **No deploy without explicit instruction.** Deploy scripts are not run speculatively.
- **No URL fetching, crawling, or PDF download** without explicit scope approval per case.
- **No investment recommendations.** All output is educational research material.
- **No buy/sell language** in any platform output, brief, draft, or agent message.
- **No secrets, IPs, VPS details, Tailscale addresses, or `.env` values** in any file.
- **No raw course transcripts, audio, video, or `course_index/` content** in any file.
- **No Marketplace/Sales changes.** Domain is paused and preserved; no modifications until explicitly scoped.
- **No public posting.** No Substack API. Manual Markdown export only.
- **No automatic ResearchCase creation.** Promotion is always a manual trigger.
- **No automatic publishing.** Draft approval and Markdown export are manual gates.
- **No improvement proposal execution without Dani approval.**

### Soft Guardrails (require judgment)

- Source Intelligence suggestions are proposals. They do not write to `investment_sources` until Phase 4D is explicitly approved.
- `evidence_found` on a resource candidate means "linked," not "verified." evidence_found does not mean verified.
- Intelligence Score `APPROVABLE` means structurally ready for manual review, not investment-approved.
- Historical analogues are pattern references, not predictions.
- Quality Assist `suggested_status` is assistive only; the analyst decides.

### Approval Tiers

| Tier | Who approves | Examples |
|---|---|---|
| **Instant** | Platform (automated) | SEC EDGAR cron detection, deduplication |
| **Manual trigger** | Dani | Case promotion, brief preview trigger, draft creation |
| **Explicit apply** | Dani | Brief section apply, source proposal approve/reject, quality assist apply |
| **Editorial gate** | Dani | Draft in-review → approved, Markdown export |
| **Explicit instruction** | Dani | Cron change, scanner trigger, v2 evaluator, migration, deploy |

---

## 8. Product Simplicity Principles

These principles govern all future Codex implementation sprints.

### 8.1 One Human Gate Per Major Transition

Each major state transition has exactly one human gate. No transition is skipped, automated, or implied. If a sprint proposal would remove a gate, it requires explicit approval from Dani before implementation.

### 8.2 AI Assists, Humans Decide

AI output is always framed as a proposal or preview:
- `saved_to_db: false` is the default for all AI-generated content.
- Apply is always a separate, explicit user action.
- AI cannot change status, readiness, or evidence links without a human confirm.

### 8.3 Deterministic Before AI

Where a result can be derived deterministically from stored metadata, it must be. AI is reserved for content generation (briefs, analysis previews, source proposals). Scores, guides, timelines, and reports are deterministic.

### 8.4 Read-Only by Default

New endpoints default to read-only. Write capability is added only when a specific user action requires it, scoped to the minimum necessary fields.

### 8.5 No Speculative Features

Each sprint implements exactly what is specified. No flexibility layers, configuration flags, or extensibility patterns for hypothetical future use. Three similar lines of code are better than a premature abstraction.

### 8.6 Touch Only What the Sprint Requires

Sprints do not improve adjacent code, refactor unrelated areas, or clean up pre-existing issues. Every changed line traces directly to the sprint scope. Pre-existing dead code is noted, not deleted.

### 8.7 Minimal Surface Exposure

No endpoint exposes:
- Private research notes
- Internal database IDs in public-facing drafts
- VPS or infrastructure metadata
- Raw course material or methodology excerpts

### 8.8 Failure Isolation

Secondary panels (Evidence Links, Documentation Guide, Activity Timeline) load independently. A failure in one panel must not block the rest of the page. Agent Ops logger failures must not affect caller transactions (SAVEPOINTs isolate them).

### 8.9 Labels Are Not Recommendations

All status and readiness labels (`candidate`, `watchlist`, `reject`, `APPROVABLE`, `evidence_found`, `intelligence_score`) describe structural state only. None imply an investment action. Platform output is always educational.

### 8.10 No Useless Surfaces

Product simplicity rejects decorative agents, duplicate dashboards, and screens that do not support detection, documentation, review, approval, or governance.

### 8.11 Scope Matches Request

When the user asks for a review, deliver a review. When the user asks for an implementation, implement exactly the stated scope. Do not conflate the two roles. Do not expand scope without explicit instruction.

---

## Appendix: Key Data Objects

| Object | Table | Created By | Promoted By |
|---|---|---|---|
| `SpecialSituation` | `special_situations` | SEC EDGAR Watcher (cron) | Manual |
| `ResearchCase` | `research_cases` | Manual promotion | Manual editorial trigger |
| `PublicArticleDraft` | `public_article_drafts` | Manual from ResearchCase | Manual approval gate |
| `HistoricalCase` | `historical_cases` | Manual creation | Manual reconstruction |
| `SourceIntelligenceSuggestion` | `source_intelligence_suggestions` | Source Intelligence Agent (manual trigger) | Manual approve/reject |
| `ResearchDocument` | `research_documents` | Manual or SEC acquisition (manual trigger) | — |
| `ResearchSource` | `research_sources` | Manual or SEC acquisition (manual trigger) | — |
| `AgentActivity` | `agent_activity` | Fail-safe logger (observer events only) | — |
| `AgentProfile` | `agent_profiles` | Sprint H seed | — |

---

*This document is a product operating model. It describes what the platform does and how it governs itself. It does not contain secrets, infrastructure details, raw course materials, credentials, or financial recommendations.*
