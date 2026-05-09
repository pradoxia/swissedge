"""
Command definitions for the SwissEdge Telegram bot.
Each entry describes the command for BotFather registration.
"""

COMMANDS = [
    ("start", "Start the SwissEdge assistant"),
    ("sell", "Sell an item — send a photo and description"),
    ("search", "Search for deals on Swiss marketplaces"),
    ("situations", "View detected special situations"),
    ("watchlist", "View your investment watchlist"),
    ("doctor", "Run a system health check"),
    ("missioncontrol", "Mission Control — estado de todos los agentes"),
    ("control", "Alias: Mission Control"),
    ("agentes", "Lista de todos los agentes"),
    ("agente", "Detalle de un agente: /agente marketplace_lister"),
    ("cron", "Próximos cron jobs (3 días)"),
    ("costes", "Resumen de costes y runs"),
    ("errores", "Últimos errores del sistema"),
    ("help", "Show available commands"),
]

HELP_TEXT = """
*SwissEdge Assistant* 🇨🇭

*Marketplace*
/sell — Sell an item (send photo + description)
/search <item> — Find deals on Tutti.ch

*Investment Radar*
/situations — View detected special situations
/watchlist — Your watchlist

*Sistema*
/doctor — Health check
/missioncontrol — Mission Control (todos los agentes)
/control — Alias de /missioncontrol
/agentes — Lista de agentes con estado
/agente <nombre> — Detalle de un agente
/cron — Próximos cron jobs (3 días)
/costes — Resumen de costes IA
/errores — Últimos errores

/help — This message

⚠️ All investment information is educational only. Not financial advice.
""".strip()
