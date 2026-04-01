"""Tests for SimRating calculator — range-based assertions only."""
import pytest

from analytics.src.simrating.calculator import SimRatingCalculator


class TestSimRating:
    def setup_method(self):
        self.calc = SimRatingCalculator()

    def test_average_player_near_zero(self):
        """Average player (all z=0) should produce SimRating near 0."""
        result = self.calc.calculate(
            kills_z=0.0, deaths_z=0.0, adjusted_kill_value_z=0.0,
            adr_z=0.0, kast_pct_z=0.0
        )
        assert abs(result.sim_rating) < 0.01

    def test_elite_player_positive(self):
        """Elite player (all z=+2) should produce positive SimRating."""
        result = self.calc.calculate(
            kills_z=2.0, deaths_z=-1.0, adjusted_kill_value_z=2.0,
            adr_z=2.0, kast_pct_z=2.0
        )
        assert result.sim_rating > 0

    def test_poor_player_negative(self):
        """Poor player (all z=-2) should produce negative SimRating."""
        result = self.calc.calculate(
            kills_z=-2.0, deaths_z=2.0, adjusted_kill_value_z=-2.0,
            adr_z=-2.0, kast_pct_z=-2.0
        )
        assert result.sim_rating < 0

    def test_rating_within_zscore_bounds(self):
        """SimRating should not exceed ±5 for typical z-score inputs."""
        result = self.calc.calculate(
            kills_z=3.0, deaths_z=-1.0, adjusted_kill_value_z=3.0,
            adr_z=3.0, kast_pct_z=3.0
        )
        # Range check — no hardcoded exact values
        assert -5.0 <= result.sim_rating <= 5.0

    def test_components_sum_to_rating(self):
        """Sum of weighted components equals SimRating."""
        result = self.calc.calculate(
            kills_z=1.0, deaths_z=0.5, adjusted_kill_value_z=1.5,
            adr_z=0.8, kast_pct_z=1.2
        )
        component_sum = sum(result.components.values())
        assert abs(component_sum - result.sim_rating) < 1e-9

    def test_validate_range_flags_outlier(self):
        """Ratings outside ±5 should fail validation."""
        assert not self.calc.validate_range(6.5)
        assert not self.calc.validate_range(-6.5)

    def test_validate_range_passes_normal(self):
        """Normal ratings should pass validation."""
        assert self.calc.validate_range(1.5)
        assert self.calc.validate_range(-1.5)
        assert self.calc.validate_range(0.0)
