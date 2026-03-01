"""Tests for LeakageDetector — critical guardrail for data quality."""
import pandas as pd
import pytest

from analytics.src.guardrails.leakage_detector import LeakageDetector, LeakageReport


def make_df(
    n: int = 10,
    include_match_id: bool = True,
    include_player_id: bool = True,
    confidence_tier: float = 75.0,
    has_derived_cols: bool = False,
) -> pd.DataFrame:
    data = {
        "player_id": [f"p{i}" for i in range(n)],
        "acs": [200.0 + i * 5 for i in range(n)],
        "kills": [10 + i for i in range(n)],
        "confidence_tier": [confidence_tier] * n,
    }
    if include_match_id:
        data["match_id"] = [f"match_{i}" for i in range(n)]
        data["map_name"] = ["Ascent"] * n
    if has_derived_cols:
        data["sim_rating"] = [0.5] * n
        data["rar_score"] = [1.1] * n
    return pd.DataFrame(data)


class TestLeakageDetectorCleanData:
    def setup_method(self):
        self.detector = LeakageDetector()

    def test_clean_train_no_leakage(self):
        """Clean training set with no overlapping match_ids returns no leakage."""
        train = make_df(10)
        report = self.detector.detect(train)
        assert not report.has_leakage
        assert report.issues == []

    def test_returns_leakage_report_instance(self):
        df = make_df(5)
        report = self.detector.detect(df)
        assert isinstance(report, LeakageReport)

    def test_no_warnings_on_clean_data(self):
        df = make_df(5)
        report = self.detector.detect(df)
        # No structural issues
        assert not report.has_leakage


class TestLeakageDetectorDerivedColumns:
    def setup_method(self):
        self.detector = LeakageDetector()

    def test_derived_cols_in_training_flagged(self):
        """sim_rating and rar_score in training set should be flagged as leakage."""
        train = make_df(5, has_derived_cols=True)
        report = self.detector.detect(train)
        assert report.has_leakage
        assert len(report.issues) > 0
        # Issue message should mention derived columns
        combined = " ".join(report.issues)
        assert "sim_rating" in combined or "rar_score" in combined

    def test_derived_cols_all_null_not_flagged(self):
        """Derived columns present but entirely null should NOT be flagged."""
        train = make_df(5)
        train["sim_rating"] = None  # Present but all null
        report = self.detector.detect(train)
        assert not report.has_leakage


class TestLeakageDetectorDuplicates:
    def setup_method(self):
        self.detector = LeakageDetector()

    def test_duplicate_match_player_records_flagged(self):
        """Duplicate (match_id, player_id, map_name) rows should be detected."""
        df = make_df(5)
        duped = pd.concat([df, df.head(2)], ignore_index=True)
        report = self.detector.detect(duped)
        assert report.has_leakage
        assert any("duplicate" in issue.lower() for issue in report.issues)

    def test_unique_records_not_flagged(self):
        """Unique composite keys should not trigger duplicate detection."""
        df = make_df(10)
        report = self.detector.detect(df)
        assert not report.has_leakage


class TestLeakageDetectorZeroConfidence:
    def setup_method(self):
        self.detector = LeakageDetector()

    def test_zero_confidence_records_flagged(self):
        """Records with confidence_tier=0 must not be included in training."""
        df = make_df(8, confidence_tier=75.0)
        # Inject two zero-confidence records
        low_conf = make_df(2, confidence_tier=0.0)
        low_conf["player_id"] = ["zp0", "zp1"]
        low_conf["match_id"] = ["zm0", "zm1"]
        combined = pd.concat([df, low_conf], ignore_index=True)
        report = self.detector.detect(combined)
        assert report.has_leakage
        assert any("confidence_tier=0" in issue for issue in report.issues)

    def test_nonzero_confidence_passes(self):
        df = make_df(5, confidence_tier=50.0)
        report = self.detector.detect(df)
        assert not report.has_leakage


class TestLeakageDetectorCrossSetOverlap:
    def setup_method(self):
        self.detector = LeakageDetector()

    def test_match_id_overlap_between_train_and_test_flagged(self):
        """match_ids appearing in both train and test is a hard leakage violation."""
        train = make_df(5)
        # Test set shares the first 2 match IDs with train
        test = make_df(5)
        test["match_id"] = ["match_0", "match_1", "match_5", "match_6", "match_7"]
        report = self.detector.detect(train, test)
        assert report.has_leakage
        combined = " ".join(report.issues)
        assert "match_id" in combined or "train and test" in combined.lower()

    def test_disjoint_train_test_passes(self):
        """No overlap between train and test match_ids should pass."""
        train = make_df(5)
        test = make_df(5)
        test["match_id"] = [f"test_match_{i}" for i in range(5)]
        report = self.detector.detect(train, test)
        assert not report.has_leakage

    def test_detect_without_test_set(self):
        """detect() should work fine when test is not provided."""
        train = make_df(5)
        report = self.detector.detect(train)  # No test argument
        assert isinstance(report, LeakageReport)
