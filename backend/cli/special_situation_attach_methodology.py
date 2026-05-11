"""Attach methodology workspaces to existing SEC-detected SpecialSituations.

Dry-run:
    python -m backend.cli.special_situation_attach_methodology --dry-run

Apply:
    python -m backend.cli.special_situation_attach_methodology --apply
"""

from __future__ import annotations

import argparse
import asyncio
import json

from backend.db.database import AsyncSessionLocal
from backend.services.investment.methodology_workspace import attach_methodology_workspace_backfill


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Attach methodology workspaces to SEC-detected SpecialSituations.")
    parser.add_argument("--dry-run", action="store_true", help="List matched records without writing. Default behavior.")
    parser.add_argument("--apply", action="store_true", help="Attach workspace snapshots to matched records.")
    return parser.parse_args()


async def _main() -> None:
    args = _parse_args()
    async with AsyncSessionLocal() as db:
        summary = await attach_methodology_workspace_backfill(db, apply=bool(args.apply))
        if args.apply:
            await db.commit()
        print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(_main())
