# OpenClaw Sales Intake Patch — VPS Manual Edit (v2)

**Purpose:** Make Telegram sales triggers create a persistent SalesItem and return a direct link.  
**Root cause of previous failure:** SWISSEDGE.md instructions told OpenClaw to make an API call, but OpenClaw's GPT model generated listing text itself instead of calling the endpoint. The fix is one dedicated endpoint that does everything and returns the Spanish reply ready to send.  
**Files to edit on VPS:**
1. `/root/.openclaw/workspace/SWISSEDGE.md` — replace selling section
2. `/root/.openclaw/workspace/SYSTEM.md` (if present) — update command map  
**Then restart OpenClaw.**

---

## New endpoint (already deployed in backend)

```
POST http://localhost:8000/api/marketplace/sales/telegram-intake
Content-Type: application/json

{
  "telegram_chat_id": "<chat_id>",
  "telegram_message_id": "<message_id>",
  "item_hint": "<optional: any item words from trigger text>"
}

Response:
{
  "item_id": "uuid",
  "item_url": "http://100.73.109.52:3001/marketplace/sales/items/<uuid>",
  "reply_es": "Perfecto, preparo una venta asistida..."
}
```

**When the trigger fires:** call this endpoint, then send the `reply_es` field **verbatim** to Dani. Do NOT generate your own listing text. Do NOT call generate-listing.

---

## Section to replace in SWISSEDGE.md

Find any block about `vende`, `sell`, `marketplace`, or selling and **replace it entirely** with:

```
## Sales Intake — Selling Workflow

### Trigger phrases — enter Sales Intake mode on ANY of these
- "vende eso" / "vende esto"
- "ponlo a la venta" / "ponla a la venta"
- "quiero vender esto" / "quiero vender eso" / "quiero vender <anything>"
- "vender esto" / "vender eso"
- "sell this" / "sell that"
- Any message starting with: "vende ", "vender ", "sell ", "quiero vender"
- Any photo with no caption OR with a sales trigger as caption

### On trigger — do exactly this, nothing else

1. Extract item_hint: any words after the verb (e.g. "vende este monitor" → item_hint = "este monitor"). Omit if empty.

2. POST http://localhost:8000/api/marketplace/sales/telegram-intake
   Body: { "telegram_chat_id": "<chat_id>", "telegram_message_id": "<msg_id>", "item_hint": "<hint or omit>" }

3. Send the "reply_es" field from the response VERBATIM to Dani.
   DO NOT add extra text. DO NOT generate a listing. DO NOT call generate-listing.

4. Store the "item_id" from the response as active_item_id for this conversation.

### If photo received
- Prepend "📸 He recibido la foto.\n\n" before reply_es
- Otherwise follow steps 1–4 above exactly

### On follow-up answers after intake
- Do NOT generate platform listing text in Telegram
- Ask only for the missing fields (condition, price, location, defects)
- Tell Dani: "Puedes ver y editar el borrador completo en: <item_url>"
- Platform texts (Ricardo, Tutti) belong in the web UI, not in Telegram

### Platforms — Switzerland only
- Ricardo.ch, Tutti.ch, Anibis.ch, Facebook Marketplace Switzerland
- NEVER: Wallapop, Milanuncios, eBay.es, non-Swiss platforms
- Currency always CHF

### Hard rules
- No auto-publish
- No buyer reply without Dani confirmation
- No meeting/pickup without Dani confirmation
- No PII (phone, address, IBAN) in replies
```

---

## How to apply on VPS

```bash
ssh swdeploy@100.73.109.52
sudo nano /root/.openclaw/workspace/SWISSEDGE.md
# Find and replace the selling/vende section with the block above
# Ctrl+O → Enter → Ctrl+X

# Restart OpenClaw
sudo systemctl restart openclaw
# or: pm2 restart openclaw
```

---

## Test after restart

1. Send `Vende eso` → bot should call telegram-intake endpoint, send reply_es (Spanish, 5 questions + link), nothing else
2. Send product photo (no caption) → same but prefixed with "📸 He recibido la foto."
3. `quiero vender este monitor` → item_hint = "este monitor"; reply includes link to /marketplace/sales/items/{id}
4. Check `/marketplace/sales/items` in browser — new item should appear with status `needs_info`

## What must NOT happen
- Bot generating German listing text (Titel/Beschreibung) in Telegram
- Bot calling `/api/marketplace/generate-listing` on sales trigger
- Any mention of Wallapop / Milanuncios
- Auto-publish or auto-listing


