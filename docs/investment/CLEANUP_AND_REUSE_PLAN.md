# SwissEdge Investment V2 Cleanup and Reuse Plan

Date: 2026-05-09

Scope: planning only. No code, migration, deploy, scan, cron, live AI, Marketplace/Sales, or public-site work is included.

## Summary Estimates

Estimated implementation mix for Investment Platform V2:

- Direct reuse: 45%
- Reuse with refactor: 35%
- Deprecate/delete later: 5%
- New code required: 15%

Interpretation:

- The ResearchCase workspace is a strong base.
- The source registry exists but must become operational rather than decorative.
- The scanner/evaluations path should be preserved during migration, then gradually demoted behind Research Inbox.
- Most new work is glue: intake events, inbox metadata, SEC registry wiring, duplicate handling, and audit surfaces.

## Backend

| Item | Current role | Classification | Reason | Risk | Recommended action | Priority |
|---|---|---|---|---|---|---|
| ResearchCase model/service/routes | Durable private research workspace. | KEEP_AND_REFACTOR | Core V2 object already exists, but needs intake/source/methodology metadata. | Breaking existing workspace if status changes are rushed. | Add fields only after migration spec; keep current endpoints. | High |
| `ResearchTask` | Manual verification and follow-up checklist. | KEEP | Maps naturally to official-source verification and enrichment. | Task vocabulary may stay too loose. | Reuse immediately; add task categories later. | High |
| `ResearchDocument` | Document metadata and snippet storage. | KEEP_AND_REFACTOR | Useful for official-source evidence; currently URL metadata only. | UI may imply URLs are fetched. | Keep metadata-only rule; later add official/source/evidence flags. | High |
| `ResearchSource` | Case-level source reference and signal quality. | KEEP_AND_REFACTOR | Already links to `investment_sources`; useful for source attribution. | Not consistently populated by intake. | Make intake create `ResearchSource` rows for origin. | High |
| `investment_sources` model/routes/config | Source registry and toggles. | KEEP_AND_REFACTOR | Must become operational source registry. | Current UI claims can mislead because scanner ignores it. | Extend V2 fields and wire SEC first. | High |
| SEC EDGAR source adapter | SEC full-text search adapter. | KEEP_AND_REFACTOR | First priority connector; already rate-limited and functional. | Coverage and parsing are narrow; no per-form diagnostics. | Add diagnostics, source-row input, broader form review later. | High |
| Scan endpoint and scanner loop | Current scan -> SpecialSituation path. | KEEP_AND_REFACTOR | Useful compatibility path, but wrong target object for V2. | Direct changes could break cron/manual scan. | Preserve initially; create source-driven SEC intake alongside or behind feature flag. | High |
| `SpecialSituation` model/routes | Current evaluation queue object. | DEPRECATE | V2 should center ResearchCase. | Removing early would break evaluations and existing links. | Keep as compatibility layer; stop making it primary after inbox exists. | Medium |
| Evaluator v1 | Production default evaluator. | KEEP_AND_REFACTOR | Stable path, but less structured than V2 needs. | Changing default violates guardrails. | Keep default; build initial evaluation contract separately. | Medium |
| Evaluator v2 | Manual preview and structured routing/evaluation. | KEEP_AND_REFACTOR | Strong schema base for initial evaluation. | Live AI and global enablement risks. | Use only in controlled shadow/preview until approved. | High |
| Routing engine | Deterministic form/situation/playbook routing. | KEEP | Fits source-driven intake and methodology status. | Current scanner does not use all recognized forms. | Reuse in SEC intake and duplicate classification. | High |
| `playbook_loader` | Loads processed course methodology artifacts. | KEEP | Required for methodology grounding. | Missing local/VPS artifacts cause empty methodology. | Add readiness checks and auditor coverage. | High |
| Source intelligence | Source scoring and suggestions approval queue. | KEEP_AND_REFACTOR | Valuable feedback loop; not initial intake engine. | Suggestions do not apply to registry yet. | Keep as later feedback; do not wire apply until approved. | Medium |
| Historical cases | Manual historical learning workspace. | KEEP | Supports source intelligence and methodology learning. | Could distract from SEC intake. | Preserve; connect later to source feedback loop. | Low |
| Publishing/public drafts | Private editorial review workflow. | KEEP | Useful after documented cases. | Public track is paused; avoid making it primary. | Keep untouched; no Substack/public work. | Low |
| Observability/run_logger | Agent run, AI usage, diagnostics foundation. | KEEP_AND_REFACTOR | Needed for intake funnel and auditor. | Current scanner metrics are too coarse. | Add structured funnel metrics in next implementation sprint. | High |
| Telegram/OpenClaw pieces | Operational/manual control layer. | KEEP_AND_REFACTOR | Future manual intake could use Telegram. | OpenClaw should not own business logic. | Keep as caller/operator only; V2 logic stays in FastAPI. | Low |
| Agent registry descriptions | Static observability descriptions. | KEEP_AND_REFACTOR | Useful UI metadata. | Some claims currently exceed backend reality. | Align text with actual behavior after V2 design decisions. | Medium |

