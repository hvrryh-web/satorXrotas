"""
Overfitting Guard — Adversarial validation to detect train/test distribution shift.
If a model can distinguish train from test better than chance, leakage is present.
"""
import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

LEAKAGE_THRESHOLD = 0.55  # RF score above this indicates distribution shift
MIN_SAMPLE_MAPS = 50       # From config/overfitting_guardrails.json
MAX_SAMPLE_MAPS = 200      # Elite player ceiling — downsample via temporal decay


@dataclass
class OverfittingReport:
    classifier_score: float
    leakage_detected: bool
    n_train: int
    n_test: int
    top_discriminating_features: list[str]
    notes: str = ""


class OverfittingGuard:
    """
    Adversarial validation: trains a RandomForestClassifier to distinguish
    training records from test records. Score > 0.55 indicates leakage.
    """

    FEATURE_COLS = ["acs", "kills", "deaths", "adr", "kast_pct",
                    "headshot_pct", "first_blood", "clutch_wins"]

    def validate(
        self,
        train: pd.DataFrame,
        test: pd.DataFrame,
    ) -> OverfittingReport:
        """
        Run adversarial validation.
        Raises OverfittingAlert if distribution shift is detected.
        """
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import cross_val_score

        feature_cols = [c for c in self.FEATURE_COLS if c in train.columns and c in test.columns]
        if not feature_cols:
            raise ValueError("No common feature columns found in train/test DataFrames")

        train_sample = self._apply_map_ceiling(train)
        test_sample = test.copy()

        X_train = train_sample[feature_cols].fillna(0)
        X_test = test_sample[feature_cols].fillna(0)

        X = pd.concat([X_train, X_test], ignore_index=True)
        y = np.concatenate([np.zeros(len(X_train)), np.ones(len(X_test))])

        clf = RandomForestClassifier(n_estimators=100, random_state=42)
        scores = cross_val_score(clf, X, y, cv=5, scoring="roc_auc")
        mean_score = float(scores.mean())

        # Feature importance for diagnostics
        clf.fit(X, y)
        importances = sorted(
            zip(feature_cols, clf.feature_importances_),
            key=lambda x: x[1], reverse=True
        )
        top_features = [f for f, _ in importances[:3]]

        leakage = mean_score > LEAKAGE_THRESHOLD
        report = OverfittingReport(
            classifier_score=mean_score,
            leakage_detected=leakage,
            n_train=len(X_train),
            n_test=len(X_test),
            top_discriminating_features=top_features,
        )

        if leakage:
            raise OverfittingAlert(
                f"Distribution shift detected: adversarial classifier AUC={mean_score:.3f} "
                f"> threshold {LEAKAGE_THRESHOLD}. "
                f"Top discriminating features: {top_features}"
            )

        logger.info(
            "✅ No distribution shift: adversarial AUC=%.3f (threshold=%.2f)",
            mean_score, LEAKAGE_THRESHOLD,
        )
        return report

    def _apply_map_ceiling(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Downsample elite players (>200 maps) using temporal decay weighting.
        Prevents famous-player bias in model training.
        """
        if "player_id" not in df.columns:
            return df

        counts = df.groupby("player_id").size()
        elite_players = counts[counts > MAX_SAMPLE_MAPS].index

        result_parts = [df[~df["player_id"].isin(elite_players)]]
        for player_id in elite_players:
            player_data = df[df["player_id"] == player_id].sort_values(
                "realworld_time", ascending=False
            )
            result_parts.append(player_data.head(MAX_SAMPLE_MAPS))

        return pd.concat(result_parts, ignore_index=True)

    def apply_sample_floor(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Exclude players with fewer than MIN_SAMPLE_MAPS appearances.
        Prevents small-sample elite bias.
        """
        if "player_id" not in df.columns:
            return df

        counts = df.groupby("player_id").size()
        qualified = counts[counts >= MIN_SAMPLE_MAPS].index
        excluded = len(counts) - len(qualified)
        if excluded:
            logger.warning(
                "Excluded %d players with < %d maps from training",
                excluded, MIN_SAMPLE_MAPS,
            )
        return df[df["player_id"].isin(qualified)]


class OverfittingAlert(Exception):
    """Raised when adversarial validation detects train/test distribution shift."""


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="training_set")
    args = parser.parse_args()
    print(f"Running overfitting scan on: {args.dataset}")
    # Production: load dataset from DB and run validate()
