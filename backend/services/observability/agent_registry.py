"""
Static registry of all logical SwissEdge agents.
Agents are listed here regardless of whether they have DB runs yet.
"""
from typing import Any

REGISTRY: dict[str, dict[str, Any]] = {
    "system_doctor": {
        "agent_name": "system_doctor",
        "display_name": "System Doctor",
        "purpose": "Monitor overall system health; check all components and report status",
        "runtime": "fastapi+cron",
        "module": "api.health.router",
        "owner": "FastAPI health router + cron every 12h",
        "current_status": "active",
        "instructions": (
            "Polls internal state (DB, Redis, external APIs, cron jobs). "
            "Runs automatically every 12h via cron and on demand via GET /api/health/full. "
            "Reports each component as ok / warning / error. Never mutates state."
        ),
        "inputs": "No inputs — polls internal state",
        "outputs": "Health report JSON: status per component, recommendations",
        "model": None,
        "tools": ["PostgreSQL ping", "Redis ping", "HTTP probes", "cron log read"],
        "permissions": "Read-only to all components",
        "human_approval_rules": "Not required",
        "cost_metric": "Negligible (no AI)",
        "success_metric": "All components return ok or warning within 20s",
        "failure_modes": ["DB unreachable", "Redis timeout", "SwissEdge service down"],
        "outcome_score_definition": "1 = all ok, 0 = any error",
        "warnings": [],
        "recommended_next_action": "Ensure 12h health-check cron is active on VPS",
    },
    "security_auditor": {
        "agent_name": "security_auditor",
        "display_name": "Security Auditor",
        "purpose": "Detect and report security misconfigurations (open ports, exposed secrets, weak access)",
        "runtime": "claude_code",
        "module": "claude_code",
        "owner": "Claude Code — triggered by Dani",
        "current_status": "active",
        "instructions": (
            "Run manually via /security-review skill in Claude Code. "
            "Inspects VPS SSH access, ufw status, sshd_config, .env exposure. "
            "All destructive actions (password change, firewall rule) require explicit Dani instruction."
        ),
        "inputs": "VPS SSH access, file inspection, ufw status, sshd config",
        "outputs": "Security report: rotated secrets, remaining risks, firewall rules",
        "model": "claude-sonnet-4-6",
        "tools": ["SSH", "SFTP", "ufw", "sshd_config read"],
        "permissions": "Full VPS access via swdeploy sudo",
        "human_approval_rules": "All destructive actions require explicit Dani instruction before executing",
        "cost_metric": "Claude Code session cost",
        "success_metric": "Zero critical secrets exposed, all ports restricted",
        "failure_modes": ["SSH lockout", "firewall misconfiguration"],
        "outcome_score_definition": "1 = all critical items resolved",
        "warnings": [],
        "recommended_next_action": "Run /security-review after any deploy or config change",
    },
    "telegram_router": {
        "agent_name": "telegram_router",
        "display_name": "Telegram Router",
        "purpose": "Receive Telegram messages from Dani, classify intent, route to correct backend endpoint",
        "runtime": "openclaw",
        "module": "openclaw.main",
        "owner": "OpenClaw main agent",
        "current_status": "active",
        "instructions": (
            "Receives all Telegram messages from Dani. Classifies intent using GPT. "
            "Routes to the correct FastAPI endpoint or responds directly. "
            "Cannot write to DB directly. Should pass X-Trigger-Source: telegram header."
        ),
        "inputs": "Telegram message text, user ID, chat ID",
        "outputs": "Telegram reply + HTTP call to FastAPI endpoint",
        "model": "openai/gpt-4o-mini",
        "tools": ["Telegram API (receive/send)", "HTTP calls to FastAPI"],
        "permissions": "Read all FastAPI public endpoints; cannot write to DB directly",
        "human_approval_rules": "Not required for read commands; required for publish/status-change",
        "cost_metric": "OpenAI token cost per conversation turn",
        "success_metric": "Correct endpoint called within 5s, reply sent to Dani",
        "failure_modes": ["FastAPI unreachable", "token expired", "misclassified intent"],
        "outcome_score_definition": "1 = correct endpoint called + reply sent",
        "warnings": ["X-Trigger-Source: telegram header not yet implemented in OpenClaw"],
        "recommended_next_action": "Verify OpenClaw is calling FastAPI with correct endpoint paths",
    },
    "marketplace_lister": {
        "agent_name": "marketplace_lister",
        "display_name": "Marketplace Lister",
        "purpose": "Generate Hochdeutsch marketplace listings from item description",
        "runtime": "fastapi",
        "module": "api.marketplace.router",
        "owner": "POST /api/marketplace/generate-listing",
        "current_status": "partial",
        "instructions": (
            "Receives item description, brand, condition, category, price. "
            "Generates title + description in Hochdeutsch using gpt-4o-mini. "
            "Always sets human_approval_required=True. "
            "Must call complete_with_usage() and log ai_usage on every call. "
            "Output must be valid JSON with title (≥5 words) and description (≥30 words)."
        ),
        "inputs": "Item description, brand, condition, category, price",
        "outputs": "JSON with title, description, category_suggestion",
        "model": "gpt-4o-mini",
        "tools": ["OpenAI API", "listing_generator.txt prompt"],
        "permissions": "AI write (prompt → completion); no DB write",
        "human_approval_rules": "Always required before publishing — non-negotiable safety rule",
        "cost_metric": "Input + output tokens × gpt-4o-mini pricing",
        "success_metric": "Valid JSON returned with title ≥ 5 words, description ≥ 30 words",
        "failure_modes": ["AI API timeout", "non-JSON response", "empty title"],
        "outcome_score_definition": "1 = valid listing draft; 0 = error or empty",
        "warnings": [
            "BUG: ai_usage rows not being created — listing_gen.py called complete() instead of "
            "complete_with_usage(), so model_used/input_tokens/output_tokens/cost stay null in agent_runs."
        ],
        "recommended_next_action": (
            "Fix confirmed: listing_gen.py now uses complete_with_usage() and returns (result, usage). "
            "marketplace router calls log_ai_usage() and passes tokens to finish_run(). "
            "Deploy and verify ai_usage table is populated after next generate-listing call."
        ),
    },
    "marketplace_pricer": {
        "agent_name": "marketplace_pricer",
        "display_name": "Marketplace Pricer",
        "purpose": "Compare item price against current Tutti.ch market data",
        "runtime": "fastapi",
        "module": "api.marketplace.router",
        "owner": "POST /api/marketplace/get-price",
        "current_status": "active",
        "instructions": (
            "Searches Tutti.ch for comparable listings. Returns average, median, min, max, count, currency. "
            "No AI involved — deterministic HTTP scraping. "
            "Note: /search endpoint currently also logs under this agent_name."
        ),
        "inputs": "Item description or search query",
        "outputs": "Price comparison: average, median, min, max, count, currency",
        "model": None,
        "tools": ["Tutti.ch HTTP scraper"],
        "permissions": "HTTP read to Tutti.ch; no DB write",
        "human_approval_rules": "Not required",
        "cost_metric": "Negligible (no AI)",
        "success_metric": "≥1 comparable listing found; comparison object returned",
        "failure_modes": ["Tutti.ch 403 anti-bot", "timeout", "zero results"],
        "outcome_score_definition": "1 = price found; 0 = blocked or empty",
        "warnings": [
            "marketplace_searcher (/search) currently logs runs under this agent_name — counts are combined"
        ],
        "recommended_next_action": (
            "Confirm with Dani whether to split marketplace_searcher into its own agent_name in the router"
        ),
    },
    "marketplace_searcher": {
        "agent_name": "marketplace_searcher",
        "display_name": "Marketplace Searcher",
        "purpose": "Search Tutti.ch listings for a given query; return raw listing results",
        "runtime": "fastapi",
        "module": "api.marketplace.router",
        "owner": "POST /api/marketplace/search",
        "current_status": "pending",
        "instructions": (
            "Intended as a distinct agent for free-text listing search. "
            "The /search endpoint exists and works, but currently logs agent_runs under marketplace_pricer. "
            "Renaming would affect existing DB records — requires Dani confirmation."
        ),
        "inputs": "Search query, limit",
        "outputs": "List of listings: title, price, currency, url, marketplace, condition",
        "model": None,
        "tools": ["Tutti.ch HTTP scraper"],
        "permissions": "HTTP read to Tutti.ch; no DB write",
        "human_approval_rules": "Not required",
        "cost_metric": "Negligible (no AI)",
        "success_metric": "≥1 listing returned without error",
        "failure_modes": ["Tutti.ch 403 anti-bot", "timeout", "zero results"],
        "outcome_score_definition": "1 = results returned; 0 = error or empty",
        "warnings": [
            "Currently logs runs under marketplace_pricer agent_name. No independent runs in DB yet."
        ],
        "recommended_next_action": (
            "Decide: rename agent_name in /search handler to 'marketplace_searcher' for proper tracking"
        ),
    },
    "marketplace_safety_guard": {
        "agent_name": "marketplace_safety_guard",
        "display_name": "Marketplace Safety Guard",
        "purpose": "Prevent unsafe marketplace actions: sharing private info, auto-publishing, arranging meetings",
        "runtime": "fastapi+openclaw",
        "module": "services.telegram.safety",
        "owner": "backend/services/telegram/safety.py + config/safety_rules.yaml",
        "current_status": "partial",
        "instructions": (
            "Rule-based guard that validates outgoing messages and action requests. "
            "Blocks: sharing phone/address, auto-publishing, arranging pickup without user confirmation. "
            "Applied via safety_rules.yaml. Cannot be bypassed by trust score — always enforced."
        ),
        "inputs": "Outgoing message or action request",
        "outputs": "Approved / blocked decision + reason",
        "model": None,
        "tools": ["safety_rules.yaml"],
        "permissions": "Read-only; can block actions",
        "human_approval_rules": "Triggers human approval flow when action is blocked",
        "cost_metric": "None",
        "success_metric": "Zero safety violations",
        "failure_modes": ["Bypass via malformed input", "safety_rules.yaml not loaded"],
        "outcome_score_definition": "1 = all outgoing messages validated; 0 = safety violation",
        "warnings": ["Safety module exists but not yet wired into all outgoing message paths"],
        "recommended_next_action": "Verify safety.py is called on every outgoing Telegram message in OpenClaw",
    },
    "investment_scanner": {
        "agent_name": "investment_scanner",
        "display_name": "Investment Scanner",
        "purpose": "Scan active investment sources for new corporate event filings; create candidate situations",
        "runtime": "fastapi+cron",
        "module": "api.investment.router",
        "owner": "POST /api/investment/scan",
        "current_status": "active",
        "instructions": (
            "Reads active sources from investment_sources DB table (never hardcoded). "
            "For each source, fetches recent filings via the source adapter. "
            "Classifies each filing via investment_classifier, evaluates via investment_evaluator. "
            "Creates SpecialSituation records for new unique filings. "
            "Logs ai_usage for each evaluation call. Sets trigger_source=cron when called via cron."
        ),
        "inputs": "Active sources from investment_sources table, hours_back param (default 6)",
        "outputs": "List of new SpecialSituation records saved to DB; scan summary",
        "model": None,
        "tools": ["SEC EDGAR full-text API", "investment_sources DB table"],
        "permissions": "DB write (special_situations), HTTP read (SEC EDGAR)",
        "human_approval_rules": "Not required for detection; required for status → active",
        "cost_metric": "API call volume, DB rows created",
        "success_metric": "≥0 filings scanned without error; new situations stored",
        "failure_modes": ["SEC EDGAR rate limit", "DB write failure", "source misconfiguration"],
        "outcome_score_definition": "1 = scan completed; partial if some sources failed",
        "warnings": [],
        "recommended_next_action": "Set up cron job: POST /api/investment/scan every 6h",
    },
    "investment_classifier": {
        "agent_name": "investment_classifier",
        "display_name": "Investment Classifier",
        "purpose": "Classify a raw filing into a situation type (spin-off, merger, liquidation, etc.)",
        "runtime": "fastapi",
        "module": "services.investment.sources.sec_edgar",
        "owner": "backend/services/investment/sources/sec_edgar.py — situation_type detection",
        "current_status": "active",
        "instructions": (
            "Rule-based keyword matching on SEC form types. "
            "Called by investment_scanner for each filing fetched. "
            "Returns a situation_type string, or None if the filing is not a special situation."
        ),
        "inputs": "Filing metadata (form type, title, description)",
        "outputs": "situation_type string; None if not classifiable",
        "model": None,
        "tools": ["SEC EDGAR filing metadata"],
        "permissions": "Read-only",
        "human_approval_rules": "Not required",
        "cost_metric": "None",
        "success_metric": "Correct situation_type assigned for all known form types",
        "failure_modes": ["Unknown form type returns None — filing silently skipped"],
        "outcome_score_definition": "1 = classified; 0 = unclassifiable",
        "warnings": [],
        "recommended_next_action": "Extend form-type keyword map as new situation types are encountered",
    },
    "investment_evaluator": {
        "agent_name": "investment_evaluator",
        "display_name": "Investment Evaluator",
        "purpose": "Evaluate a classified filing against the investment course methodology; produce structured analysis",
        "runtime": "fastapi",
        "module": "services.investment.evaluator",
        "owner": "backend/services/investment/evaluator.py",
        "current_status": "active",
        "instructions": (
            "Receives a Filing object and the course checklist+playbook for its situation type. "
            "Calls gpt-4o-mini with situation_evaluator.txt prompt. "
            "Returns evaluation dict: checklist_results, strengths, weaknesses, risks, confidence, "
            "recommendation, disclaimer. "
            "ALWAYS include 'This is not financial advice' in the disclaimer field."
        ),
        "inputs": "Filing object (company, type, summary), course checklist + playbook for situation type",
        "outputs": "Evaluation dict with checklist_results, strengths, weaknesses, risks, confidence, recommendation, disclaimer",
        "model": "gpt-4o-mini",
        "tools": ["OpenAI API", "situation_evaluator.txt prompt", "course_index files"],
        "permissions": "AI write; no direct DB write (result stored by scanner)",
        "human_approval_rules": "Not required for evaluation; required for status → active",
        "cost_metric": "Input + output tokens × gpt-4o-mini pricing",
        "success_metric": "Valid JSON returned with confidence field; disclaimer present",
        "failure_modes": ["Non-JSON response", "AI timeout", "missing course index"],
        "outcome_score_definition": "1 = evaluation complete with confidence; 0 = error or PASS recommendation",
        "warnings": [],
        "recommended_next_action": "Verify course_index files are present for all 4 situation types on VPS",
    },
    "course_reference_agent": {
        "agent_name": "course_reference_agent",
        "display_name": "Course Reference Agent",
        "purpose": "Retrieve relevant course chapter, checklist, and playbook for a given situation type",
        "runtime": "fastapi",
        "module": "services.investment.course_index",
        "owner": "backend/services/investment/course_index.py",
        "current_status": "partial",
        "instructions": (
            "Reads from course_index/ static files generated by scripts/ingest_course.py. "
            "Never re-reads raw transcripts. Returns chapter info, checklist, playbook for a situation_type. "
            "Returns empty/None gracefully if master_index.json is missing — callers must handle this."
        ),
        "inputs": "situation_type string",
        "outputs": "Chapter info, checklist list, playbook list",
        "model": None,
        "tools": ["course_index/ static files"],
        "permissions": "Read-only to course_index/ directory",
        "human_approval_rules": "Not required",
        "cost_metric": "None",
        "success_metric": "Returns non-empty checklist for all 4 known situation types",
        "failure_modes": ["Missing chapter file", "malformed master_index.json"],
        "outcome_score_definition": "1 = content returned; 0 = empty or file missing",
        "warnings": ["course_index/ is git-ignored — files must be present on VPS separately"],
        "recommended_next_action": "Run scripts/ingest_course.py to generate course_index/ if missing on VPS",
    },
    "publisher_agent": {
        "agent_name": "publisher_agent",
        "display_name": "Publisher Agent",
        "purpose": "Publish marketplace listings or investment summaries to external platforms",
        "runtime": "fastapi",
        "module": "api.marketplace.router",
        "owner": "POST /api/marketplace/publish",
        "current_status": "partial",
        "instructions": (
            "Phase 1: generates copy-paste listing text only. "
            "Writes to a marketplace ONLY when approved=true is explicitly set in the request. "
            "Human approval is NON-NEGOTIABLE — never auto-publish regardless of trust score."
        ),
        "inputs": "Item ID, marketplace target, approval flag",
        "outputs": "Draft listing URL or copy-paste text",
        "model": None,
        "tools": ["Tutti.ch adapter (phase 1: stub)"],
        "permissions": "Write to marketplaces ONLY if approved=true is explicit",
        "human_approval_rules": "ALWAYS required — approved=true must be explicit",
        "cost_metric": "None (phase 1)",
        "success_metric": "Listing text generated; external publish only if explicitly approved",
        "failure_modes": ["Missing approval flag", "adapter failure", "marketplace down"],
        "outcome_score_definition": "1 = published or draft returned; 0 = blocked by safety",
        "warnings": ["Tutti.ch create-listing adapter is a stub — actual publish not yet active"],
        "recommended_next_action": "Implement Tutti.ch create-listing API integration in phase 2",
    },
    "contact_discovery_agent": {
        "agent_name": "contact_discovery_agent",
        "display_name": "Contact Discovery Agent",
        "purpose": "Discover public investor contacts (activists, specialists) from public sources",
        "runtime": "future",
        "module": "services.investment.contact_discovery",
        "owner": "Not yet assigned",
        "current_status": "future",
        "instructions": (
            "Planned for a future phase. Will search public SEC 13D/13G filings and web sources "
            "to find activist investors and specialists relevant to a detected situation. "
            "Human approval required before using any contact data for outreach."
        ),
        "inputs": "Situation type, company name, filing keywords",
        "outputs": "InvestorContact records saved to DB",
        "model": "TBD",
        "tools": ["Web search", "SEC 13D/13G filings", "SEC EDGAR"],
        "permissions": "HTTP read; DB write to investor_contacts",
        "human_approval_rules": "Required before using contact data for outreach",
        "cost_metric": "TBD",
        "success_metric": "≥1 relevant contact found per situation",
        "failure_modes": ["No public filings found", "rate limiting"],
        "outcome_score_definition": "TBD",
        "warnings": ["Not yet implemented"],
        "recommended_next_action": "Design and spec contact_discovery_agent in phase 3 planning",
    },
    "claude_engineer": {
        "agent_name": "claude_engineer",
        "display_name": "Claude Engineer",
        "purpose": "Build, fix, deploy, and audit the SwissEdge platform during engineering sessions",
        "runtime": "claude_code",
        "module": "claude_code",
        "owner": "Claude Code (Anthropic), triggered by Dani",
        "current_status": "active",
        "instructions": (
            "Runs during Claude Code engineering sessions. Builds all code, runs /doctor to diagnose failures. "
            "Appends to docs/engineering-log.md after each session. "
            "NEVER deploys without explicit 'deploy' or 'apply' instruction from Dani. "
            "Uses swdeploy + sudo -S for all VPS operations. "
            "Every AI call must use complete_with_usage(). "
            "Every new FastAPI endpoint that calls AI/external API must call run_logger start/finish/fail."
        ),
        "inputs": "Dani's task description, codebase state, VPS state",
        "outputs": "Code changes, deployments, health reports, engineering log entries",
        "model": "claude-sonnet-4-6",
        "tools": ["File read/write", "SSH", "SFTP", "bash", "git"],
        "permissions": "Full local file access; VPS access via swdeploy sudo; no autonomous deployment",
        "human_approval_rules": "Required for all VPS deployments, firewall changes, secret rotations",
        "cost_metric": "Claude Code session token usage (see docs/claude-code-usage.md)",
        "success_metric": "Task complete, tests pass, service remains healthy after deploy",
        "failure_modes": ["SSH timeout", "broken deploy", "regression in existing features"],
        "outcome_score_definition": "1 = task delivered + service healthy; 0 = rollback needed",
        "warnings": [],
        "recommended_next_action": "Log session cost via POST /api/observability/claude-session at end of session",
    },
    "openclaw_operator": {
        "agent_name": "openclaw_operator",
        "display_name": "OpenClaw Operator",
        "purpose": "Execute operational commands via Telegram on behalf of Dani: trigger scans, check status, move situations",
        "runtime": "openclaw",
        "module": "openclaw.main",
        "owner": "OpenClaw main agent (all Telegram commands that call FastAPI)",
        "current_status": "active",
        "instructions": (
            "Receives Dani's Telegram commands. Calls the correct FastAPI endpoint. "
            "Publish actions require 'sí, publicar' explicitly from Dani. "
            "Status changes to active require confirmation. "
            "Must never bypass FastAPI to write to DB directly."
        ),
        "inputs": "Telegram command text, Dani's intent",
        "outputs": "FastAPI API call + formatted Telegram reply",
        "model": "openai/gpt-4o-mini",
        "tools": ["All FastAPI endpoints listed in CLAUDE.md"],
        "permissions": "All read endpoints; PATCH/POST to investment and marketplace within safety rules",
        "human_approval_rules": "Publish requires 'sí, publicar'; status → active requires confirmation",
        "cost_metric": "OpenAI token cost per command",
        "success_metric": "Correct FastAPI endpoint called; accurate reply to Dani; no safety violations",
        "failure_modes": ["FastAPI down", "ambiguous command", "safety rule triggered"],
        "outcome_score_definition": "1 = action completed correctly; 0 = wrong endpoint or safety block",
        "warnings": [],
        "recommended_next_action": "Verify OpenClaw is alive and routing to correct FastAPI endpoint paths",
    },
    "source_registry_manager": {
        "agent_name": "source_registry_manager",
        "display_name": "Source Registry Manager",
        "purpose": "Manage the investment_sources table: add, update, activate, deactivate investment sources",
        "runtime": "fastapi",
        "module": "api.investment.router",
        "owner": "CRUD endpoints at /api/investment/sources",
        "current_status": "active",
        "instructions": (
            "Provides CRUD for the investment_sources table via REST. "
            "New sources must be added via POST /api/investment/sources or config/investment_sources.yaml seed. "
            "NEVER hardcode sources in scanner code — always read from the DB table. "
            "Sources with active=false are skipped by investment_scanner."
        ),
        "inputs": "Source name, URL, type, frequency_hours, market, jurisdiction",
        "outputs": "Updated InvestmentSource records in DB",
        "model": None,
        "tools": ["PostgreSQL — investment_sources table"],
        "permissions": "DB read/write for investment_sources table only",
        "human_approval_rules": "Not required for source management; deletions require care",
        "cost_metric": "None",
        "success_metric": "Sources correctly listed and scanner uses active sources only",
        "failure_modes": ["DB write failure", "duplicate source name", "invalid URL"],
        "outcome_score_definition": "1 = source registry accurate; scanner uses correct sources",
        "warnings": [],
        "recommended_next_action": "Seed initial sources via config/investment_sources.yaml if DB table is empty",
    },
}


def get_all() -> list[dict[str, Any]]:
    return list(REGISTRY.values())


def get_one(agent_name: str) -> dict[str, Any] | None:
    return REGISTRY.get(agent_name)
