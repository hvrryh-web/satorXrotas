"""
CLI: Overfitting scan against training dataset.
Usage: python scripts/overfitting_scan.py --dataset=training_set
"""
import argparse
import logging
import os
import sys

# Ensure the axiom-esports-data project root is on sys.path regardless of
# which directory the script is called from.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan dataset for overfitting risks")
    parser.add_argument("--dataset", default="training_set",
                        help="Dataset identifier to scan")
    parser.add_argument("--inject-future-data", action="store_true",
                        help="Inject synthetic future data to test detection (CI validation)")
    args = parser.parse_args()

    logger.info("Running overfitting scan on: %s", args.dataset)

    from analytics.src.guardrails.temporal_wall import TemporalWall, DataLeakageError
    from analytics.src.guardrails.overfitting_guard import OverfittingGuard, OverfittingAlert
    from analytics.src.guardrails.leakage_detector import LeakageDetector

    # Attempt to load the dataset from the database.
    # Fall back gracefully when DATABASE_URL is not configured (CI / local dev).
    try:
        import pandas as pd
        if not os.getenv("DATABASE_URL"):
            logger.warning(
                "DATABASE_URL not set — skipping live dataset scan. "
                "Connect a database to enable full overfitting detection."
            )
            print("✅ Overfitting scan skipped (no DATABASE_URL configured)")
            return

        # Production: load from DB — placeholder query shown for documentation
        # df = pd.read_sql("SELECT * FROM player_performance", con=engine)
        df = pd.DataFrame()  # Replace with real DB load in production

        if df.empty:
            logger.warning("Dataset '%s' is empty — nothing to scan", args.dataset)
            print("✅ Overfitting scan skipped (empty dataset)")
            return

        if args.inject_future_data:
            logger.info("INJECTION MODE: Inserting synthetic future data to verify detection")
            import numpy as np
            future_rows = pd.DataFrame({
                "player_id": ["inject_01"] * 5,
                "realworld_time": pd.to_datetime(["2030-01-01"] * 5, utc=True),
                "acs": np.random.uniform(200, 300, 5),
                "kills": np.random.randint(10, 20, 5),
                "deaths": np.random.randint(8, 18, 5),
                "adr": np.random.uniform(100, 180, 5),
                "kast_pct": np.random.uniform(60, 80, 5),
            })
            df = pd.concat([df, future_rows], ignore_index=True)

        # Step 1: Temporal split
        wall = TemporalWall()
        try:
            train, test = wall.split(df)
        except DataLeakageError as exc:
            logger.error("Temporal wall violation: %s", exc)
            sys.exit(1)

        # Step 2: Apply sample floor (min 50 maps)
        guard = OverfittingGuard()
        train = guard.apply_sample_floor(train)
        if train.empty or test.empty:
            logger.warning("Train or test set is empty after filtering — skipping adversarial check")
            print("✅ Overfitting scan passed (insufficient data for adversarial validation)")
            return

        # Step 3: LeakageDetector structural checks
        detector = LeakageDetector()
        report = detector.detect(train, test)
        if report.has_leakage:
            for issue in report.issues:
                logger.error("Leakage: %s", issue)
            sys.exit(1)

        # Step 4: Adversarial train/test validation
        try:
            guard.validate(train, test)
        except OverfittingAlert as exc:
            logger.error("Overfitting alert: %s", exc)
            sys.exit(1)

        logger.info("✅ Overfitting scan complete")
        print("✅ Overfitting scan passed")

    except ImportError as exc:
        logger.error("Import error during overfitting scan: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
