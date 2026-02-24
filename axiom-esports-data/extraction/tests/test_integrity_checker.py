"""Tests for IntegrityChecker SHA-256 verification."""
import hashlib
import tempfile
from pathlib import Path

import pytest

from extraction.src.storage.integrity_checker import IntegrityChecker


class TestIntegrityChecker:
    def test_valid_file_passes(self, tmp_path):
        content = "test html content"
        checksum = hashlib.sha256(content.encode()).hexdigest()
        f = tmp_path / f"{checksum}.raw"
        f.write_text(content)

        checker = IntegrityChecker(storage_path=tmp_path)
        assert checker.verify_file(f)

    def test_corrupted_file_fails(self, tmp_path):
        content = "original content"
        checksum = hashlib.sha256(content.encode()).hexdigest()
        f = tmp_path / f"{checksum}.raw"
        f.write_text("corrupted content")  # Different from checksum

        checker = IntegrityChecker(storage_path=tmp_path)
        assert not checker.verify_file(f)

    def test_non_sha256_filename_warns(self, tmp_path):
        f = tmp_path / "not_a_checksum.raw"
        f.write_text("content")

        checker = IntegrityChecker(storage_path=tmp_path)
        assert not checker.verify_file(f)

    def test_verify_all_raises_on_corruption(self, tmp_path):
        # Valid file
        good = "good content"
        good_checksum = hashlib.sha256(good.encode()).hexdigest()
        (tmp_path / f"{good_checksum}.raw").write_text(good)

        # Corrupted file
        bad_checksum = hashlib.sha256(b"original").hexdigest()
        (tmp_path / f"{bad_checksum}.raw").write_text("different content")

        checker = IntegrityChecker(storage_path=tmp_path)
        with pytest.raises(RuntimeError, match="corrupted files"):
            checker.verify_all()

    def test_verify_all_passes_clean_store(self, tmp_path):
        for i in range(3):
            content = f"match content {i}"
            checksum = hashlib.sha256(content.encode()).hexdigest()
            (tmp_path / f"{checksum}.raw").write_text(content)

        checker = IntegrityChecker(storage_path=tmp_path)
        results = checker.verify_all()
        assert all(results.values())
