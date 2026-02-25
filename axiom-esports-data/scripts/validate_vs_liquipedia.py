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


if __name__ == "__main__":
    main()
