"""
Temporal Wall — Enforces strict temporal train/test split to prevent data leakage.
No future data may appear in the training set (Mono no aware compliance).
"""
import logging
from datetime import datetime
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_CUTOFF = "2024-01-01"


class TemporalWall:
    """
    Prevents temporal data leakage in model training.
    Training data must predate the cutoff date.
    Test data must postdate it. No overlap permitted.

    Critical: shuffle splits are PROHIBITED — always use this class.
    """

    def __init__(self, cutoff_date: str = DEFAULT_CUTOFF) -> None:
        self.cutoff = pd.Timestamp(cutoff_date)
        logger.info("TemporalWall initialized with cutoff: %s", cutoff_date)

    def split(self, df: pd.DataFrame, time_col: str = "realworld_time") -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split dataframe into train (before cutoff) and test (on/after cutoff).
        Raises if any temporal overlap is detected.
        """
        if time_col not in df.columns:
            raise ValueError(f"Column '{time_col}' not found in DataFrame")

        df = df.copy()
        df[time_col] = pd.to_datetime(df[time_col], utc=True)

        train = df[df[time_col] < self.cutoff].copy()
        test = df[df[time_col] >= self.cutoff].copy()

        self._assert_no_overlap(train, test)
        logger.info(
            "Temporal split: %d training records (before %s), %d test records",
            len(train), self.cutoff.date(), len(test),
        )
        return train, test

    def _assert_no_overlap(self, train: pd.DataFrame, test: pd.DataFrame) -> None:
        """Verify zero match_id overlap between train and test sets."""
        if "match_id" not in train.columns or "match_id" not in test.columns:
            return  # Cannot verify without match_id

        train_matches = set(train["match_id"])
        test_matches = set(test["match_id"])
        overlap = train_matches & test_matches

        if overlap:
            raise DataLeakageError(
                f"TEMPORAL LEAKAGE DETECTED: {len(overlap)} match_ids appear in both "
                f"train and test sets. Resolve before proceeding. "
                f"Sample overlap: {list(overlap)[:5]}"
            )
        logger.info("✅ No temporal overlap detected between train and test sets")

    def validate_no_future_data(self, df: pd.DataFrame, time_col: str = "realworld_time") -> None:
        """Assert that a training dataframe contains no records at or after cutoff."""
        df[time_col] = pd.to_datetime(df[time_col], utc=True)
        violations = df[df[time_col] >= self.cutoff]
        if len(violations) > 0:
            raise DataLeakageError(
                f"FUTURE DATA IN TRAINING SET: {len(violations)} records "
                f"on or after cutoff {self.cutoff.date()}."
            )
        logger.info("✅ Training set temporal wall validated — no future data")


class DataLeakageError(Exception):
    """Raised when temporal data leakage is detected."""
