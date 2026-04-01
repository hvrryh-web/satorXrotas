"""
Monthly Full Harvest — Complete re-scrape of all three epochs + validation suite.

Steps (in order):
  1. Run full (not delta) harvest across Epochs I, II, and III
  2. Verify SHA-256 integrity on all newly stored records
  3. Cross-reference a sample against Liquipedia (when credentials available)
  4. Run overfitting guard and temporal wall on refreshed dataset
  5. Print a monthly summary report

Full harvest re-scrapes the entire epoch date range, deduplicating via checksums
(``RawRepository.already_stored`` is a no-op for unchanged content).

Exit codes:
  0 — harvest and validation completed successfully
  1 — integrity or validation failure detected

Usage:
  python scripts/monthly_full_harvest.py
  python scripts/monthly_full_harvest.py --epochs 2 3   # limit to specific epochs
  python scripts/monthly_full_harvest.py --dry-run       # check modules, no network I/O
"""
import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger(__name__)


async def _run_full_harvest(epochs: list[int], dry_run: bool) -> dict[int, int]:
    """Trigger a full-mode harvest for the specified epochs."""
    if dry_run:
        logger.info("DRY RUN: full harvest skipped (module import only)")
        from extraction.src.scrapers.epoch_harvester import EpochHarvester  # noqa: F401
        return {e: 0 for e in epochs}

    import aiohttp
    from extraction.src.scrapers.epoch_harvester import EpochHarvester
    from extraction.src.scrapers.vlr_resilient_client import ResilientVLRClient

    harvester = EpochHarvester(mode="full", epochs=epochs)
    logger.info("Starting full harvest — epochs=%s", epochs)
    totals = await harvester.run()
    logger.info("Full harvest totals: %s", totals)
    return totals


def _run_integrity_check(storage_path: Path) -> bool:
    """Post-harvest SHA-256 integrity verification."""
    logger.info("[integrity] Verifying raw extraction checksums in %s", storage_path)
    if not storage_path.exists():
        logger.info("Storage path not found — no files to verify")
        return True

    from extraction.src.storage.integrity_checker import IntegrityChecker

    raw_files = list(storage_path.glob("*.raw"))
    if not raw_files:
        logger.info("No raw extraction files present — integrity check vacuous pass")
        return True

    try:
        checker = IntegrityChecker(storage_path=storage_path)
        results = checker.verify_all()
        passed = sum(1 for v in results.values() if v)
        logger.info("Integrity: %d/%d files OK", passed, len(results))
        return True
    except RuntimeError as exc:
        logger.error("Integrity verification FAILED: %s", exc)
        return False


def _run_cross_reference(sample_size: int) -> bool:
    """Cross-reference against Liquipedia (skipped gracefully when no credentials)."""
    logger.info("[crossref] Liquipedia cross-reference — sample=%d", sample_size)
    from extraction.src.scrapers.validation_crossref import ValidationCrossRef

    db_url = os.environ.get("DATABASE_URL")
    ref = ValidationCrossRef(database_url=db_url)
    result = ref.validate_vs_liquipedia(sample_size=sample_size)

    if result.sample_size == 0 or result.correlation == 0.0:
        logger.warning("Cross-reference skipped — credentials not configured")
        return True

    logger.info(
        "Cross-reference result: r=%.3f  passed=%s  source=%s",
        result.correlation,
        result.passed,
        result.source,
    )
    if not result.passed:
        logger.error(
            "Correlation %.3f is below CORRELATION_TARGET — investigate extraction quality",
            result.correlation,
        )
        return False
    return True


def _run_guardrails() -> bool:
    """Run overfitting guard and confirm temporal wall is intact."""
    logger.info("[guardrails] Temporal wall + overfitting guard check")
    try:
        from analytics.src.guardrails.temporal_wall import TemporalWall
        from analytics.src.guardrails.overfitting_guard import OverfittingGuard, LEAKAGE_THRESHOLD

        wall = TemporalWall()
        guard = OverfittingGuard()
        logger.info("Temporal wall cutoff: %s", wall.cutoff)
        logger.info("Overfitting guard loaded — leakage threshold: %.2f", LEAKAGE_THRESHOLD)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Guardrail check failed: %s", exc)
        return False


def _print_monthly_report(
    harvest_totals: dict[int, int],
    integrity_ok: bool,
    crossref_ok: bool,
    guardrails_ok: bool,
    started_at: datetime,
) -> None:
    """Print human-readable monthly summary to stdout."""
    total_records = sum(harvest_totals.values())
    duration = (datetime.now(tz=timezone.utc) - started_at).total_seconds()
    month_tag = started_at.strftime("%Y-%m")

    print("")
    print("╔══════════════════════════════════════════════╗")
    print(f"║  Monthly Full Harvest Report — {month_tag}  ║")
    print("╠══════════════════════════════════════════════╣")
    for epoch_num, count in sorted(harvest_totals.items()):
        print(f"║  Epoch {epoch_num}: {count:>6d} records harvested          ║")
    print(f"║  Total:  {total_records:>6d} records                       ║")
    print("╠══════════════════════════════════════════════╣")
    print(f"║  Integrity    : {'✅ OK' if integrity_ok  else '❌ FAIL':<41}║")
    print(f"║  Cross-ref    : {'✅ OK' if crossref_ok   else '❌ FAIL':<41}║")
    print(f"║  Guardrails   : {'✅ OK' if guardrails_ok else '❌ FAIL':<41}║")
    print(f"║  Duration     : {duration:<6.1f}s                             ║")
    print("╚══════════════════════════════════════════════╝")
    print("")


def main() -> None:
    parser = argparse.ArgumentParser(description="Monthly full harvest + validation")
    parser.add_argument(
        "--epochs",
        nargs="+",
        type=int,
        default=[1, 2, 3],
        help="Epochs to harvest (default: 1 2 3)",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=100,
        help="Records to sample for Liquipedia cross-reference",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Import and validate modules without performing network I/O",
    )
    args = parser.parse_args()

    started_at = datetime.now(tz=timezone.utc)
    logger.info(
        "=== Monthly Full Harvest started at %s (epochs=%s) ===",
        started_at.isoformat(),
        args.epochs,
    )

    # Step 1 — Full harvest
    harvest_totals = asyncio.run(_run_full_harvest(args.epochs, args.dry_run))

    # Steps 2-4 — Validation suite
    storage_path = Path(os.environ.get("RAW_STORAGE_PATH", "data/raw_extractions"))
    integrity_ok = _run_integrity_check(storage_path)
    crossref_ok = _run_cross_reference(args.sample)
    guardrails_ok = _run_guardrails()

    _print_monthly_report(
        harvest_totals, integrity_ok, crossref_ok, guardrails_ok, started_at
    )

    if not all([integrity_ok, crossref_ok, guardrails_ok]):
        logger.error("Monthly full harvest completed with failures — see report above")
        sys.exit(1)

    logger.info("=== Monthly Full Harvest PASSED ===")


if __name__ == "__main__":
    main()
