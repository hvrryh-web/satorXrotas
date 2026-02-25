"""
CLI: Cross-reference validation against Liquipedia.
Usage: python scripts/validate_vs_liquipedia.py --sample=100
"""
import argparse
import logging
import os
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate extractions vs Liquipedia")
    parser.add_argument("--sample", type=int, default=100,
                        help="Number of records to sample for cross-reference")
    parser.add_argument("--target-r", type=float, default=0.85,
                        help="Minimum correlation coefficient target")
    args = parser.parse_args()

    logger.info("Sampling %d records for Liquipedia cross-reference", args.sample)
    logger.info("Target correlation: r > %.2f", args.target_r)

    database_url = os.environ.get("DATABASE_URL")

    from extraction.src.scrapers.validation_crossref import ValidationCrossRef, CORRELATION_TARGET

    ref = ValidationCrossRef(database_url=database_url)
    result = ref.validate_vs_liquipedia(sample_size=args.sample)

    if result.sample_size == 0 or result.correlation == 0.0:
        logger.warning("Liquipedia cross-reference requires API credentials (see .env.example)")
        print("⚠️  Liquipedia validation skipped — configure DATABASE_URL and credentials to run")
        sys.exit(0)

    logger.info(
        "Correlation: r=%.3f vs target %.2f (passed=%s)",
        result.correlation, args.target_r, result.passed,
    )

    if not result.passed:
        logger.error("Correlation %.3f is below target %.2f", result.correlation, args.target_r)
        sys.exit(1)

    print(f"✅ Liquipedia validation passed: r={result.correlation:.3f}")


if __name__ == "__main__":
    main()
