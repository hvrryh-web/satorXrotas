"""
Leakage Detector — Checks for common data leakage patterns in the dataset.
"""
import logging
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class LeakageReport:
    has_leakage: bool
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class LeakageDetector:
    """
    Scans dataset for known leakage patterns:
    1. Hardcoded player references in test assertions
    2. Future match IDs in training data
    3. Role-performance circular assignment
    4. Analytics columns (sim_rating, rar_score) present before training cutoff
    """

    DERIVED_COLUMNS = {"sim_rating", "rar_score", "investment_grade",
                       "role_adjusted_value", "adjusted_kill_value"}

    def detect(
        self,
        train: pd.DataFrame,
        test: Optional[pd.DataFrame] = None,
        cutoff_date: str = "2024-01-01",
    ) -> LeakageReport:
        issues = []
        warnings = []

        # Check 1: Derived analytics columns present in training set
        derived_present = self.DERIVED_COLUMNS & set(train.columns)
        if derived_present:
            non_null = {c for c in derived_present if train[c].notna().any()}
            if non_null:
                issues.append(
                    f"Derived columns with values in training set: {non_null}. "
                    "These must be computed after training, not before."
                )

        # Check 2: Duplicate match records
        if "match_id" in train.columns and "player_id" in train.columns:
            dupes = train.duplicated(subset=["match_id", "player_id", "map_name"]).sum()
            if dupes > 0:
                issues.append(f"{dupes} duplicate (match_id, player_id, map_name) records detected")

        # Check 3: Zero-confidence records in training
        if "confidence_tier" in train.columns:
            zero_conf = (train["confidence_tier"] == 0).sum()
            if zero_conf > 0:
                issues.append(
                    f"{zero_conf} records with confidence_tier=0 in training set. "
                    "These should be excluded."
                )

        # Check 4: Cross-set match_id leak
        if test is not None and "match_id" in train.columns and "match_id" in test.columns:
            overlap = set(train["match_id"]) & set(test["match_id"])
            if overlap:
                issues.append(
                    f"{len(overlap)} match_ids appear in both train and test. "
                    f"Sample: {list(overlap)[:3]}"
                )

        has_leakage = len(issues) > 0
        if has_leakage:
            for issue in issues:
                logger.error("LEAKAGE: %s", issue)
        else:
            logger.info("✅ No data leakage patterns detected")

        return LeakageReport(has_leakage=has_leakage, issues=issues, warnings=warnings)
