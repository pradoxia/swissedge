# Ricardo Integration Design — SwissEdge Sales Automation

**Status:** Design note — not implemented  
**Date:** 2026-04-30  
**Scope:** SwissEdge marketplace/sales module only

---

## 1. Integration Modes

| Mode | Description | Complexity | Risk |
|---|---|---|---|
| **Manual copy/paste** | SwissEdge generates a Ricardo-formatted draft; Dani copies fields manually into Ricardo web UI | None | None |
| **Ricardo-ready payload** | SwissEdge generates a structured JSON payload matching Ricardo's listing fields; Dani exports/pastes into Ricardo Import or draft tool | Low | Low |
| **Product feed / professional seller** | Ricardo's JSON feed format for bulk/pro sellers; requires a Ricardo seller account with feed access enabled | Medium | Medium — requires Ricardo account setup |
| **Official OAuth / token flow** | Ricardo documented a `SellService.InsertArticle` API and token/app authorization model; user grants SwissEdge a scoped token without sharing password | High | Low if implemented correctly |
| **Browser automation** | Selenium/Playwright logs into Ricardo on Dani's behalf | Very High | **High** — violates Ricardo ToS / robots.txt; fragile; credential exposure risk |

**Browser automation must not be implemented without explicit Dani approval and legal review.**  
Ricardo `robots.txt` disallows `/login`, `/api/listing-form`, and `/marketplace-spa/api/questions`.

---

## 2. Recommended Phased Roadmap

### Phase 1 — Assisted Manual (current / next sprint)
- SwissEdge generates a **Ricardo-ready structured draft** from the listing form.
- Draft fields: title, description (Hochdeutsch), category suggestion, condition, price, location.
- Dani copies each field manually into Ricardo web UI.
- No credentials stored. No API calls. No automation.
- **UI addition:** "Ricardo Draft" tab/panel on `/marketplace/sales` showing field-by-field copy buttons.

### Phase 2 — Ricardo-Ready JSON Payload
- SwissEdge renders a downloadable/copyable JSON payload matching Ricardo's import format.
- Dani can paste into Ricardo's bulk upload or professional feed tool if account supports it.
- Still requires Dani to initiate upload manually.
- No Ricardo credentials stored in SwissEdge.

### Phase 3 — Official Token Flow (if Ricardo API is accessible)
- Implement OAuth/app token flow: user is redirected to Ricardo to authorize; SwissEdge receives a scoped access token (not the password).
- Token stored **encrypted at rest** in `.env`/secrets manager — never in DB plain text or code.
- `POST /api/marketplace/publish-ricardo` endpoint created; guarded by human approval gate.
- Dani still confirms each publish action before execution.
- Token refresh handled server-side, never exposed to frontend.

### Phase 4 — Buyer Question Routing (after Phase 3 is stable)
- Ricardo Q&A events polled or webhook-received.
- Each question stored as a `buyer_question` record (DB) with status `pending_dani`.
- Telegram alert sent to Dani with question text and AI-suggested reply options.
- Dani selects/edits reply; SwissEdge sends via Ricardo API only after explicit confirmation.
- **No automated replies** until Dani has approved at least 10 responses for that item type.

---

## 3. Account / Security Model

### What must never be stored in plain text
- Ricardo username / password
- Session cookies
- Any OAuth access or refresh token in source code or committed files
- Buyer contact details (phone, email, address)

### Credential handling for Phase 3+
- OAuth tokens stored in `.env` on VPS only (never committed).
- Token encrypted at rest using `cryptography.fernet` or equivalent before DB write if persistence is needed.
- Token rotation handled automatically; rotation failures trigger Telegram alert to Dani.
- `scripts/vps_config.py` (local only, not committed) holds placeholder comments for Ricardo token env vars.
- All token operations wrapped in try/except; failure mode is "degrade to manual copy/paste", never silent.

### What requires Dani confirmation (always)
- Every publish action, regardless of phase
- Every buyer reply sent
- Any price change on an existing listing
- Any listing deletion or archive
- Any pickup or meeting arrangement message

---

## 4. Publishing Model

```
SwissEdge generates draft
    ↓
Dani reviews title / description / price / photos
    ↓
Dani confirms (click / Telegram approval)
    ↓
Phase 1: Dani copies to Ricardo manually
Phase 3: SwissEdge calls Ricardo API with confirmed payload
    ↓
Confirmation stored: listing_id, platform, published_at
```

**Image handling:**  
- SwissEdge must never alter image content in a way that misrepresents item condition (e.g. removing scratches, brightening to hide wear).
- Metadata-only operations (resize, format conversion) are acceptable.
- Any AI enhancement requires a visible disclaimer in the draft.

---

## 5. Buyer Questions Model

```
Ricardo Q&A event (API poll or webhook)
    ↓
SwissEdge stores question: buyer_questions table
    [item_id, platform, question_text, received_at, status=pending_dani]
    ↓
Telegram alert → Dani with question + 2-3 AI-suggested replies
    ↓
Dani selects or writes reply
    ↓
SwissEdge sends reply via Ricardo API
    [reply stored: replied_at, reply_text, sent_by=dani]
    ↓
No automated reply until trust threshold reached (Dani decision)
```

**Never automate:**
- Price negotiation acceptance
- Pickup/meeting arrangement
- Personal contact information exchange
- Offer acceptance

---

## 6. Risks and Guardrails

| Risk | Mitigation |
|---|---|
| Ricardo ToS violation via browser automation | Disallowed until explicit legal review + Dani approval |
| Credential leak | No passwords stored; OAuth tokens encrypted; no secrets in code/docs |
| Misrepresentation via AI-enhanced images | Image content modification disallowed; disclaimer required if any enhancement |
| Automated buyer reply backfire | All replies require Dani approval; no trust-based automation initially |
| Stale/expired tokens causing silent publish failures | Rotation monitored; failure degrades to manual with Telegram alert |
| PII in buyer messages leaked to logs | Buyer contact details excluded from agent_runs logs; masked in observability |
| robots.txt violations | `/login`, `/api/listing-form`, `/marketplace-spa/api/questions` never called by SwissEdge automation |

---

## 7. Data Model (Phase 3+, not implemented yet)

```sql
-- marketplace_listings
id, platform, external_listing_id, title, description, price_chf,
condition, category, status, published_at, archived_at,
agent_run_id, created_at, updated_at

-- buyer_questions
id, listing_id, platform, question_text, received_at,
status (pending_dani | replied | ignored),
suggested_replies (jsonb), reply_text, replied_at, sent_by

-- marketplace_tokens (Phase 3 only)
id, platform, token_hash (encrypted), expires_at, last_refreshed_at
-- NOTE: raw token never stored; only encrypted blob
```

---

## 8. Recommended Next Implementation Sprint

**Sprint 26 — Ricardo-Ready Draft Panel (Phase 1)**

- Add a "Ricardo Draft" tab/section to `/marketplace/sales` (frontend only).
- On form submit, render a second structured panel with Ricardo-specific field mapping:
  - Titel (≤60 chars)
  - Beschreibung (≤2000 chars)
  - Kategorie (Ricardo category suggestion)
  - Zustand (mapped from condition dropdown)
  - Preis CHF
  - Standort
- Individual copy buttons per field (already available via `CopyButton`).
- "Copy all as text" block for manual paste.
- No backend changes required.
- No credentials. No API. No scraping.
- Build validation: `cd frontend && npm run build`.
