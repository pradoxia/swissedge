# SwissEdge — Logical Agent Registry
> Authoritative definition of every logical agent in the system.
> Last updated: 2026-04-27. Owner: Dani / SwissEdge.

---

## Agent taxonomy

| Runtime | Description |
|---------|-------------|
| `fastapi` | Runs inside the FastAPI backend process |
| `cron` | Triggered by system crontab via HTTP call to FastAPI |
| `openclaw` | Runs inside the OpenClaw gateway process, responds to Telegram |
| `claude_code` | Runs during Claude Code engineering sessions (on-demand) |
| `future` | Planned but not yet implemented |

---

## 1. system_doctor

| Field | Value |
|-------|-------|
| **Purpose** | Monitor overall system health; check all components and report status |
| **Runtime** | `fastapi` + `cron` |
| **Owner** | FastAPI health router + cron every 12h |
| **Inputs** | No inputs — polls internal state |
| **Outputs** | Health report JSON: status per component, recommendations |
| **Model** | None |
| **Tools** | PostgreSQL ping, Redis ping, HTTP probes, cron log read |
| **Permissions** | Read-only to all components |
| **Human approval** | Not required |
| **Cost metric** | Negligible (no AI) |
| **Success metric** | All components return `ok` or `warning` within 20s |
| **Failure modes** | DB unreachable, Redis timeout, SwissEdge service down |
| **Outcome score** | 1 = all ok, 0 = any error |

---

## 2. security_auditor

| Field | Value |
|-------|-------|
| **Purpose** | Detect and report security misconfigurations (open ports, exposed secrets, weak access) |
| **Runtime** | `claude_code` (manual) |
| **Owner** | Claude Code — triggered by Dani |
| **Inputs** | VPS SSH access, file inspection, ufw status, sshd config |
| **Outputs** | Security report: rotated secrets, remaining risks, firewall rules |
| **Model** | claude-sonnet-4-6 (Claude Code) |
| **Tools** | SSH, SFTP, ufw, sshd_config read |
| **Permissions** | Full VPS access via `swdeploy` sudo |
| **Human approval** | All destructive actions (password change, firewall rule) require explicit instruction from Dani |
| **Cost metric** | Claude Code session cost |
| **Success metric** | Zero critical secrets exposed, all ports restricted |
| **Failure modes** | SSH lockout, firewall misconfiguration |
| **Outcome score** | 1 = all critical items resolved |

---

## 3. telegram_router

| Field | Value |
|-------|-------|
| **Purpose** | Receive Telegram messages from Dani, classify intent, route to correct backend endpoint or respond directly |
| **Runtime** | `openclaw` |
| **Owner** | OpenClaw main agent |
| **Inputs** | Telegram message text, user ID, chat ID |
| **Outputs** | Telegram reply + HTTP call to FastAPI endpoint |
| **Model** | `openai/gpt-5-mini` |
| **Tools** | Telegram API (receive/send), HTTP calls to FastAPI |
| **Permissions** | Read all FastAPI public endpoints; cannot write to DB directly |
| **Human approval** | Not required for read commands; required for publish/status-change |
| **Cost metric** | OpenAI token cost per conversation turn |
| **Success metric** | Correct endpoint called within 5s, reply sent to Dani |
| **Failure modes** | FastAPI unreachable, token expired, misclassified intent |
| **Outcome score** | 1 = correct endpoint called + reply sent |

---

## 4. marketplace_lister

| Field | Value |
|-------|-------|
| **Purpose** | Generate Hochdeutsch marketplace listings from item description |
| **Runtime** | `fastapi` |
| **Owner** | `POST /api/marketplace/generate-listing` |
| **Inputs** | Item description, brand, condition, category, price |
| **Outputs** | JSON with `title`, `description`, `category_suggestion` |
| **Model** | `gpt-4o-mini` (via ai_client) |
| **Tools** | OpenAI API, listing_generator.txt prompt |
| **Permissions** | AI write (prompt → completion); no DB write |
| **Human approval** | Always required before publishing (safety rule) |
| **Cost metric** | Input + output tokens × gpt-4o-mini pricing |
| **Success metric** | Valid JSON returned with title ≥ 5 words, description ≥ 30 words |
| **Failure modes** | AI API timeout, non-JSON response, empty title |
| **Outcome score** | 1 = valid listing draft; 0 = error or empty |

---

## 5. marketplace_pricer

