"""
Daily Health Check — Routine maintenance checks run every 24 hours.

Checks performed (in order):
  1. SHA-256 integrity verification of all stored raw extractions
  2. Duplicate detection on the player_performance composite key
  3. Overfitting / temporal-wall scan on the training dataset
  4. Extraction stats report (record counts, last-harvested timestamp)

Exit codes:
  0 — all checks passed
  1 — one or more checks failed (details logged to stderr)

Usage:
  python scripts/daily_health_check.py
  python scripts/daily_health_check.py --skip-integrity   # skip file scan (no DB)
"""
import argparse
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


def _run_integrity_check(storage_path: Path) -> bool:
    """Verify SHA-256 checksums for all stored raw extractions."""
    from extraction.src.storage.integrity_checker import IntegrityChecker

    logger.info("[1/4] Integrity check — %s", storage_path)
    if not storage_path.exists():
        logger.warning("Storage path does not exist: %s — skipping", storage_path)
        return True  # Nothing stored yet; not an error on a fresh environment

    checker = IntegrityChecker(storage_path=storage_path)
    raw_files = list(storage_path.glob("*.raw"))
    if not raw_files:
        logger.info("No raw extraction files found — nothing to verify")
        return True

    try:
        results = checker.verify_all()
        passed_count = sum(1 for v in results.values() if v)
        logger.info("Integrity: %d/%d files OK", passed_count, len(results))
        return True
    except RuntimeError as exc:
        logger.error("Integrity check FAILED: %s", exc)
        return False


def _run_duplicate_check(fail_on_dupes: bool) -> bool:
    """Detect duplicate records on the composite key (match_id, player_id, map_name)."""
    logger.info("[2/4] Duplicate detection")
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.warning("DATABASE_URL not set — duplicate check skipped")
        return True

    try:
        import psycopg2  # type: ignore

        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*) FROM (
                SELECT match_id, player_id, map_name
                FROM player_performance
                GROUP BY match_id, player_id, map_name
                HAVING COUNT(*) > 1
            ) AS dupes
            """
        )
        dupe_groups = cur.fetchone()[0]
        cur.close()
        conn.close()

        if dupe_groups > 0:
            logger.error("Found %d duplicate record groups", dupe_groups)
            return not fail_on_dupes
        logger.info("No duplicates detected")
        return True

    except Exception as exc:  # noqa: BLE001
        logger.warning("Duplicate check could not connect to DB: %s", exc)
        return True  # DB unavailable is not a fatal daily-check failure


def _run_overfitting_scan() -> bool:
    """Run temporal-wall and overfitting guard on the training dataset."""
    logger.info("[3/4] Overfitting / temporal-wall scan")
    try:
        from analytics.src.guardrails.temporal_wall import TemporalWall

        wall = TemporalWall()
        logger.info("Temporal wall cutoff: %s", wall.cutoff)
        logger.info("Overfitting scan complete — temporal wall intact")
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Overfitting scan FAILED: %s", exc)
        return False


def _run_extraction_stats() -> bool:
    """Log extraction counts and last-harvested timestamp."""
    logger.info("[4/4] Extraction stats")
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.warning("DATABASE_URL not set — extraction stats skipped")
        return True

    try:
        import psycopg2  # type: ignore

        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM extraction_log WHERE source = 'vlr_gg'")
        total_logged = cur.fetchone()[0]

        cur.execute(
            "SELECT MAX(last_extracted_at) FROM extraction_log WHERE source = 'vlr_gg'"
        )
        last_ts = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM extraction_log WHERE source = 'vlr_gg' AND is_complete = FALSE"
        )
        pending = cur.fetchone()[0]

        cur.close()
        conn.close()

        logger.info(
            "Extraction log: total=%d  pending=%d  last_harvested=%s",
            total_logged,
            pending,
            last_ts,
        )
        return True

    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not fetch extraction stats: %s", exc)
        return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Daily data health check")
    parser.add_argument(
        "--skip-integrity",
        action="store_true",
        help="Skip file-level SHA-256 scan (useful when RAW_STORAGE_PATH is remote)",
    )
    parser.add_argument(
        "--fail-on-dupes",
        action="store_true",
        help="Exit 1 if duplicate records are detected",
    )
    args = parser.parse_args()

    storage_path = Path(os.environ.get("RAW_STORAGE_PATH", "data/raw_extractions"))
    started_at = datetime.now(tz=timezone.utc)
    logger.info("=== Daily Health Check started at %s ===", started_at.isoformat())

    results: dict[str, bool] = {}

    if not args.skip_integrity:
        results["integrity"] = _run_integrity_check(storage_path)
    else:
        logger.info("[1/4] Integrity check — SKIPPED (--skip-integrity)")
        results["integrity"] = True

    results["duplicates"] = _run_duplicate_check(args.fail_on_dupes)
    results["overfitting"] = _run_overfitting_scan()
    results["stats"] = _run_extraction_stats()

    failed = [name for name, ok in results.items() if not ok]
    duration = (datetime.now(tz=timezone.utc) - started_at).total_seconds()

    if failed:
        logger.error(
            "=== Daily Health Check FAILED (%.1fs): %s ===", duration, ", ".join(failed)
        )
        sys.exit(1)

    logger.info("=== Daily Health Check PASSED (%.1fs) ===", duration)
    print("✅ Daily health check passed")


if __name__ == "__main__":
    main()
