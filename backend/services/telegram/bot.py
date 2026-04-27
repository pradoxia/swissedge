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


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming photos — Phase 1: use caption as description."""
    caption = update.message.caption or ""
    if not caption:
        await _safe_reply(
            update,
            "📸 Foto erhalten! Bitte füge eine *Beschreibung* als Bildunterschrift hinzu.\n"
            "Beispiel: 'Samsung Galaxy S23, sehr gut, 128GB'",
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
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    return app


async def set_commands(app: Application) -> None:
    await app.bot.set_my_commands([BotCommand(cmd, desc) for cmd, desc in COMMANDS])


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    application = build_app()
    application.run_polling(allowed_updates=Update.ALL_TYPES)
