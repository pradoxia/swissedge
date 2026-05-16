"""Manual SEC EDGAR detection core for Sprint Q.

Run with:
    python -m backend.cli.sec_edgar_detect --hours-back 36

Live-create mode requires explicit opt-in:
    python -m backend.cli.sec_edgar_detect --hours-back 36 --live-create

This command does not call the evaluator, does not create ResearchCases, and
does not trigger /api/investment/scan.
"""

from __future__ import annotations

import argparse
import asyncio
import json

from backend.db.database import AsyncSessionLocal
from backend.services.investment.sec_detection import run_sec_edgar_detection
from backend.services.investment.detection_run_service import DetectionRunService
from backend.services.investment.sources.sec_edgar import SECEdgarAdapter


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run manual SEC EDGAR detection.")
    parser.add_argument("--hours-back", type=int, default=36, help="Lookback window in hours.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        default=True,
        help="Fetch/classify only; do not write DB rows. This is the default.",
    )
    mode.add_argument(
        "--live-create",
        dest="dry_run",
        action="store_false",
        help="Explicitly allow SpecialSituation writes. Requires Dani approval before use.",
    )
    return parser.parse_args()


async def _main() -> None:
    args = _parse_args()
    logger = DetectionRunService()
    run_id = await logger.start_run(
        source="sec_edgar",
        hours_back=args.hours_back,
        dry_run=args.dry_run,
        forms_checked=list(SECEdgarAdapter.FILING_TYPES),
    )
    try:
        async with AsyncSessionLocal() as db:
            summary = await run_sec_edgar_detection(
                db,
                hours_back=args.hours_back,
                dry_run=args.dry_run,
            )
            if not args.dry_run:
                await db.commit()
            if summary.get("errors"):
                await logger.mark_partial(run_id, summary=summary, error_message="; ".join(summary["errors"]))
            else:
                await logger.mark_success(run_id, summary=summary)
            print(json.dumps(summary, indent=2, sort_keys=True))
    except Exception as exc:
        await logger.mark_failed(run_id, str(exc))
        raise


if __name__ == "__main__":
    asyncio.run(_main())