| Field | Value |
|-------|-------|
| **Purpose** | Compare item price against current Tutti.ch market data |
| **Runtime** | `fastapi` |
| **Owner** | `POST /api/marketplace/get-price` |
| **Inputs** | Item description/search query |
| **Outputs** | Price comparison: average, median, min, max, count, currency |
| **Model** | None |
| **Tools** | Tutti.ch HTTP scraper |
| **Permissions** | HTTP read to Tutti.ch; no DB write |
| **Human approval** | Not required |
| **Cost metric** | Negligible (no AI) |
| **Success metric** | ≥1 comparable listing found; comparison object returned |
| **Failure modes** | Tutti.ch 403 anti-bot, timeout, zero results |
| **Outcome score** | 1 = price found; 0 = blocked or empty |

---

## 6. marketplace_safety_guard

| Field | Value |
|-------|-------|
| **Purpose** | Prevent unsafe marketplace actions: sharing private info, auto-publishing, arranging meetings |
| **Runtime** | `fastapi` + `openclaw` |
| **Owner** | `backend/services/telegram/safety.py` + SWISSEDGE.md rules |
| **Inputs** | Outgoing message or action request |
| **Outputs** | Approved / blocked decision + reason |
| **Model** | None (rule-based) |
| **Tools** | `safety_rules.yaml` |
| **Permissions** | Read-only; can block actions |
| **Human approval** | Triggers human approval flow when action is blocked |
| **Cost metric** | None |
| **Success metric** | Zero safety violations |
| **Failure modes** | Bypass via malformed input, YAML not loaded |
| **Outcome score** | 1 = all messages validated |

---

## 7. investment_scanner

| Field | Value |
|-------|-------|
| **Purpose** | Scan active investment sources for new corporate event filings; create candidate situations |
| **Runtime** | `fastapi` + `cron` (every 6h) |
| **Owner** | `POST /api/investment/scan` |
| **Inputs** | Active sources from `investment_sources` table, `hours_back` param |
| **Outputs** | List of new `SpecialSituation` records saved to DB; scan summary |
| **Model** | None (source fetching is deterministic) |
| **Tools** | SEC EDGAR full-text API, `investment_sources` DB table |
| **Permissions** | DB write (special_situations), HTTP read (SEC EDGAR) |
| **Human approval** | Not required for detection; required for status → active |
| **Cost metric** | API call volume, DB rows created |
| **Success metric** | ≥0 filings scanned without error; new situations stored |
| **Failure modes** | SEC EDGAR rate limit, DB write failure, source misconfiguration |
| **Outcome score** | 1 = scan completed; partial if some sources failed |

---

## 8. investment_classifier

| Field | Value |
|-------|-------|
| **Purpose** | Classify a raw filing into a situation type (spin-off, merger, etc.) |
| **Runtime** | `fastapi` (called from scanner) |
| **Owner** | `backend/services/investment/sources/sec_edgar.py` — `situation_type` detection |
| **Inputs** | Filing metadata (form type, title, description) |
| **Outputs** | `situation_type` string; `None` if not a special situation |
| **Model** | None (rule-based keyword matching on form types) |
| **Tools** | SEC EDGAR filing metadata |
| **Permissions** | Read-only |
| **Human approval** | Not required |
| **Cost metric** | None |
| **Success metric** | Correct situation_type assigned for known form types |
| **Failure modes** | Unknown form type returns None (filing skipped) |
| **Outcome score** | 1 = classified; 0 = unclassifiable |

---

## 9. investment_evaluator

| Field | Value |
|-------|-------|
| **Purpose** | Evaluate a classified filing against the 22-chapter investment course methodology; produce structured analysis |
| **Runtime** | `fastapi` (called from scanner after classification) |
| **Owner** | `backend/services/investment/evaluator.py` |
| **Inputs** | `Filing` object (company, type, summary), course checklist + playbook for situation type |
| **Outputs** | Evaluation dict: checklist_results, strengths, weaknesses, risks, confidence, recommendation, disclaimer |
| **Model** | `gpt-4o-mini` (via ai_client) |
| **Tools** | OpenAI API, situation_evaluator.txt prompt, course_index files |
| **Permissions** | AI write; no direct DB write (result stored by scanner) |
| **Human approval** | Not required for evaluation; required to move to `active` status |
| **Cost metric** | Input + output tokens × gpt-4o-mini pricing |
| **Success metric** | Valid JSON returned with confidence field; disclaimer present |
| **Failure modes** | Non-JSON response, AI timeout, missing course index |
| **Outcome score** | 1 = evaluation complete with confidence; 0 = error or PASS recommendation |

---

## 10. course_reference_agent

