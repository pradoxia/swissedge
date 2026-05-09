# Sales Item Persistence — Design Note

**Status:** Design only — not implemented
**Date:** 2026-04-30
**Sprint:** 27
**Scope:** SwissEdge Marketplace / Sales module

---

## 1. Why persistence now?

The current sales pipeline is entirely stateless: the Telegram bot collects intake answers in a single conversation thread, the listing generator produces a draft, and everything disappears if the session ends. Without persistence:

- Dani cannot resume a half-finished intake
- No audit trail of what was listed, at what price, on which platform
- Buyer questions cannot be routed async (Phase 2+)
- Analytics on sell-through rate, time-to-sell, pricing accuracy are impossible

Persistence is the prerequisite for every phase beyond "manual copy/paste."

---

## 2. Existing model inventory

| Model | Table | Notes |
|---|---|---|
| `InventoryItem` | `inventory_items` | Personal inventory; single `marketplace` field (string); no sub-tables; closest existing model |
| `SpecialSituation` | `special_situations` | Two-table pattern with `SituationHistory`; UUID PK; JSONB; ForeignKey + relationship |
| `AgentRun` | `agent_runs` | Observability; UUID PK; `_now()` helper |

No existing sales item tables. The new schema must be created from scratch.

---

## 3. Proposed data model

### 3.1 Table overview

```
sales_items          ← one row per physical item Dani wants to sell
  └── sales_item_photos       ← one row per photo attached to the item
  └── sales_platform_listings ← one row per (item × platform) listing attempt

buyer_questions      ← Phase 2+, one row per inbound buyer question per listing
```

### 3.2 `sales_items`

Core record created when Dani triggers sales intake (Telegram or web form).

```python
class SalesItem(Base):
    __tablename__ = "sales_items"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str | None] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
    condition: Mapped[str | None] = mapped_column(String(40))
    # "new" | "like_new" | "very_good" | "good" | "with_defects"
    asking_price_chf: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    observed_price_low_chf: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    observed_price_high_chf: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    pickup_location: Mapped[str | None] = mapped_column(String(200))
    shipping_offered: Mapped[bool] = mapped_column(Boolean, default=False)
    defects_notes: Mapped[str | None] = mapped_column(Text)
    accessories_notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="needs_info")
    intake_source: Mapped[str | None] = mapped_column(String(40))
    # "telegram" | "web"
    telegram_chat_id: Mapped[str | None] = mapped_column(String(40))
    generated_draft: Mapped[dict | None] = mapped_column(JSONB)
    # stores last ListingDraft payload from generate-listing endpoint
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    photos: Mapped[list["SalesItemPhoto"]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )
    platform_listings: Mapped[list["SalesPlatformListing"]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )
```

### 3.3 Item status model

```
needs_info      ← intake started; one or more of the 5 intake questions unanswered
draft_ready     ← all 5 intake fields present; generate-listing has been called
ready_to_publish← Dani has reviewed and approved the draft
published       ← at least one platform_listing has status=published
sold            ← Dani marked as sold
archived        ← removed from active flow (not sold; withdrawn)
```

Valid transitions:

```
needs_info → draft_ready → ready_to_publish → published → sold
                                           ↘            ↘
                                            archived      archived
needs_info → archived   (user cancels early)
draft_ready → needs_info (Dani edits a field, draft must be regenerated)
```

Status changes are written by the API; the Telegram bot never writes status directly — it calls API endpoints.

### 3.4 `sales_item_photos`

```python
class SalesItemPhoto(Base):
    __tablename__ = "sales_item_photos"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    item_id: Mapped[UUID] = mapped_column(ForeignKey("sales_items.id", ondelete="CASCADE"))
    telegram_file_id: Mapped[str | None] = mapped_column(String(200))
    storage_path: Mapped[str | None] = mapped_column(String(500))
    # local VPS path or object storage key; null until downloaded
    mime_type: Mapped[str | None] = mapped_column(String(80))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    item: Mapped["SalesItem"] = relationship(back_populates="photos")
```

