# SwissEdge Investment Platform — Deployment Notes

---

## Sprint C V2 metadata deployment note

Sprint C introduced Alembic revision `d4e5f6a7b8c9` (`add_researchcase_v2_metadata`), which adds 14 nullable V2 metadata columns to the `research_cases` table.

This migration file was not present in the backend deploy script allowlist when Sprint C was first deployed, so it had to be copied to the VPS manually before running Alembic.

**Correct deployment order for Sprint C (and for any sprint that includes an Alembic migration):**

1. Copy all backend files including the migration file to the VPS (using `scripts/deploy_backend_files.ps1`).
2. Run Alembic on the VPS: `python -m alembic upgrade d4e5f6a7b8c9`
3. Restart the backend service.
4. Deploy frontend files (using `scripts/deploy_frontend.ps1`).

**The deploy script now includes this migration file** (`backend/db/migrations/versions/d4e5f6a7b8c9_add_researchcase_v2_metadata.py`) in the explicit allowlist so it will be included in all future backend deployments automatically.

**Do not run Alembic migrations automatically from the deploy script.** Migrations must be approved and run explicitly by Dani. The deploy script copies migration files to the VPS; the `alembic upgrade` command is always a separate manual step.

---

## General migration deployment pattern

For all future sprints that include an Alembic migration:

1. Add the migration file to the `$backendFiles` allowlist in `scripts/deploy_backend_files.ps1`.
2. Add the migration file to the `for file in ...` backup loop in the same script.
3. After the backend deploy script runs, manually run `python -m alembic upgrade <revision>` on the VPS.
4. Restart the backend service.
5. Deploy the frontend.

Never run `alembic upgrade head` automatically or without reviewing the migration chain first.

---

## Sprint H Agent Ops deployment note

Sprint H introduced Alembic revision `e5f6a7b8c9d0` (`add_agent_ops_tables`), which creates six additive Agent Ops tables: `agent_rooms`, `agent_profiles`, `agent_activities`, `agent_results`, `agent_diagnostic_events`, `agent_learning_proposals`. `agent_score_snapshot` is deferred.

The migration file and all Agent Ops backend modules must be present on the VPS before Alembic is run.

Historical note: before Sprint H deployment, release was blocked until Sprint H.1 confirmed that `scripts/deploy_backend_files.ps1` included the Agent Ops migration and modules in both the backend file allowlist and backup loop. Later 2026-05-10 closeout docs record Sprint H as deployed and Alembic revision `e5f6a7b8c9d0` as applied.

**Correct manual deployment order for Sprint H:**

1. Deploy backend files including the migration and Agent Ops modules.
2. Run Alembic on the VPS: `python -m alembic upgrade e5f6a7b8c9d0`
3. Restart the backend service.
4. Smoke test Agent Ops endpoints: `GET /api/agent-ops/rooms`, `GET /api/agent-ops/agents`, `GET /api/agent-ops/activity`, `GET /api/agent-ops/proposals`.

Do not run migrations automatically from the deploy script. Migration steps are always separate manual operations approved by Dani.

Do not connect Agent Ops to scanner or evaluator without a separately approved sprint. Sprint K introduced logger isolation with nested transactions/SAVEPOINTs, but scanner/evaluator integration is still not approved. No scanner/evaluator/cron behavior changed in Sprint H.

---

## Sprint H/I Agent Ops deploy closeout note

Sprint H backend deployment succeeded after the Agent Ops migration was applied manually with Alembic revision `e5f6a7b8c9d0`.

Sprint I frontend deployment requires a valid Next production build with `.next/BUILD_ID`. If the frontend fails with `Could not find a production build`, run `npm run build` in `frontend` and verify `.next/BUILD_ID` exists before starting the production server.

Browser DevTools may show a CSP `unsafe-eval` warning while `/agent-ops` still works. Do not relax CSP or add `unsafe-eval` for this warning unless real functionality is broken.

---

## Agent Ops verification notes

After backend deployment, verify only read-only Agent Ops endpoints:

1. `GET /api/health/ping`
2. `GET /api/agent-ops/rooms`
3. `GET /api/agent-ops/agents`
4. `GET /api/agent-ops/activity`
5. `GET /api/agent-ops/diagnostics`
6. `GET /api/agent-ops/proposals`

Expected state: health OK, rooms count 6, agents count 6. Activity may contain narrow observer events from proposal review and manual ResearchCase creation if Sprint N/O are deployed; diagnostics/proposals may still be empty unless manually created.

