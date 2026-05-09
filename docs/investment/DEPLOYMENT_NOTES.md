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

**Correct manual deployment order for Sprint H:**

1. Deploy backend files using `scripts/deploy_backend_files.ps1` — this copies the migration file and all Agent Ops modules to the VPS.
2. Run Alembic on the VPS: `python -m alembic upgrade e5f6a7b8c9d0`
3. Restart the backend service.
4. Smoke test Agent Ops endpoints: `GET /api/agent-ops/rooms`, `GET /api/agent-ops/agents`, `GET /api/agent-ops/activity`, `GET /api/agent-ops/proposals`.

**Sprint H deploy script was updated in Sprint H.1** (`scripts/deploy_backend_files.ps1`) to include all required Agent Ops backend files and the migration in the explicit allowlist and the SSH backup loop.

Do not run migrations automatically from the deploy script. Migration steps are always separate manual operations approved by Dani.

Do not connect Agent Ops to scanner or evaluator during or after this deploy. The fail-safe logger is present but unwired. No scanner/evaluator/cron behavior changes in this sprint.
