"""
Confidence Sampler — Inverse-weight stratified sampling by confidence tier.
Low-confidence records are upsampled; high-confidence records downsampled.
"""
import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class ConfidenceSampler:
    """
    Applies inverse confidence weighting to produce balanced training samples.
    Prevents the model from over-relying on high-confidence (elite) records.
    """

    def sample(
        self,
        df: pd.DataFrame,
        n: int = 10_000,
        confidence_col: str = "confidence_tier",
        random_state: Optional[int] = 42,
    ) -> pd.DataFrame:
        """
        Draw n samples with inverse confidence weighting.
        Records with confidence_tier=25 are weighted 4x vs confidence_tier=100.
        Records with confidence_tier=0 are excluded from training.
        """
        if confidence_col not in df.columns:
            logger.warning(
                "Column '%s' not found — sampling uniformly", confidence_col
            )
            return df.sample(n=min(n, len(df)), random_state=random_state)

        # Exclude zero-confidence records from training
        eligible = df[df[confidence_col] > 0].copy()
        excluded = len(df) - len(eligible)
        if excluded:
            logger.info("Excluded %d zero-confidence records from sampling", excluded)

        # Inverse weight: lower confidence → higher weight
        weights = 1.0 / eligible[confidence_col].clip(lower=1.0)
        weights = weights / weights.sum()  # Normalize

        sample_n = min(n, len(eligible))
        sampled = eligible.sample(
            n=sample_n,
            weights=weights,
            replace=False,
            random_state=random_state,
        )

        logger.info(
            "Sampled %d records (from %d eligible, %d total)",
            len(sampled), len(eligible), len(df),
        )
        return sampled

    def stratified_by_role(
        self,
        df: pd.DataFrame,
        n_per_role: int = 2_000,
        role_col: str = "role",
    ) -> pd.DataFrame:
        """
        Sample n records per role to ensure role-balanced training sets.
        Prevents Entry-fragger overrepresentation.
        """
        if role_col not in df.columns:
            return df

        parts = []
        for role, group in df.groupby(role_col):
            n = min(n_per_role, len(group))
            parts.append(group.sample(n=n, random_state=42))
            logger.info("Role %s: sampled %d / %d records", role, n, len(group))

        return pd.concat(parts, ignore_index=True)
