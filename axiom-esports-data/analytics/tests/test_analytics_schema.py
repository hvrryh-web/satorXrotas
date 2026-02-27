"""Analytics-layer schema compliance tests using synthetic DataFrames."""
import pytest
import pandas as pd
import numpy as np

from analytics.src.simrating.normalizer import SeasonCohortNormalizer, NUMERIC_COLS
from analytics.src.simrating.calculator import SimRatingCalculator, SimRatingResult


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def synthetic_df():
    """Synthetic cohort: 30 players, 2 seasons, 2 roles."""
    rng = np.random.default_rng(42)
    n = 30
    return pd.DataFrame({
        "player_id": [f"p{i:03d}" for i in range(n)],
        "season":    (["2023"] * 15) + (["2024"] * 15),
        "role":      (["Entry"] * 10 + ["Controller"] * 5) * 2,
        "kills":     rng.integers(8, 25, n).astype(float),
        "deaths":    rng.integers(6, 22, n).astype(float),
        "acs":       rng.uniform(150.0, 400.0, n),
        "adr":       rng.uniform(80.0, 200.0, n),
        "kast_pct":  rng.uniform(55.0, 85.0, n),
    })


@pytest.fixture
def normalizer():
    return SeasonCohortNormalizer()


@pytest.fixture
def calculator():
    return SimRatingCalculator()


# ── SeasonCohortNormalizer tests ──────────────────────────────────────────────

class TestSeasonCohortNormalizer:

    def test_produces_z_score_columns_for_present_numeric_cols(self, normalizer, synthetic_df):
        """fit_transform must add _z suffix columns for every numeric col present."""
        result = normalizer.fit_transform(synthetic_df)
        present_cols = [c for c in NUMERIC_COLS if c in synthetic_df.columns]
        for col in present_cols:
            z_col = f"{col}_z"
            assert z_col in result.columns, (
                f"Expected z-score column '{z_col}' in result"
            )

    def test_z_score_columns_within_plausible_range(self, normalizer, synthetic_df):
        """Z-score columns should be within [-5, +5] for normally-distributed data."""
        result = normalizer.fit_transform(synthetic_df)
        present_cols = [c for c in NUMERIC_COLS if c in synthetic_df.columns]
        for col in present_cols:
            z_col = f"{col}_z"
            z_vals = result[z_col].dropna()
            assert (z_vals.abs() <= 5.0).all(), (
                f"Column '{z_col}' has values outside [-5, +5]: "
                f"min={z_vals.min():.3f}, max={z_vals.max():.3f}"
            )

    def test_z_score_mean_near_zero_per_group(self, normalizer, synthetic_df):
        """Within each cohort group, z-score mean should be near zero."""
        result = normalizer.fit_transform(synthetic_df)
        present_cols = [c for c in NUMERIC_COLS if c in synthetic_df.columns]
        for col in present_cols:
            z_col = f"{col}_z"
            for (season, role), group in result.groupby(["season", "role"]):
                group_mean = group[z_col].mean()
                assert abs(group_mean) < 0.1, (
                    f"Group ({season}, {role}) mean for '{z_col}' "
                    f"deviates from 0: {group_mean:.4f}"
                )

    def test_handles_missing_optional_columns_gracefully(self, normalizer):
        """fit_transform should not raise if optional NUMERIC_COLS are absent."""
        minimal_df = pd.DataFrame({
            "player_id": ["p001", "p002", "p003"],
            "season":    ["2024", "2024", "2024"],
            "role":      ["Entry", "Entry", "Controller"],
            "kills":     [12.0, 15.0, 10.0],
            "deaths":    [8.0, 10.0, 9.0],
            # No acs, adr, kast_pct, headshot_pct, etc.
        })
        try:
            result = normalizer.fit_transform(minimal_df)
        except Exception as exc:
            pytest.fail(
                f"fit_transform raised unexpectedly with missing optional columns: {exc}"
            )
        # Only present columns should have z-score equivalents
        assert "kills_z" in result.columns
        assert "deaths_z" in result.columns
        assert "acs_z" not in result.columns

    def test_handles_no_season_column(self, normalizer):
        """fit_transform must work even when season column is absent."""
        df = pd.DataFrame({
            "role":   ["Entry", "Entry", "Controller", "Controller"],
            "kills":  [10.0, 14.0, 11.0, 13.0],
            "deaths": [8.0, 9.0, 7.0, 10.0],
        })
        result = normalizer.fit_transform(df)
        assert "kills_z" in result.columns
        assert "deaths_z" in result.columns

    def test_output_row_count_preserved(self, normalizer, synthetic_df):
        """Output DataFrame should have the same row count as input."""
        result = normalizer.fit_transform(synthetic_df)
        assert len(result) == len(synthetic_df)

    def test_original_columns_preserved(self, normalizer, synthetic_df):
        """All original columns should still exist in the output."""
        result = normalizer.fit_transform(synthetic_df)
        for col in synthetic_df.columns:
            assert col in result.columns, f"Original column '{col}' was dropped"


# ── SimRatingResult schema tests ──────────────────────────────────────────────

class TestSimRatingResultSchema:

    def test_result_has_all_required_fields(self, calculator):
        """SimRatingResult must contain sim_rating, components, and z_scores."""
        result = calculator.calculate(
            kills_z=0.5, deaths_z=-0.3, adjusted_kill_value_z=0.8,
            adr_z=0.4, kast_pct_z=0.6,
        )
        assert hasattr(result, "sim_rating"), "Missing field: sim_rating"
        assert hasattr(result, "components"), "Missing field: components"
        assert hasattr(result, "z_scores"),   "Missing field: z_scores"

    def test_components_dict_has_five_entries(self, calculator):
        """components dict should have exactly 5 entries (one per z-score input)."""
        result = calculator.calculate(
            kills_z=1.0, deaths_z=0.5, adjusted_kill_value_z=1.0,
            adr_z=0.8, kast_pct_z=1.2,
        )
        assert len(result.components) == 5

    def test_z_scores_dict_has_five_entries(self, calculator):
        """z_scores dict should track all 5 raw z-score inputs."""
        result = calculator.calculate(
            kills_z=1.0, deaths_z=0.5, adjusted_kill_value_z=1.0,
            adr_z=0.8, kast_pct_z=1.2,
        )
        assert len(result.z_scores) == 5

    def test_sim_rating_is_float(self, calculator):
        result = calculator.calculate(
            kills_z=0.0, deaths_z=0.0, adjusted_kill_value_z=0.0,
            adr_z=0.0, kast_pct_z=0.0,
        )
        assert isinstance(result.sim_rating, float)

    def test_sim_rating_within_schema_range(self, calculator):
        """SimRating should stay within the ±5 schema-documented range for normal inputs."""
        result = calculator.calculate(
            kills_z=2.0, deaths_z=-1.0, adjusted_kill_value_z=2.0,
            adr_z=2.0, kast_pct_z=2.0,
        )
        assert -5.0 <= result.sim_rating <= 5.0

    def test_result_is_simratingresult_instance(self, calculator):
        result = calculator.calculate(
            kills_z=0.0, deaths_z=0.0, adjusted_kill_value_z=0.0,
            adr_z=0.0, kast_pct_z=0.0,
        )
        assert isinstance(result, SimRatingResult)
