"""Manual Resource Scout v1 for SpecialSituations.

Single situation:
    python -m backend.cli.resource_scout_special_situation --situation-id <id> --dry-run
    python -m backend.cli.resource_scout_special_situation --situation-id <id> --apply

Limited batch:
    python -m backend.cli.resource_scout_special_situation --limit 5 --dry-run
    python -m backend.cli.resource_scout_special_situation --limit 5 --apply
"""

from __future__ import annotations

import argparse
import asyncio
import json

from backend.db.database import AsyncSessionLocal
from backend.services.investment.resource_scout import run_resource_scout


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run manual Resource Scout v1 for SpecialSituations.")
    parser.add_argument("--situation-id", help="Target a single SpecialSituation ID.")
    parser.add_argument("--limit", type=int, default=5, help="Batch limit when --situation-id is not provided. Max 25.")
    parser.add_argument("--dry-run", action="store_true", help="Preview resource candidates without writing. Default behavior.")
    parser.add_argument("--apply", action="store_true", help="Store resource candidates and search suggestions.")
    return parser.parse_args()


async def _main() -> None:
    args = _parse_args()
    async with AsyncSessionLocal() as db:
        summary = await run_resource_scout(
            db,
            situation_id=args.situation_id,
            limit=args.limit,
            apply=bool(args.apply),
        )
        if args.apply:
            await db.commit()
        print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(_main())
