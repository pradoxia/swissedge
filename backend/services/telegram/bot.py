"""
SwissEdge Telegram Bot.

Architecture choice: This bot runs standalone (not via OpenClaw) for maximum control.
OpenClaw remains the brain for cron scheduling; the bot handles the Telegram conversation.

To run: python -m backend.services.telegram.bot
"""

import logging
import httpx
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from backend.config import get_settings
from backend.services.telegram.commands import COMMANDS, HELP_TEXT
from backend.services.telegram.safety import validate_outgoing_message

logger = logging.getLogger(__name__)

BACKEND_URL = "http://localhost:8000"


async def _safe_reply(update: Update, text: str) -> None:
    """Send a reply after passing safety validation."""
    is_safe, violations = validate_outgoing_message(text)
    if not is_safe:
        logger.warning("Safety check failed: %s", violations)
        await update.message.reply_text(
            "⚠️ Die Nachricht konnte nicht gesendet werden (Sicherheitsprüfung)."
        )
        return
    await update.message.reply_text(text, parse_mode="Markdown")


# ── command handlers ──────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _safe_reply(
        update,
        "👋 Willkommen bei *SwissEdge*!\n\n"
        "Ich helfe dir beim Verkaufen auf Schweizer Marktplätzen "
        "und beim Finden von Investment-Situationen.\n\n"
        "Tippe /help für alle Befehle.",
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _safe_reply(update, HELP_TEXT)


async def cmd_sell(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _safe_reply(
        update,
        "📸 Schick mir ein *Foto* deines Artikels mit einer kurzen Beschreibung.\n"
        "Ich erstelle dann einen Inserat-Entwurf auf Hochdeutsch.",
    )


async def cmd_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = " ".join(context.args) if context.args else ""
    if not query:
        await _safe_reply(update, "🔍 Was suchst du? Beispiel: `/search PS5`")
        return

    await update.message.reply_text(f"🔍 Suche nach *{query}*...", parse_mode="Markdown")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{BACKEND_URL}/api/marketplace/search",
                json={"query": query, "limit": 5},
            )
            data = resp.json()
    except Exception as e:
        await _safe_reply(update, f"❌ Fehler bei der Suche: {e}")
        return

    listings = data.get("listings", [])
    if not listings:
        await _safe_reply(update, f"Keine Ergebnisse für *{query}* gefunden.")
        return

    lines = [f"🛍 *{query}* — {data['count']} Ergebnis(se):\n"]
    for i, l in enumerate(listings[:5], 1):
        price_str = f"CHF {l['price']:.0f}" if l.get("price") else "Preis unbekannt"
        lines.append(f"{i}. {l['title']} — {price_str}")
        if l.get("url"):
            lines.append(f"   [Anzeige ansehen]({l['url']})")
    await _safe_reply(update, "\n".join(lines))


async def cmd_situations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{BACKEND_URL}/api/investment/situations")
            data = resp.json()
    except Exception as e:
        await _safe_reply(update, f"❌ Fehler: {e}")
        return

    situations = data.get("situations", [])
    if not situations:
        await _safe_reply(update, "Keine Situationen gefunden. Scan noch nicht gelaufen.")
        return

    lines = [f"📊 *{data['count']} Situation(en) entdeckt:*\n"]
    for s in situations[:5]:
        status_emoji = {"detected": "🔵", "watchlist": "👁", "active": "🟢", "passed": "⚪"}.get(s["status"], "⚫")
        lines.append(f"{status_emoji} *{s['company_name']}* ({s['situation_type']})")
        lines.append(f"   Status: {s['status']} | Filing: {s.get('filing_type', '-')}")
    lines.append("\n⚠️ _Not financial advice. Educational purposes only._")
    await _safe_reply(update, "\n".join(lines))


async def cmd_doctor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🩺 Systemcheck läuft...")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{BACKEND_URL}/api/health/full")
            report = resp.json()
    except Exception as e:
        await _safe_reply(update, f"❌ Backend nicht erreichbar: {e}")
        return

    icons = {"ok": "✅", "warning": "⚠️", "error": "❌"}
    lines = [f"🩺 *SwissEdge Health* — {report['status'].upper()}\n"]
    for c in report["components"]:
        icon = icons.get(c["status"], "❓")
        lines.append(f"{icon} {c['name']}: {c['message']}")
    summary = report["summary"]
    lines.append(f"\n{summary['ok']} ok · {summary['warning']} warn · {summary['error']} err")
    await _safe_reply(update, "\n".join(lines))