| Field | Value |
|-------|-------|
| **Purpose** | Retrieve relevant course chapter, checklist, and playbook for a given situation type |
| **Runtime** | `fastapi` (utility, called by evaluator) |
| **Owner** | `backend/services/investment/course_index.py` |
| **Inputs** | `situation_type` string |
| **Outputs** | Chapter info, checklist list, playbook list |
| **Model** | None (deterministic file read) |
| **Tools** | `course_index/` static files |
| **Permissions** | Read-only to `course_index/` directory |
| **Human approval** | Not required |
| **Cost metric** | None |
| **Success metric** | Returns non-empty checklist for all 4 known situation types |
| **Failure modes** | Missing chapter file, malformed master_index.json |
| **Outcome score** | 1 = content returned; 0 = empty or file missing |

---

## 11. publisher_agent

| Field | Value |
|-------|-------|
| **Purpose** | Publish marketplace listings or investment situation summaries to external platforms |
| **Runtime** | `fastapi` (phase 1: copy-paste text only) |
| **Owner** | `POST /api/marketplace/publish` |
| **Inputs** | Item ID, marketplace target, approval flag |
| **Outputs** | Draft listing URL or copy-paste text |
| **Model** | None |
| **Tools** | Tutti.ch adapter (phase 1: stub) |
| **Permissions** | Write to marketplaces (ONLY if approved=true) |
| **Human approval** | **Always required** — `approved=true` must be explicit in request |
| **Cost metric** | None (phase 1) |
| **Success metric** | Listing text generated; external publish only if explicitly approved |
| **Failure modes** | Missing approval, adapter failure, marketplace down |
| **Outcome score** | 1 = published or draft returned; 0 = blocked by safety |

---

## 12. contact_discovery_agent

| Field | Value |
|-------|-------|
| **Purpose** | Discover public investor contacts (activists, specialists) from public sources |
| **Runtime** | `future` |
| **Owner** | Not yet assigned |
| **Inputs** | Situation type, company name, filing keywords |
| **Outputs** | `InvestorContact` records in DB |
| **Model** | TBD |
| **Tools** | Web search, SEC 13D/13G filings, SEC EDGAR |
| **Permissions** | HTTP read; DB write to `investor_contacts` |
| **Human approval** | Required before using contact data for outreach |
| **Cost metric** | TBD |
| **Success metric** | ≥1 relevant contact found per situation |
| **Failure modes** | No public filings found, rate limiting |
| **Outcome score** | TBD |

---

## 13. claude_engineer

| Field | Value |
|-------|-------|
| **Purpose** | Build, fix, deploy, and audit the SwissEdge platform during engineering sessions |
| **Runtime** | `claude_code` |
| **Owner** | Claude Code (Anthropic), triggered by Dani |
| **Inputs** | Dani's task description, codebase, VPS state |
| **Outputs** | Code changes, deployments, reports, SYSTEM.md updates |
| **Model** | `claude-sonnet-4-6` |
| **Tools** | File read/write, SSH, SFTP, bash, git |
| **Permissions** | Full local file access; VPS access via `swdeploy` sudo; no autonomous deployment (requires Dani approval) |
| **Human approval** | Required for all VPS deployments, firewall changes, secret rotations |
| **Cost metric** | Claude Code session token usage (see `docs/claude-code-usage.md`) |
| **Success metric** | Task complete, tests pass, service remains healthy after deploy |
| **Failure modes** | SSH timeout, broken deploy, regression in existing features |
| **Outcome score** | 1 = task delivered + service healthy; 0 = rollback needed |

---

## 14. openclaw_operator

| Field | Value |
|-------|-------|
| **Purpose** | Execute operational commands via Telegram on behalf of Dani: trigger scans, check status, move situations |
| **Runtime** | `openclaw` |
| **Owner** | OpenClaw main agent (all Telegram commands that call FastAPI) |
| **Inputs** | Telegram command text, Dani's intent |
| **Outputs** | FastAPI API call + formatted Telegram reply |
| **Model** | `openai/gpt-5-mini` |
| **Tools** | All FastAPI endpoints listed in SWISSEDGE.md |
| **Permissions** | All read endpoints; PATCH/POST to investment and marketplace (within safety rules) |
| **Human approval** | Publish actions always require `"sí, publicar"` from Dani; status changes to `active` require confirmation |
| **Cost metric** | OpenAI token cost per command |
| **Success metric** | Correct FastAPI endpoint called; accurate reply to Dani; no safety violations |
| **Failure modes** | FastAPI down, ambiguous command, safety rule triggered |
| **Outcome score** | 1 = action completed correctly; 0 = wrong endpoint or safety block |
