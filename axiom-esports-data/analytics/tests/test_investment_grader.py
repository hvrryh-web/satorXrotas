"""Tests for InvestmentGrader — range-based assertions only."""
import pytest

from analytics.src.investment.grader import InvestmentGrader

VALID_GRADES = {"A+", "A", "B", "C", "D"}


class TestInvestmentGrader:
    def setup_method(self):
        self.grader = InvestmentGrader()
        self.peak_range = (21, 26)

    # ── 1. Age factor is 1.0 in peak range, 0.85 outside ────────────────────
    def test_age_factor_is_one_when_in_peak(self):
        """Players within peak_age_range should receive age_factor == 1.0."""
        for age in range(21, 27):  # 21..26 inclusive
            result = self.grader.grade(raw_rating=1.0, role="Controller", age=age)
            assert result["age_factor"] == 1.0, (
                f"Expected age_factor=1.0 for age={age}, got {result['age_factor']}"
            )

    def test_age_factor_is_reduced_below_peak(self):
        """Players younger than peak_age_range should receive age_factor < 1.0."""
        result = self.grader.grade(raw_rating=1.0, role="Controller", age=19)
        assert result["age_factor"] < 1.0
        # Default discount is 0.85
        assert 0.8 <= result["age_factor"] <= 0.9

    def test_age_factor_is_reduced_above_peak(self):
        """Players older than peak_age_range should receive age_factor < 1.0."""
        result = self.grader.grade(raw_rating=1.0, role="Controller", age=30)
        assert result["age_factor"] < 1.0
        assert 0.8 <= result["age_factor"] <= 0.9

    def test_age_factor_at_exact_boundaries(self):
        """Boundary ages 21 and 26 are in-peak."""
        for boundary_age in (21, 26):
            result = self.grader.grade(raw_rating=1.0, role="Entry", age=boundary_age)
            assert result["age_factor"] == 1.0, (
                f"Boundary age {boundary_age} should be in-peak"
            )

    def test_age_factor_just_outside_boundaries(self):
        """Ages 20 and 27 are outside the default peak range."""
        for outside_age in (20, 27):
            result = self.grader.grade(raw_rating=1.0, role="Entry", age=outside_age)
            assert result["age_factor"] < 1.0, (
                f"Age {outside_age} should be outside-peak"
            )

    # ── 2. Investment grade is always a valid letter ─────────────────────────
    def test_investment_grade_is_valid_letter(self):
        test_cases = [
            (0.5, "Controller", 22),
            (1.0, "Entry", 24),
            (1.5, "IGL", 19),
            (2.0, "Sentinel", 30),
        ]
        for raw, role, age in test_cases:
            result = self.grader.grade(raw_rating=raw, role=role, age=age)
            assert result["investment_grade"] in VALID_GRADES, (
                f"Invalid grade '{result['investment_grade']}' for "
                f"raw={raw}, role={role}, age={age}"
            )

    # ── 3. Higher raw_rating produces better or equal grade ──────────────────
    def test_higher_raw_rating_better_or_equal_grade(self):
        """A higher raw_rating should never produce a worse investment_grade."""
        grade_order = {"D": 0, "C": 1, "B": 2, "A": 3, "A+": 4}
        ratings = [0.5, 0.8, 1.0, 1.1, 1.2, 1.4, 1.6]
        age = 23  # in-peak — age_factor=1.0, keeps the comparison clean
        role = "Controller"

        grades = [
            self.grader.grade(raw_rating=r, role=role, age=age)["investment_grade"]
            for r in ratings
        ]
        for i in range(len(grades) - 1):
            low_rank = grade_order[grades[i]]
            high_rank = grade_order[grades[i + 1]]
            assert high_rank >= low_rank, (
                f"Grade should not decrease: rating {ratings[i]}->{ratings[i+1]} "
                f"produced {grades[i]}->{grades[i+1]}"
            )

    # ── 4. in_peak_age is True when age is within peak_age_range ─────────────
    def test_in_peak_age_true_for_peak_ages(self):
        for age in range(21, 27):
            result = self.grader.grade(raw_rating=1.0, role="Initiator", age=age)
            assert result["in_peak_age"] is True, f"age={age} should be in-peak"

    def test_in_peak_age_false_outside_peak(self):
        for age in [18, 19, 20, 27, 28, 35]:
            result = self.grader.grade(raw_rating=1.0, role="Initiator", age=age)
            assert result["in_peak_age"] is False, f"age={age} should not be in-peak"

    def test_custom_peak_range_respected(self):
        """Custom peak_age_range should override the default."""
        result_in = self.grader.grade(
            raw_rating=1.0, role="Controller", age=28, peak_age_range=(25, 30)
        )
        result_out = self.grader.grade(
            raw_rating=1.0, role="Controller", age=23, peak_age_range=(25, 30)
        )
        assert result_in["in_peak_age"] is True
        assert result_out["in_peak_age"] is False

    # ── 5. adjusted_rar <= rar_score when not in peak (age_factor < 1.0) ─────
    def test_adjusted_rar_discounted_outside_peak(self):
        """Outside peak range, adjusted_rar should be less than rar_score."""
        result = self.grader.grade(raw_rating=1.2, role="Entry", age=19)
        assert result["adjusted_rar"] < result["rar_score"], (
            "adjusted_rar should be discounted outside peak age"
        )

    def test_adjusted_rar_equals_rar_score_in_peak(self):
        """Inside peak range, adjusted_rar == rar_score (age_factor=1.0)."""
        result = self.grader.grade(raw_rating=1.2, role="Entry", age=23)
        assert abs(result["adjusted_rar"] - result["rar_score"]) < 1e-9

    def test_adjusted_rar_within_plausible_range(self):
        """adjusted_rar should stay within a sensible numeric range."""
        result = self.grader.grade(raw_rating=1.5, role="Controller", age=24)
        assert 0.0 < result["adjusted_rar"] < 5.0

    # ── 6. Result dict completeness ──────────────────────────────────────────
    def test_result_contains_all_required_keys(self):
        required = {"rar_score", "age_factor", "adjusted_rar", "investment_grade", "in_peak_age"}
        result = self.grader.grade(raw_rating=1.0, role="Controller", age=23)
        assert required.issubset(result.keys())
