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

*System*
/doctor — Health check
/help — This message

⚠️ All investment information is educational only. Not financial advice.
""".strip()