After frontend deployment, verify `/agent-ops` loads and shows Rooms, Agents, Activity Feed, Diagnostics, Learning Proposals, Scoreboard placeholder, Fontana Reports placeholder, the guardrail banner, Refresh button, and Last refreshed timestamp.

If frontend startup fails with `Could not find a production build`, run `npm run build` in `frontend` and verify `.next/BUILD_ID` exists before starting the production server.

Browser DevTools may show a CSP `unsafe-eval` warning while the page works. Do not fix that by weakening CSP or adding `unsafe-eval`; investigate only if real functionality is broken.

---

## Sprint P manual runtime verification checklist

Do not call production endpoints unless Dani explicitly provides the environment and asks for verification.

Read-only checks for Dani:

1. `GET /api/health/ping`
2. `GET /api/agent-ops/rooms`
3. `GET /api/agent-ops/agents`
4. `GET /api/agent-ops/activity`
5. `GET /api/agent-ops/diagnostics`
6. `GET /api/agent-ops/proposals`

Mutation checks only with explicit Dani approval:

1. Create/review one Agent Ops proposal to verify Sprint N proposal-review observer logging.
2. Create a ResearchCase from an existing Evaluation/SpecialSituation to verify Sprint O ResearchCase bridge observer logging.

Do not call `/api/investment/scan`.

---

## Sprint Q SEC EDGAR Detection Core deployment note

Sprint Q adds a manual SEC EDGAR detection core:

- `backend/services/investment/sec_detection.py`
- `backend/cli/sec_edgar_detect.py`
- conservative SEC adapter throttle/backoff updates

No Alembic migration is required. Before manual deployment, ensure the backend file deployment step includes `backend/services/investment/sec_detection.py`, `backend/cli/__init__.py`, `backend/cli/sec_edgar_detect.py`, and the updated SEC adapter.

Manual run pattern after Claude GO and Dani-approved deploy:

1. Optional dry run: `python -m backend.cli.sec_edgar_detect --hours-back 36 --dry-run`
2. Manual write run: `python -m backend.cli.sec_edgar_detect --hours-back 36`

Sprint Q does not schedule execution. Do not modify cron in this deployment. Do not call `/api/investment/scan` for Sprint Q verification. The manual script does not call live AI, does not enable evaluator v2, does not create ResearchCases, does not create public drafts, and does not touch Marketplace/Sales.

Sprint Q 8-K liquidation/dissolution detection is metadata-dependent. It uses SEC search result metadata fields, not full document body fetching. Therefore recall for liquidation 8-Ks may be incomplete. This is intentional for Sprint Q to avoid extra document downloads and keep SEC requests conservative. A future sprint may add controlled document-body retrieval only if needed and rate-limited.

Expected run summary fields:

- run started/completed timestamp
- lookback window
- filings fetched/inspected
- candidates detected
- duplicates skipped
- unsupported forms skipped
- `SpecialSituation` records created/updated
- errors
- rate-limit/backoff events

---

## Sprint R SEC EDGAR scheduled intake deployment note

Sprint R prepares scheduled SEC EDGAR detection using a cron-friendly wrapper script:

- `scripts/run_sec_edgar_detection.sh`

No cron entry is installed automatically by the deploy script. Dani must enable scheduling manually after Claude GO.

The wrapper runs:

```bash
python -m backend.cli.sec_edgar_detect --hours-back 168
```

It changes directory to `/opt/swissedge`, activates `.venv`, loads `/opt/swissedge/.env` without printing values, and uses a lock to prevent overlapping runs.

Manual post-deploy setup:

```bash
cd /opt/swissedge
sudo chmod +x scripts/run_sec_edgar_detection.sh
sudo mkdir -p logs
```

Cron template:

```cron
0 7,19 * * * /opt/swissedge/scripts/run_sec_edgar_detection.sh >> /opt/swissedge/logs/sec_edgar_detection.log 2>&1
```

Log inspection:

```bash
tail -n 120 /opt/swissedge/logs/sec_edgar_detection.log
```

Sprint R keeps the Sprint Q boundaries: no `/api/investment/scan`, no live AI, no evaluator v2 global enablement, no ResearchCase auto-creation, no public publishing, no external sources, and no document body fetching. The SEC adapter rate limit remains one request every five seconds, and dedupe prevents repeated `SpecialSituation` creation.

---

## Sprint S SpecialSituation methodology workspace deployment note

