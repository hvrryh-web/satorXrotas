"""
Integrity Checker — SHA-256 verification for all stored extractions.
"""
import hashlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class IntegrityChecker:
    """
    Verifies SHA-256 checksums of all stored raw extractions.
    Called before any analytics processing.
    """

    def __init__(self, storage_path: Path = Path("data/raw_extractions")) -> None:
        self.storage_path = storage_path

    def verify_file(self, file_path: Path) -> bool:
        """Verify a single raw file's checksum matches its filename."""
        expected_checksum = file_path.stem  # filename is the checksum
        if len(expected_checksum) != 64:
            logger.warning("File %s does not appear to be named by SHA-256", file_path)
            return False

        content = file_path.read_text(encoding="utf-8")
        actual = hashlib.sha256(content.encode()).hexdigest()

        if actual != expected_checksum:
            logger.error(
                "Checksum MISMATCH: %s. Expected %s, got %s",
                file_path.name, expected_checksum[:12], actual[:12],
            )
            return False

        return True

    def verify_all(self) -> dict[str, bool]:
        """
        Verify all .raw files in storage. Returns {filename: passed} dict.
        """
        results = {}
        raw_files = list(self.storage_path.glob("*.raw"))
        logger.info("Verifying %d raw extraction files", len(raw_files))

        for f in raw_files:
            results[f.name] = self.verify_file(f)

        passed = sum(1 for v in results.values() if v)
        failed = len(results) - passed
        logger.info("Integrity check: %d passed, %d failed", passed, failed)

        if failed > 0:
            raise RuntimeError(
                f"Integrity check failed: {failed} corrupted files detected. "
                "Do not proceed with analytics until resolved."
            )
        return results


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-all", action="store_true")
    args = parser.parse_args()
    if args.verify_all:
        checker = IntegrityChecker()
        checker.verify_all()
        print("✅ All integrity checks passed")