**Purpose:** Fix wrong Wallapop/image-analysis response when Dani sends "vende eso" or a product photo.  
**Also:** Create a persistent SalesItem via backend API and return a direct link.  
**File to edit on VPS:** `/root/.openclaw/workspace/SWISSEDGE.md`  
**How:** SSH into VPS, open the file, find the Marketplace / selling section, and **replace or add** the block below.

---

## Section to add/replace in SWISSEDGE.md

Find any existing block about `vende`, `sell`, `marketplace`, or photo handling and **replace it entirely** with:

```
## Sales Intake — Selling Workflow

### Trigger phrases (any of these = enter Sales Intake mode)
- "vende eso"
- "vende esto"
- "ponlo a la venta" / "ponla a la venta"
- "quiero vender esto" / "quiero vender eso"
- "vender esto" / "vender eso"
- "sell this" / "sell that"
- Any message starting with: "vende ", "vender ", "sell ", "quiero vender"

### Also trigger on:
- Any photo sent with no caption, or with a sales trigger as caption

### Step 1 — Create a SalesItem in the backend (REQUIRED)

As soon as a sales trigger is detected, call:

POST http://localhost:8000/api/marketplace/sales/items
Content-Type: application/json

{
  "created_from": "telegram",
  "telegram_chat_id": "<chat_id>",
  "telegram_message_id": "<message_id>",
  "brand_model": "<any item hint extracted from the trigger text, or omit if none>"
}

The response will include an "id" field (UUID). Store it as active_item_id for this conversation.

If the POST fails, continue with the response anyway (do not block the user).

### Step 2 — Required response (in Spanish, always)

Perfecto, preparo una venta asistida. 🇨🇭

No publicaré nada sin tu confirmación.

Para hacer un buen anuncio en Ricardo / Tutti / Anibis necesito:
1. ¿Qué es exactamente el artículo?
2. Estado: nuevo / como nuevo / muy bueno / bueno / con defectos
3. Precio deseado en CHF
4. Recogida o envío (y desde dónde)
5. Defectos, accesorios o detalles importantes

🔗 Ver y editar: http://100.73.109.52:3001/marketplace/sales/items/<item_id>

Sin confirmación tuya no publico nada.

(Replace <item_id> with the id from the POST response. If POST failed, omit the link line.)

### If a photo is received
- Do NOT ask "do you want me to analyze the image?"
- Do NOT offer A/B image analysis options
- Treat it as a product photo
- Prepend "📸 He recibido la foto." before the intake response
- If you cannot read the image, say: "He recibido la foto. Para evitar errores, dime qué artículo es exactamente."
- Then give the intake response above including the item link

### Platforms — Switzerland only
- Always suggest: Ricardo.ch, Tutti.ch, Anibis.ch, Facebook Marketplace Switzerland
- NEVER mention: Wallapop, Milanuncios, eBay.es, or any non-Swiss platform
- Currency is always CHF

### Hard rules
- No auto-publish under any circumstance
- No buyer reply sent without Dani confirmation
- No pickup or meeting arranged without Dani confirmation
- PII (phone, address, IBAN) must never appear in bot replies
- AI image enhancement must not misrepresent item condition
```

---

## How to apply on VPS

```bash
# SSH into VPS
nano /root/.openclaw/workspace/SWISSEDGE.md
# Find marketplace/selling section → replace with block above
# Save: Ctrl+O, Enter, Ctrl+X

# Restart OpenClaw to reload the workspace file
sudo systemctl restart openclaw
# or if running via pm2:
pm2 restart openclaw
```

## Test messages Dani should send after restart

1. `Vende eso` → should POST to /api/marketplace/sales/items, respond with intake + link
2. Send a product photo (no caption) → "He recibido la foto..." + intake + link
3. Send a product photo with caption `vende esto` → same
4. `quiero vender este monitor` → intake response with "monitor" extracted as brand_model hint + link

## What should NOT appear after the fix
- Any mention of Wallapop or Milanuncios
- "Do you want me to analyze/describe the attached image?"
- Generic OpenClaw image analysis options
- Any suggestion of auto-publishing
- The link line if the backend POST failed (link is optional, not required)

## Backend endpoint reference

POST http://localhost:8000/api/marketplace/sales/items

Minimal body:
```json
{
  "created_from": "telegram",
  "telegram_chat_id": "string",
  "telegram_message_id": "string"
}
```

Optional fields: `brand_model` (item hint from trigger text), `title`, `condition`, `target_price_chf`, `pickup_location`

Response shape includes `id` (UUID string) — use this in the frontend link.
Status is always `needs_info` on creation unless all required fields are present.