Photos are kept separate so the item record stays lean and photo storage can be deferred (Phase 2).

### 3.5 `sales_platform_listings`

One row per (item × platform) attempt. Supports listing the same item on Ricardo + Tutti simultaneously.

```python
class SalesPlatformListing(Base):
    __tablename__ = "sales_platform_listings"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    item_id: Mapped[UUID] = mapped_column(ForeignKey("sales_items.id", ondelete="CASCADE"))
    platform: Mapped[str] = mapped_column(String(40))
    # "ricardo" | "tutti" | "anibis" | "facebook"
    status: Mapped[str] = mapped_column(String(40), default="not_listed")
    external_listing_id: Mapped[str | None] = mapped_column(String(200))
    listing_url: Mapped[str | None] = mapped_column(String(500))
    listed_price_chf: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sold_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    item: Mapped["SalesItem"] = relationship(back_populates="platform_listings")
```

Platform listing status model:

```
not_listed   ← default; item approved but not yet sent to this platform
draft        ← Ricardo-ready JSON payload generated; waiting for Dani to publish manually (Phase 1)
published    ← Dani confirmed publication (manual or API)
sold         ← Dani marked as sold on this platform
archived     ← removed from this platform without selling
```

### 3.6 `buyer_questions` (Phase 2+, not implemented)

```python
class BuyerQuestion(Base):
    __tablename__ = "buyer_questions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    platform_listing_id: Mapped[UUID] = mapped_column(
        ForeignKey("sales_platform_listings.id", ondelete="CASCADE")
    )
    platform: Mapped[str] = mapped_column(String(40))
    question_text: Mapped[str] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(40), default="pending_dani")
    # "pending_dani" | "replied" | "ignored"
    suggested_replies: Mapped[list | None] = mapped_column(JSONB)
    reply_text: Mapped[str | None] = mapped_column(Text)
    replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_by: Mapped[str | None] = mapped_column(String(40))
    # "dani" always for now
```

**Hard rule:** `status` must never be set to `replied` without an explicit Dani confirmation event recorded.

---

## 4. API endpoint proposal

All endpoints live under `/api/marketplace/sales/`.

### Phase 1 endpoints (implement first)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/marketplace/sales/items` | Create item from intake data |
| `GET` | `/api/marketplace/sales/items` | List items (filter by status, limit/offset) |
| `GET` | `/api/marketplace/sales/items/{id}` | Get single item with photos + platform listings |
| `PATCH` | `/api/marketplace/sales/items/{id}` | Update intake fields; resets to `needs_info` if required field cleared |
| `POST` | `/api/marketplace/sales/items/{id}/generate-draft` | Call `listing_gen` and persist result in `generated_draft` |
| `POST` | `/api/marketplace/sales/items/{id}/approve` | Dani approves draft → status `ready_to_publish` |
| `POST` | `/api/marketplace/sales/items/{id}/mark-sold` | Mark item sold (optional: `platform`, `price_chf`) |
| `POST` | `/api/marketplace/sales/items/{id}/archive` | Archive item |
| `POST` | `/api/marketplace/sales/items/{id}/platform-listings` | Create platform listing record (status=`draft`) |
| `PATCH` | `/api/marketplace/sales/items/{id}/platform-listings/{lid}` | Update platform listing (e.g. set `published`, add `external_listing_id`) |

### Phase 2+ endpoints (design only)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/marketplace/sales/items/{id}/photos` | Upload/register a photo |
| `GET` | `/api/marketplace/sales/buyer-questions` | List pending buyer questions |
| `POST` | `/api/marketplace/sales/buyer-questions/{id}/reply` | Send reply (requires Dani approval token) |

### Response shape (item)