## Frontend

| Item | Current role | Classification | Reason | Risk | Recommended action | Priority |
|---|---|---|---|---|---|---|
| `/investment/research` | ResearchCase list and manual create-from-evaluation. | KEEP_AND_REFACTOR | Becomes base for Research Inbox. | Current list lacks intake/source buckets. | Add `/investment/research-inbox` first; then merge or redirect later. | High |
| `/investment/research/[id]` | Full ResearchCase workspace. | KEEP | Strong existing detail surface for tasks, docs, sources, brief, quality, source intelligence. | Large file and many responsibilities. | Reuse; later extract panels and add intake metadata. | High |
| `/investment/sources` | Source registry UI and toggles. | KEEP_AND_REFACTOR | Must become operational source control surface. | Current "scanner reads these" wording is misleading. | Add V2 fields and warnings; avoid implying active toggles drive scanner until true. | High |
| `/investment/evaluations` | Current SpecialSituation queue. | DEPRECATE | V2 inbox should become main queue. | Existing users still need access during migration. | Keep as legacy/evaluations view; link to Research Inbox. | Medium |
| `/investment/radar-status` | Read-only scanner and cron observability. | KEEP_AND_REFACTOR | Good operational page. | It lacks funnel metrics and source-registry caveat. | Add scanner funnel diagnostics after backend supports them. | High |
| `/investment/public-drafts` | Private editorial queue. | KEEP | Publishing track paused but workflow remains valid. | Can distract from V2 intake. | Preserve; do not promote in navigation during V2. | Low |
| Future `/investment/research-inbox` | Main V2 queue. | NEW | Needed to separate preliminary ResearchCases from legacy evaluations. | Could duplicate `/research` if not scoped. | Build as read-only aggregate first. | High |

## Docs

| Item | Current role | Classification | Reason | Risk | Recommended action | Priority |
|---|---|---|---|---|---|---|
| `docs/PROJECT_STATE_LIGHT.md` | Compact handoff. | KEEP_AND_REFACTOR | Needs active-track update. | Stale active phase sends work to public site. | Minimal update to Investment Platform V2. | High |
| `docs/PROJECT_STATE.md` | Full canonical history. | KEEP | Useful history, but not needed for this sprint. | Large edits risk churn. | Update only after implementation sprint, not this planning sprint unless requested. | Medium |
| Workflow docs | Role and sprint rules. | KEEP | Current workflow matches architect/engineer/reviewer split. | None. | Keep. | High |
| Previous redesign docs | Prior research-platform design. | KEEP | Still useful as historical architecture base. | May conflict with source-driven intake if treated as current. | Reference as Phase 1-5 foundation. | Medium |
| Phase/source docs | Phase 3/3E source intelligence docs. | KEEP | Useful for source intelligence continuation. | Not same as source-driven intake. | Keep; distinguish feedback loop from intake engine. | Medium |
| `RADAR_RELIABILITY_AUDIT.md` | Current scanner reliability diagnosis. | KEEP | Directly motivates V2. | None. | Use as input to Sprint A diagnostics. | High |
| Public-site docs | Paused public brand/editorial work. | DEPRECATE | Not active track. | Could pull focus back to public website. | Mark as paused in state/backlog; keep files. | Low |
| Sales/Marketplace docs | Separate paused domain. | KEEP | Preserve history but out of scope. | Accidental changes. | Do not touch in V2 sprint. | Low |

## KEEP

- ResearchCase core workspace.
- Tasks, documents, sources, notes, disclaimers.
- Processed course methodology artifacts.
- Routing engine and playbook loader.
- SEC EDGAR adapter as first connector.
- Observability foundation.
- PublicArticleDraft workflow as later-stage private editorial output.
- HistoricalCase workspace as later feedback input.

## KEEP_AND_REFACTOR

- `investment_sources`: extend into operational source registry.
- Scanner: refactor from hardcoded adapter to source-driven intake.
- Evaluator: preserve v1 default, reuse v2 schema concepts for initial evaluation.
- Sources UI: revise misleading text and add V2 fields.
- Radar Status: add source-driven funnel diagnostics.
- Research list: evolve into Research Inbox or add a new inbox route.
- Agent registry: align claims with implemented behavior.

## DEPRECATE

- Evaluations queue as primary work queue.
- `SpecialSituation` as the primary durable opportunity object.
- Public-site track as current "next sprint".

## DELETE_LATER

Nothing should be deleted now.

Possible later deletion candidates only after migration and validation:

- Duplicate UI labels that imply source registry controls scanner before it does.
- Dead placeholder source references once V2 source registry can represent them.
- Legacy SpecialSituation-only UI paths if all active workflows move to ResearchCase.

## First Refactor Order

1. Documentation/state alignment.
2. Read-only scanner/source diagnostics.
3. Research Inbox read-only view over existing ResearchCases.
4. Add V2 metadata fields through approved migration.
5. SEC EDGAR source-driven ResearchCase intake.
6. Duplicate handling.
7. Initial course-grounded evaluation attachment.
8. External source manual intake.
9. Auditor read-only report.
