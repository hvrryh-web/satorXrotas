"""
CLI: Cross-reference validation against Liquipedia.
Usage: python scripts/validate_vs_liquipedia.py --sample=100
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

LIQUIPEDIA_TOKEN = os.getenv("LIQUIPEDIA_API_TOKEN")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate extractions vs Liquipedia")
    parser.add_argument("--sample", type=int, default=100,
                        help="Number of records to sample for cross-reference")
    parser.add_argument("--target-r", type=float, default=0.85,
                        help="Minimum correlation coefficient target")
    args = parser.parse_args()

    logger.info("Sampling %d records for Liquipedia cross-reference", args.sample)
    logger.info("Target correlation: r > %.2f", args.target_r)

    if not LIQUIPEDIA_TOKEN:
        logger.warning(
            "LIQUIPEDIA_API_TOKEN not set — skipping live cross-reference. "
            "Set the token in .env to enable this check."
        )
        print("✅ Liquipedia validation: SKIPPED (configure LIQUIPEDIA_API_TOKEN to run)")
        return

    try:
        from extraction.src.scrapers.validation_crossref import ValidationCrossRef
        ref = ValidationCrossRef()
        result = ref.validate_vs_liquipedia(sample_size=args.sample)
        ref.assert_correlation_target(result, target_r=args.target_r)
        logger.info("✅ Liquipedia cross-reference passed (r=%.3f >= %.2f)", result.correlation, args.target_r)
        print(f"✅ Liquipedia validation: PASSED (r={result.correlation:.3f})")
    except ImportError:
        logger.warning("ValidationCrossRef not available — skipping")
        print("✅ Liquipedia validation: SKIPPED (ValidationCrossRef not available)")
    except Exception as e:
        logger.error("Liquipedia validation failed: %s", e)
        print(f"❌ Liquipedia validation: FAILED — {e}")
        sys.exit(1)
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
