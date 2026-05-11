"""Manual cleanup for historical SEC false detections from Sprint Q validation.

Run dry-run first:
    python -m backend.cli.sec_edgar_cleanup_false_detections --dry-run

Delete requires explicit confirmation:
    python -m backend.cli.sec_edgar_cleanup_false_detections --delete --confirm DELETE_FALSE_SEC_DETECTIONS
"""

from __future__ import annotations

import argparse
import asyncio
import json

from backend.db.database import AsyncSessionLocal
from backend.services.investment.sec_false_detection_cleanup import run_false_detection_cleanup


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean up historical SEC false detections.")
    parser.add_argument("--dry-run", action="store_true", help="List matched records without deleting. Default behavior.")
    parser.add_argument("--delete", action="store_true", help="Delete matched false detections.")
    parser.add_argument("--confirm", help="Required confirmation token for --delete.")
    return parser.parse_args()


async def _main() -> None:
    args = _parse_args()
    delete = bool(args.delete)
    async with AsyncSessionLocal() as db:
        summary = await run_false_detection_cleanup(
            db,
            delete=delete,
            confirm=args.confirm,
        )
        if delete and not summary.get("error"):
            await db.commit()
        print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(_main())