async def cmd_missioncontrol(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🤖 Cargando Mission Control...")
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(f"{BACKEND_URL}/api/observability/mission-control/text")
            resp.raise_for_status()
            text = resp.text
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return
    if len(text) > 4000:
        text = text[:4000] + "\n...[truncado]"
    await update.message.reply_text(text)


async def cmd_agentes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{BACKEND_URL}/api/observability/agents")
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return

    status_icons = {"active": "✅", "partial": "⚠️", "pending": "🔵", "future": "⚙️"}
    lines = [f"🤖 *Agentes SwissEdge* ({data['count']} total)\n"]
    for a in data["agents"]:
        icon = status_icons.get(a["current_status"], "❓")
        run_info = f"runs={a['total_runs']}"
        if a["failed_runs"]:
            run_info += f" fallos={a['failed_runs']}"
        lines.append(f"{icon} `{a['agent_name']}` — {a['current_status']} ({run_info})")
        if a.get("last_outcome"):
            lines.append(f"   ↳ {a['last_outcome'][:60]}")
        for w in a.get("warnings", [])[:1]:
            lines.append(f"   ⚠️ {w[:70]}")
    await _safe_reply(update, "\n".join(lines))


async def cmd_agente(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "Uso: /agente <nombre>\nEjemplo: /agente marketplace\\_lister"
        )
        return
    name = context.args[0]
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{BACKEND_URL}/api/observability/agents/{name}/text")
            if resp.status_code == 404:
                await update.message.reply_text(f"❌ Agente '{name}' no registrado.")
                return
            resp.raise_for_status()
            text = resp.text
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return
    if len(text) > 4000:
        text = text[:4000] + "\n...[truncado]"
    await update.message.reply_text(text)


async def cmd_cron(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{BACKEND_URL}/api/observability/cron/upcoming/text?days=3"
            )
            resp.raise_for_status()
            text = resp.text
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return
    if len(text) > 4000:
        text = text[:4000] + "\n...[truncado]"
    await update.message.reply_text(text)


async def cmd_costes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{BACKEND_URL}/api/observability/summary")
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return

    sr = data.get("success_rate")
    sr_str = f"{sr * 100:.1f}%" if sr is not None else "N/A"
    lines = [
        "💰 *Costes SwissEdge*\n",
        f"Total runs: {data['total_runs']}",
        f"Fallos: {data['failed_runs']}",
        f"Tasa éxito: {sr_str}",
        f"Coste total IA: ${data['total_ai_cost_usd']:.4f}",
        f"Aprobaciones pendientes: {data['pending_human_approvals']}",
        "",
        "*Top agentes:*",
    ]
    for i, a in enumerate(data.get("top_agents", [])[:5], 1):
        lines.append(f"{i}. `{a['agent_name']}` — {a['run_count']} runs")
    await _safe_reply(update, "\n".join(lines))


async def cmd_errores(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{BACKEND_URL}/api/observability/runs?status=failed&limit=10"
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return

    runs = data.get("runs", [])
    if not runs:
        await _safe_reply(update, "✅ No hay errores recientes.")
        return

    lines = [f"❌ *Últimos errores* ({len(runs)})\n"]
    for r in runs:
        ts = (r.get("started_at") or "")[:16]
        lines.append(f"🔴 `{r['agent_name']}` — {ts}")
        if r.get("error_message"):
            lines.append(f"   {r['error_message'][:100]}")
    await _safe_reply(update, "\n".join(lines))


FRONTEND_BASE_URL = "http://100.73.109.52:3001"


async def _create_sales_item(
    chat_id: str,
    message_id: str | None,
    hint: str | None,
    photo_file_id: str | None,
) -> dict | None:
    payload: dict = {
        "created_from": "telegram",
        "telegram_chat_id": chat_id,
    }
    if message_id:
        payload["telegram_message_id"] = message_id
    if hint:
        payload["brand_model"] = hint[:200]
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{BACKEND_URL}/api/marketplace/sales/items",
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.warning("Failed to create SalesItem: %s", e)
        return None


SALES_INTAKE_RESPONSE = (
    "Perfecto, preparo una venta asistida. 🇨🇭\n\n"
    "No publicaré nada sin tu confirmación.\n\n"
    "Para hacer un buen anuncio en *Ricardo / Tutti / Anibis* necesito:\n"
    "1️⃣ ¿Qué es exactamente el artículo?\n"
    "2️⃣ Estado: nuevo / como nuevo / muy bueno / bueno / con defectos\n"
    "3️⃣ Precio deseado en CHF\n"
    "4️⃣ Recogida o envío (y desde dónde)\n"
    "5️⃣ Defectos, accesorios o detalles importantes\n\n"
    "_Sin confirmación tuya no publico nada._"
)

SALES_TRIGGERS = {
    "vende eso", "vende esto", "ponlo a la venta", "ponla a la venta",
    "quiero vender esto", "quiero vender eso", "sell this", "sell that",
    "vender esto", "vender eso",
}


def _is_sales_intent(text: str) -> bool:
    t = text.strip().lower()
    if t in SALES_TRIGGERS:
        return True
    sales_verbs = ("vende ", "vender ", "sell ", "ponlo a la venta", "ponla a la venta", "quiero vender")
    return any(t.startswith(v) for v in sales_verbs)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming photos — enter sales intake mode and create persistent SalesItem."""
    caption = (update.message.caption or "").strip()
    chat_id = str(update.effective_chat.id)
    message_id = str(update.message.message_id)
    photo = update.message.photo[-1] if update.message.photo else None
    photo_file_id = photo.file_id if photo else None

    if _is_sales_intent(caption) or not caption:
        hint = None
        if caption and _is_sales_intent(caption):
            words = caption.split()
            if len(words) > 2:
                hint = " ".join(words[2:])

        item = await _create_sales_item(chat_id, message_id, hint, photo_file_id)
        context.user_data["active_item_id"] = item["id"] if item else None

        item_link = (
            f"\n\n🔗 [Ver item]({FRONTEND_BASE_URL}/marketplace/sales/items/{item['id']})"
            if item else ""
        )
        await _safe_reply(
            update,
            "📸 He recibido la foto.\n\n" + SALES_INTAKE_RESPONSE + item_link,
        )
        return

    await update.message.reply_text("⏳ Erstelle Inserat-Entwurf...")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{BACKEND_URL}/api/marketplace/generate-listing",
                json={"item_description": caption},
            )
            data = resp.json()
    except Exception as e:
        await _safe_reply(update, f"❌ Fehler: {e}")
        return

    title = data.get("title", "")
    description = data.get("description", "")
    msg = (
        f"📝 *Inserat-Entwurf*\n\n"
        f"*Titel:* {title}\n\n"
        f"*Beschreibung:*\n{description}\n\n"
        f"✏️ Bitte überprüfe und kopiere den Text auf Tutti.ch."
    )
    await _safe_reply(update, msg)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Catch free-text sales intent phrases."""
    text = (update.message.text or "").strip()
    if _is_sales_intent(text):
        chat_id = str(update.effective_chat.id)
        message_id = str(update.message.message_id)
        words = text.split()
        hint = " ".join(words[2:]) if len(words) > 2 else None

        item = await _create_sales_item(chat_id, message_id, hint, None)
        context.user_data["active_item_id"] = item["id"] if item else None

        item_link = (
            f"\n\n🔗 [Ver item]({FRONTEND_BASE_URL}/marketplace/sales/items/{item['id']})"
            if item else ""
        )
        await _safe_reply(update, SALES_INTAKE_RESPONSE + item_link)
        return


# ── app setup ─────────────────────────────────────────────────────────────────

def build_app() -> Application:
    settings = get_settings()
    app = Application.builder().token(settings.telegram_bot_token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("sell", cmd_sell))
    app.add_handler(CommandHandler("search", cmd_search))
    app.add_handler(CommandHandler("situations", cmd_situations))
    app.add_handler(CommandHandler("watchlist", cmd_situations))
    app.add_handler(CommandHandler("doctor", cmd_doctor))
    app.add_handler(CommandHandler("missioncontrol", cmd_missioncontrol))
    app.add_handler(CommandHandler("control", cmd_missioncontrol))
    app.add_handler(CommandHandler("agentes", cmd_agentes))
    app.add_handler(CommandHandler("agente", cmd_agente))
    app.add_handler(CommandHandler("cron", cmd_cron))
    app.add_handler(CommandHandler("costes", cmd_costes))
    app.add_handler(CommandHandler("errores", cmd_errores))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    return app


async def set_commands(app: Application) -> None:
    await app.bot.set_my_commands([BotCommand(cmd, desc) for cmd, desc in COMMANDS])


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    application = build_app()
    application.run_polling(allowed_updates=Update.ALL_TYPES)