Sprint S adds methodology checklist/resource snapshots to SEC-detected `SpecialSituation` records using the existing `evaluation` JSONB field. No Alembic migration is required.

New backend files:

- `backend/services/investment/methodology_workspace.py`
- `backend/cli/special_situation_attach_methodology.py`

New frontend route:

- `/investment/situations/[id]`

After backend deployment, new SEC detections automatically include `evaluation.methodology_workspace`.

Manual backfill for existing SEC detections:

```bash
python -m backend.cli.special_situation_attach_methodology --dry-run
python -m backend.cli.special_situation_attach_methodology --apply
```

Backfill only targets detected SEC EDGAR records with `evaluation.detected_only=true`, existing `evaluation.sec_detection`, and no existing methodology workspace.

Sprint S does not call live AI, does not crawl the web, does not download PDFs, does not fetch SEC document bodies, does not mark checklist items verified, does not create ResearchCases automatically, does not publish, does not modify cron, and does not call `/api/investment/scan`.

---

## Sprint T Resource Scout v1 deployment note

Sprint T adds manual Resource Scout v1 for `SpecialSituation` methodology workspaces. No Alembic migration is required.

New backend files:

- `backend/services/investment/resource_scout.py`
- `backend/cli/resource_scout_special_situation.py`

New endpoint:

```text
POST /api/investment/situations/{id}/resources
```

Manual CLI:

```bash
python -m backend.cli.resource_scout_special_situation --situation-id <id> --dry-run
python -m backend.cli.resource_scout_special_situation --situation-id <id> --apply
python -m backend.cli.resource_scout_special_situation --limit 5 --dry-run
python -m backend.cli.resource_scout_special_situation --limit 5 --apply
```

Resource Scout v1 stores resource candidates and search suggestions in `evaluation.methodology_workspace`. It does not run on cron, does not crawl the web, does not download PDFs, does not fetch SEC document bodies, does not store full article text, does not verify evidence, and does not evaluate or create ResearchCases.

Frontend deploy is required for the updated `/investment/situations/[id]` evidence workspace UI.

---

## Sprint U Kanban Actions + Evidence Mapping deployment note

Sprint U adds manual action support for `SpecialSituation` methodology workspaces. No Alembic migration is required because workflow, resource review, and evidence mapping state are stored in `SpecialSituation.evaluation.methodology_workspace`.

Changed endpoints:

```text
PATCH /api/investment/situations/{id}/workflow-status
POST /api/investment/situations/{id}/resources
PATCH /api/investment/situations/{id}/resources/{resource_candidate_id}
```

Manual verification after backend/frontend deploy:

1. Open `/investment/situations`.
2. Move one SEC-detected situation to `needs_resources`.
3. Open `/investment/situations/{id}`.
4. Add a manual HTTP/HTTPS resource candidate.
5. Link it to one required resource and one checklist item.
6. Mark it `evidence_found`.
7. Confirm the linked required resource and checklist item move to `evidence_found`, not `verified`.
8. Reject a separate candidate and confirm it remains visible.

Sprint U does not modify cron, does not call `/api/investment/scan`, does not call live AI, does not enable evaluator v2 globally, does not create ResearchCases automatically, does not crawl the web, does not download PDFs, does not fetch document/article bodies, and does not publish.

---

## Sprint V SpecialSituation promotion deployment note

Sprint V adds manual promotion from `SpecialSituation` to `ResearchCase`. No Alembic migration is required.

Changed endpoint:

```text
POST /api/investment/situations/{id}/promote-to-research-case
```

Promotion is idempotent. It first checks `evaluation.methodology_workspace.research_case_id`, then existing `ResearchCase.situation_id`. If a ResearchCase already exists, the endpoint returns it instead of creating a duplicate.

Manual verification after backend/frontend deploy:

1. Open `/investment/situations/{id}` for a situation with methodology workspace.
2. Click `Promote to ResearchCase`.
3. Confirm the warning.
4. Open the returned ResearchCase link.
5. Confirm the ResearchCase has `status=under_investigation`, `investment_readiness=needs_more_work`, safe detection/workspace snapshot context, and initial verification tasks.
6. Reload the situation detail and confirm duplicate promotion is disabled or returns the existing ResearchCase.

Sprint V does not modify cron, does not call `/api/investment/scan`, does not call live AI, does not enable evaluator v2 globally, does not auto-create ResearchCases from detection, does not create public drafts, does not publish, does not crawl the web, does not download PDFs, and does not fetch document/article bodies.