```json
{
  "id": "uuid",
  "title": "Bosch Staubsauger BSG6...",
  "condition": "very_good",
  "asking_price_chf": 35.00,
  "status": "draft_ready",
  "intake_source": "telegram",
  "generated_draft": { "title": "...", "description": "..." },
  "photos": [],
  "platform_listings": [
    { "platform": "tutti", "status": "draft", "listed_price_chf": 35.00 }
  ],
  "created_at": "2026-04-30T14:00:00Z",
  "updated_at": "2026-04-30T14:05:00Z"
}
```

---

## 5. Frontend route proposal

### New routes

| Route | Purpose |
|---|---|
| `/marketplace/sales/items` | Item list — kanban or table view grouped by status |
| `/marketplace/sales/items/[id]` | Item detail — intake form + draft panel + platform listings |
| `/marketplace/sales/items/new` | Start a new intake (web path; Telegram path uses bot) |

### `/marketplace/sales/items` (list view)

- Status columns: `needs_info` / `draft_ready` / `ready_to_publish` / `published` / `sold`
- Each card: item title, condition badge, price, photo count, platform listing status chips
- "New item" button → `/marketplace/sales/items/new`
- Filter bar: status, platform

### `/marketplace/sales/items/[id]` (detail view)

Tabs:

1. **Intake** — editable form for the 5 intake fields; save triggers PATCH
2. **Draft** — generated listing draft with RicardoDraftPanel and per-field copy buttons
3. **Platforms** — list of platform listing records with status badges; "Mark as published" / "Mark as sold" actions
4. **Photos** — (Phase 2) photo gallery with sort/delete

### Integration with existing `/marketplace/sales`

The existing page (`/marketplace/sales`) remains as the entry hub. Add a new section at the top:

```
[ Active Items (3) ]  →  /marketplace/sales/items
```

This keeps the existing listing generator form and pipeline UI untouched.

---

## 6. Telegram intake integration plan

### Current flow (stateless)

```
Dani: "vende eso" or photo
Bot: returns 5-question intake text
Dani: answers in free text (one message)
Bot: calls generate-listing → returns draft
```

### Proposed persistent flow (Phase 1.5)

```
Dani: "vende eso" or photo
Bot: calls POST /api/marketplace/sales/items  ← creates item, status=needs_info
     returns item_id + 5-question intake text

Dani: answers intake (one message or step by step)
Bot: calls PATCH /api/marketplace/sales/items/{id} with parsed fields
     if all 5 present → calls POST /api/marketplace/sales/items/{id}/generate-draft
     returns draft + link to web UI for full review

Dani: reviews on web or approves via Telegram
Bot: calls POST /api/marketplace/sales/items/{id}/approve → status=ready_to_publish
```

### Intake parsing

The bot can parse a single free-text intake reply with a lightweight prompt:

```
Extract from user reply:
1. item_name
2. condition (map to: new / like_new / very_good / good / with_defects)
3. price_chf (number only)
4. pickup_location + shipping (bool)
5. defects_notes
Return JSON. If field missing, return null for that field.
```

Missing fields leave `status=needs_info`; bot asks follow-up for each null field.

### Photo handling

When Dani sends a photo:
- Bot stores `telegram_file_id` via `POST /api/marketplace/sales/items/{id}/photos`
- VPS downloads the file async and updates `storage_path`
- Photo download is non-blocking and must not fail the intake flow

### Session state in Telegram

The bot must track which `item_id` the current Telegram conversation is "about" to route follow-up messages. Options:

| Option | Complexity | Notes |
|---|---|---|
| `context.user_data["active_item_id"]` | Low | Lost on bot restart; acceptable for Phase 1 |
| DB `telegram_sessions` table | Medium | Survives restarts; needed for Phase 2 |
| Redis key `telegram:active_item:{chat_id}` | Low-Medium | Fast; TTL handles cleanup |

**Recommendation for Phase 1:** `context.user_data["active_item_id"]` — zero DB cost, sufficient until Phase 2.

