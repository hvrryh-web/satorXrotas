"""Tests for RAR (Role-Adjusted Rating) module — range-based assertions only."""
import pytest

from analytics.src.rar.decomposer import RARDecomposer
from analytics.src.rar.replacement_levels import get_replacement_level

VALID_GRADES = {"A+", "A", "B", "C", "D"}
ALL_ROLES = ["Entry", "IGL", "Controller", "Initiator", "Sentinel"]


class TestRARDecomposer:
    def setup_method(self):
        self.rar = RARDecomposer()

    # ── 1. rar_score is always positive when raw_rating is positive ─────────
    def test_positive_raw_rating_yields_positive_rar_score(self):
        """Any positive raw_rating should produce a positive rar_score."""
        for role in ALL_ROLES:
            result = self.rar.compute(raw_rating=1.0, role=role)
            assert result.rar_score > 0, f"Expected positive rar_score for role={role}"

    def test_high_raw_rating_positive_rar(self):
        result = self.rar.compute(raw_rating=2.0, role="Controller")
        assert result.rar_score > 0

    def test_small_positive_raw_rating_positive_rar(self):
        result = self.rar.compute(raw_rating=0.1, role="Entry")
        assert result.rar_score > 0

    # ── 2. Grade thresholds produce valid grades ─────────────────────────────
    def test_grade_thresholds_produce_valid_grades(self):
        """_grade must always return one of A+/A/B/C/D."""
        test_scores = [0.5, 0.85, 1.00, 1.15, 1.30, 1.50, 2.0]
        for score in test_scores:
            grade = self.rar._grade(score)
            assert grade in VALID_GRADES, f"Unexpected grade '{grade}' for score={score}"

    def test_high_rar_score_yields_a_plus(self):
        """rar_score >= 1.30 must be 'A+'."""
        assert self.rar._grade(1.30) == "A+"
        assert self.rar._grade(1.50) == "A+"

    def test_mid_rar_score_yields_a(self):
        """1.15 <= rar_score < 1.30 must be 'A'."""
        assert self.rar._grade(1.15) == "A"
        assert self.rar._grade(1.20) == "A"

    def test_at_replacement_yields_b(self):
        """1.00 <= rar_score < 1.15 must be 'B'."""
        assert self.rar._grade(1.00) == "B"
        assert self.rar._grade(1.10) == "B"

    def test_below_replacement_yields_c(self):
        """0.85 <= rar_score < 1.00 must be 'C'."""
        assert self.rar._grade(0.85) == "C"
        assert self.rar._grade(0.95) == "C"

    def test_very_low_rar_score_yields_d(self):
        """rar_score < 0.85 must be 'D'."""
        assert self.rar._grade(0.84) == "D"
        assert self.rar._grade(0.50) == "D"

    # ── 3. Replacement mean is within expected range ─────────────────────────
    def test_replacement_mean_within_range(self):
        """Mean replacement level across all roles should be in (0.9, 1.1)."""
        mean = self.rar.get_replacement_mean()
        assert 0.9 < mean < 1.1, f"Replacement mean {mean:.4f} outside (0.9, 1.1)"

    def test_replacement_mean_is_finite(self):
        mean = self.rar.get_replacement_mean()
        assert isinstance(mean, float)
        assert mean == mean  # not NaN

    # ── 4. Unknown role falls back to 1.00 replacement level ─────────────────
    def test_unknown_role_uses_default_replacement(self):
        """Unrecognised roles should fall back to 1.00 replacement level."""
        result = self.rar.compute(raw_rating=1.0, role="UnknownRole")
        assert result.replacement_level == 1.00

    def test_unknown_role_rar_score_equals_raw_rating(self):
        """With replacement=1.0, rar_score == raw_rating."""
        raw = 1.25
        result = self.rar.compute(raw_rating=raw, role="Fragger")
        assert abs(result.rar_score - raw) < 1e-9

    # ── 5. investment_grade matches _grade(rar_score) ────────────────────────
    def test_investment_grade_consistent_with_internal_grade(self):
        """investment_grade on the result must equal _grade(rar_score)."""
        for role in ALL_ROLES:
            for raw in [0.5, 0.9, 1.0, 1.1, 1.2, 1.4]:
                result = self.rar.compute(raw_rating=raw, role=role)
                expected_grade = self.rar._grade(result.rar_score)
                assert result.investment_grade == expected_grade, (
                    f"Grade mismatch for role={role}, raw={raw}: "
                    f"got {result.investment_grade!r}, expected {expected_grade!r}"
                )

    def test_investment_grade_is_valid_letter(self):
        result = self.rar.compute(raw_rating=1.0, role="Controller")
        assert result.investment_grade in VALID_GRADES

    # ── 6. RARResult fields are populated correctly ───────────────────────────
    def test_result_fields_populated(self):
        result = self.rar.compute(raw_rating=1.1, role="Entry")
        assert result.role == "Entry"
        assert abs(result.raw_rating - 1.1) < 1e-9
        assert result.replacement_level > 0
        assert result.rar_score > 0
        assert result.investment_grade in VALID_GRADES


class TestGetReplacementLevel:
    """Tests for the standalone get_replacement_level function."""

    def test_known_roles_return_positive_levels(self):
        for role in ["Entry", "IGL", "Controller", "Initiator", "Sentinel"]:
            level = get_replacement_level(role)
            assert level > 0, f"Replacement level for {role} must be positive"

    def test_entry_replacement_above_controller(self):
        """Entry (1.15) should have a higher replacement bar than Controller (1.00)."""
        assert get_replacement_level("Entry") > get_replacement_level("Controller")

    def test_igl_replacement_below_controller(self):
        """IGL (0.95) should have a lower replacement bar than Controller (1.00)."""
        assert get_replacement_level("IGL") < get_replacement_level("Controller")

    def test_unknown_role_defaults_to_one(self):
        assert get_replacement_level("Support") == 1.00
        assert get_replacement_level("") == 1.00

    def test_all_levels_within_plausible_range(self):
        """Replacement levels should be between 0.8 and 1.4."""
        for role in ["Entry", "IGL", "Controller", "Initiator", "Sentinel"]:
            level = get_replacement_level(role)
            assert 0.8 <= level <= 1.4, (
                f"Replacement level {level} for {role} outside plausible range"
            )
