"""Manual SEC EDGAR detection core for Sprint Q.

Run with:
    python -m backend.cli.sec_edgar_detect --hours-back 36 --dry-run

This command does not call the evaluator, does not create ResearchCases, and
does not trigger /api/investment/scan.
"""

from __future__ import annotations

import argparse
import asyncio
import json

from backend.db.database import AsyncSessionLocal
from backend.services.investment.sec_detection import run_sec_edgar_detection


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run manual SEC EDGAR detection.")
    parser.add_argument("--hours-back", type=int, default=36, help="Lookback window in hours.")
    parser.add_argument("--dry-run", action="store_true", help="Fetch/classify only; do not write DB rows.")
    return parser.parse_args()


async def _main() -> None:
    args = _parse_args()
    async with AsyncSessionLocal() as db:
        summary = await run_sec_edgar_detection(
            db,
            hours_back=args.hours_back,
            dry_run=args.dry_run,
        )
        if not args.dry_run:
            await db.commit()
        print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(_main())
