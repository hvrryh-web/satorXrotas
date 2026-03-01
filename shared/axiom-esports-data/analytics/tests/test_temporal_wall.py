"""Tests for TemporalWall — temporal data leakage prevention."""
import pandas as pd
import pytest

from analytics.src.guardrails.temporal_wall import TemporalWall, DataLeakageError


def make_df(dates: list[str], match_ids: list[str] = None) -> pd.DataFrame:
    n = len(dates)
    return pd.DataFrame({
        "realworld_time": pd.to_datetime(dates, utc=True),
        "match_id": match_ids or [f"match_{i}" for i in range(n)],
        "player_id": [f"player_{i % 3}" for i in range(n)],
        "acs": [200.0 + i * 5 for i in range(n)],
    })


class TestTemporalWall:
    def setup_method(self):
        self.wall = TemporalWall(cutoff_date="2024-01-01")

    def test_split_basic(self):
        df = make_df([
            "2023-06-01", "2023-12-31",
            "2024-01-01", "2024-06-01",
        ])
        train, test = self.wall.split(df)
        assert len(train) == 2
        assert len(test) == 2

    def test_no_overlap_in_split(self):
        df = make_df([
            "2023-01-01", "2023-06-01", "2023-12-31",
            "2024-01-01", "2024-06-01",
        ])
        train, test = self.wall.split(df)
        overlap = set(train["match_id"]) & set(test["match_id"])
        assert len(overlap) == 0, f"Overlap detected: {overlap}"

    def test_raises_on_match_id_overlap(self):
        shared_ids = ["match_A", "match_B"]
        df_train = make_df(["2023-06-01", "2023-09-01"], match_ids=shared_ids)
        df_test = make_df(["2024-03-01", "2024-06-01"], match_ids=shared_ids)
        with pytest.raises(DataLeakageError, match="TEMPORAL LEAKAGE"):
            self.wall._assert_no_overlap(df_train, df_test)

    def test_future_data_rejected(self):
        df = make_df(["2024-06-01", "2025-01-01"])
        with pytest.raises(DataLeakageError, match="FUTURE DATA"):
            self.wall.validate_no_future_data(df)

    def test_train_only_past_data(self):
        df = make_df(["2022-01-01", "2023-01-01", "2023-12-31"])
        # Should not raise
        self.wall.validate_no_future_data(df)

    def test_all_training_acs_in_valid_range(self):
        """Tests use statistical ranges — no hardcoded player values."""
        df = make_df(["2023-01-01", "2023-06-01", "2023-12-01"])
        train, _ = self.wall.split(df)
        for acs in train["acs"]:
            assert 100 < acs < 500, f"ACS {acs} outside plausible range"
