"""
Normalizer — Z-score normalization within season/role cohorts.
"""
import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

NUMERIC_COLS = ["kills", "deaths", "acs", "adjusted_kill_value", "adr", "kast_pct",
                "headshot_pct", "first_blood", "clutch_wins"]


class SeasonCohortNormalizer:
    """
    Computes z-scores for each player record relative to their
    season + role cohort (e.g., 2024 Controllers).
    Prevents cross-era comparisons inflating older records.
    """

    def fit_transform(
        self,
        df: pd.DataFrame,
        season_col: str = "season",
        role_col: str = "role",
    ) -> pd.DataFrame:
        """Add z-score columns for all numeric metrics, grouped by season+role."""
        result = df.copy()
        cols_present = [c for c in NUMERIC_COLS if c in df.columns]

        if season_col not in df.columns:
            logger.warning("No season column — normalizing globally")
            group_keys = [role_col] if role_col in df.columns else []
        else:
            group_keys = [season_col, role_col] if role_col in df.columns else [season_col]

        for col in cols_present:
            z_col = f"{col}_z"
            if group_keys:
                result[z_col] = result.groupby(group_keys)[col].transform(
                    lambda x: (x - x.mean()) / (x.std() + 1e-8)
                )
            else:
                mu, sigma = df[col].mean(), df[col].std()
                result[z_col] = (df[col] - mu) / (sigma + 1e-8)

        return result