---

## 7. Guardrails

These constraints must be enforced at the API layer, not only the bot layer.

### Immutable rules (enforced in endpoint logic)

- `status` can only advance via the defined transitions above — no arbitrary writes
- `status=ready_to_publish` requires `title`, `condition`, `asking_price_chf`, and `pickup_location` to be non-null
- `sales_platform_listings.status=published` requires a matching `sales_items.status ∈ {ready_to_publish, published}`
- `buyer_questions.status=replied` requires `reply_text` non-null and a `sent_by` value
- No platform listing can have `status=published` without `listed_price_chf`

### PII handling

- `pickup_location` stores city/canton only — never full street address
- `telegram_chat_id` stored for routing only — never included in listing content or AI prompts
- `buyer_questions` rows excluded from `agent_runs` log payloads (masked in observability)

### No auto-publish guarantee

- No endpoint writes `platform_listings.status=published` without an explicit `POST .../approve` or `POST .../platform-listings/{lid}` call with a status body
- The `generate-draft` endpoint only updates `generated_draft` JSONB — it does not change item status or platform status
- All status-advancing writes are logged to `agent_runs` with `agent_name="sales_item_api"` and `triggered_by="dani"`

---

## 8. Alembic migration plan

New migration file: `backend/db/versions/xxxx_add_sales_tables.py`

```
add_sales_tables
├── create table sales_items
├── create table sales_item_photos (FK → sales_items)
├── create table sales_platform_listings (FK → sales_items)
├── create index sales_items_status_idx ON sales_items(status)
├── create index sales_items_created_at_idx ON sales_items(created_at DESC)
└── create index platform_listings_item_id_idx ON sales_platform_listings(item_id)
```

`buyer_questions` deferred to a separate migration in Phase 2.

---

## 9. Phased implementation mini-sprints

### Sprint 28 — DB + API skeleton

- Create `backend/models/sales.py` with `SalesItem`, `SalesItemPhoto`, `SalesPlatformListing`
- Create Alembic migration
- Create `backend/api/marketplace/sales_items.py` with POST + GET + PATCH item endpoints
- Add router to `backend/main.py`
- Write `backend/tests/test_sales_items.py` (create, update, status transition guard)
- No Telegram changes. No frontend changes.

### Sprint 29 — Telegram integration (Phase 1.5)

- Add `active_item_id` tracking to `context.user_data` in `bot.py`
- Update `handle_photo` and `handle_text_message` to create item via API
- Add intake-parser prompt to `backend/prompts/sales_intake_parser.txt`
- Add `POST /api/marketplace/sales/items/{id}/generate-draft` endpoint
- End-to-end test: Telegram → item created → draft generated

### Sprint 30 — Frontend items list + detail

- Create `/marketplace/sales/items/page.tsx` (list view)
- Create `/marketplace/sales/items/[id]/page.tsx` (detail view, Intake + Draft tabs)
- Add "Active Items" entry point to existing `/marketplace/sales` page
- No new API endpoints needed (uses Sprint 28 API)

### Sprint 31 — Platform listings UI + mark-sold flow

- Add Platforms tab to item detail page
- Implement "Mark as published" and "Mark as sold" actions
- Update item list to show sold/archived counts
- Add `GET /api/marketplace/sales/items?status=sold` summary to observability

### Sprint 32+ — Buyer questions (Phase 2, design only for now)

- `buyer_questions` migration
- Ricardo Q&A poll or webhook
- Telegram routing for buyer questions
- Requires Phase 3 (OAuth) to be functional end-to-end

---

## 10. What is explicitly out of scope

- No auto-publish logic at any phase
- No Ricardo credentials stored — Phase 1 remains manual copy
- No photo download in Sprint 28 (stored as `telegram_file_id` only)
- No buyer question handling before Sprint 32
- No price negotiation automation ever
- No meeting/pickup arrangement automation ever
