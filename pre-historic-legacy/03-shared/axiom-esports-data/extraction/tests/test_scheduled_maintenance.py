"""
Tests for scheduled maintenance scripts:
  - daily_health_check.py
  - weekly_analytics_refresh.py
  - monthly_full_harvest.py

All tests are unit tests that exercise the script logic without requiring
a live database or network access.  Range-based assertions only — no
hardcoded player values or exact floating-point comparisons.
"""
import hashlib
import importlib
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _import_script(name: str):
    """Import a script module from axiom-esports-data/scripts/ by name."""
    scripts_dir = Path(__file__).parent.parent.parent / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    # We need the parent (axiom-esports-data/) on the path too so that
    # analytics/extraction imports inside the scripts resolve correctly.
    axiom_dir = scripts_dir.parent
    if str(axiom_dir) not in sys.path:
        sys.path.insert(0, str(axiom_dir))
    return importlib.import_module(name)


# ---------------------------------------------------------------------------
# daily_health_check.py
# ---------------------------------------------------------------------------

class TestDailyHealthCheckIntegrity:
    def test_integrity_check_empty_storage_passes(self, tmp_path):
        mod = _import_script("daily_health_check")
        assert mod._run_integrity_check(tmp_path) is True

    def test_integrity_check_missing_dir_passes(self, tmp_path):
        mod = _import_script("daily_health_check")
        missing = tmp_path / "nonexistent"
        assert mod._run_integrity_check(missing) is True

    def test_integrity_check_valid_files_passes(self, tmp_path):
        content = "sample raw html"
        cs = hashlib.sha256(content.encode()).hexdigest()
        (tmp_path / f"{cs}.raw").write_text(content)
        mod = _import_script("daily_health_check")
        assert mod._run_integrity_check(tmp_path) is True

    def test_integrity_check_corrupted_file_fails(self, tmp_path):
        cs = hashlib.sha256(b"original").hexdigest()
        (tmp_path / f"{cs}.raw").write_text("corrupted")
        mod = _import_script("daily_health_check")
        assert mod._run_integrity_check(tmp_path) is False


class TestDailyHealthCheckDuplicates:
    def test_duplicate_check_no_db_returns_true(self):
        """Without DATABASE_URL, duplicate check should not fail."""
        mod = _import_script("daily_health_check")
        with patch.dict("os.environ", {}, clear=True):
            # Ensure DATABASE_URL is absent
            import os
            os.environ.pop("DATABASE_URL", None)
            assert mod._run_duplicate_check(fail_on_dupes=False) is True

    def test_duplicate_check_fail_on_dupes_still_skips_without_db(self):
        mod = _import_script("daily_health_check")
        import os
        os.environ.pop("DATABASE_URL", None)
        assert mod._run_duplicate_check(fail_on_dupes=True) is True


class TestDailyHealthCheckOverfitting:
    def test_overfitting_scan_loads_temporal_wall(self):
        mod = _import_script("daily_health_check")
        assert mod._run_overfitting_scan() is True


class TestDailyHealthCheckStats:
    def test_stats_no_db_returns_true(self):
        mod = _import_script("daily_health_check")
        import os
        os.environ.pop("DATABASE_URL", None)
        assert mod._run_extraction_stats() is True


# ---------------------------------------------------------------------------
# weekly_analytics_refresh.py
# ---------------------------------------------------------------------------

class TestWeeklyRefreshTemporalWall:
    def test_temporal_wall_check_passes(self):
        mod = _import_script("weekly_analytics_refresh")
        assert mod._check_temporal_wall() is True


class TestWeeklyRefreshSimRating:
    def test_simrating_dry_run_passes(self):
        mod = _import_script("weekly_analytics_refresh")
        assert mod._refresh_simrating(dry_run=True) is True

    def test_simrating_live_run_passes(self):
        """Live run without DB still loads module successfully."""
        mod = _import_script("weekly_analytics_refresh")
        import os
        os.environ.pop("DATABASE_URL", None)
        assert mod._refresh_simrating(dry_run=False) is True


class TestWeeklyRefreshRAR:
    def test_rar_dry_run_passes(self):
        mod = _import_script("weekly_analytics_refresh")
        assert mod._refresh_rar(dry_run=True) is True

    def test_rar_mean_within_range(self):
        """RAR replacement mean must stay within 0.9–1.1."""
        from analytics.src.rar.decomposer import RARDecomposer
        d = RARDecomposer()
        mean = d.get_replacement_mean()
        assert 0.9 <= mean <= 1.1


class TestWeeklyRefreshInvestmentGrades:
    def test_investment_grade_dry_run_passes(self):
        mod = _import_script("weekly_analytics_refresh")
        assert mod._refresh_investment_grades(dry_run=True) is True

    def test_investment_grade_sample_valid(self):
        """All investment grades must be from the allowed set."""
        from analytics.src.investment.grader import InvestmentGrader
        grader = InvestmentGrader()
        valid_grades = {"A+", "A", "B", "C", "D"}
        for rating in (0.70, 0.90, 1.05, 1.20, 1.40):
            result = grader.grade(raw_rating=rating, role="Entry", age=23)
            assert result["investment_grade"] in valid_grades


class TestWeeklyRefreshSnapshot:
    def test_weekly_snapshot_dry_run_passes(self):
        mod = _import_script("weekly_analytics_refresh")
        assert mod._export_weekly_snapshot(dry_run=True) is True

    def test_weekly_snapshot_no_db_passes(self):
        mod = _import_script("weekly_analytics_refresh")
        import os
        os.environ.pop("DATABASE_URL", None)
        assert mod._export_weekly_snapshot(dry_run=False) is True


# ---------------------------------------------------------------------------
# monthly_full_harvest.py
# ---------------------------------------------------------------------------

class TestMonthlyGuardrails:
    def test_guardrails_check_passes(self):
        mod = _import_script("monthly_full_harvest")
        assert mod._run_guardrails() is True


class TestMonthlyCrossReference:
    def test_cross_reference_no_db_passes(self):
        """With no DATABASE_URL the cross-reference should skip gracefully."""
        mod = _import_script("monthly_full_harvest")
        import os
        os.environ.pop("DATABASE_URL", None)
        assert mod._run_cross_reference(sample_size=50) is True


class TestMonthlyIntegrityCheck:
    def test_integrity_empty_storage_passes(self, tmp_path):
        mod = _import_script("monthly_full_harvest")
        assert mod._run_integrity_check(tmp_path) is True

    def test_integrity_valid_file_passes(self, tmp_path):
        content = "monthly raw"
        cs = hashlib.sha256(content.encode()).hexdigest()
        (tmp_path / f"{cs}.raw").write_text(content)
        mod = _import_script("monthly_full_harvest")
        assert mod._run_integrity_check(tmp_path) is True


class TestMonthlyFullHarvestAsync:
    @pytest.mark.asyncio
    async def test_dry_run_returns_zero_counts(self):
        mod = _import_script("monthly_full_harvest")
        totals = await mod._run_full_harvest(epochs=[1, 2, 3], dry_run=True)
        assert set(totals.keys()) == {1, 2, 3}
        assert all(v == 0 for v in totals.values())

    @pytest.mark.asyncio
    async def test_dry_run_single_epoch(self):
        mod = _import_script("monthly_full_harvest")
        totals = await mod._run_full_harvest(epochs=[3], dry_run=True)
        assert totals == {3: 0}
