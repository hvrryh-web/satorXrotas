"""Tests for KCRITR schema completeness and extraction bridge."""
from uuid import uuid4

import pytest

from extraction.src.bridge.extraction_bridge import ExtractionBridge, KCRITRRecord


EXPECTED_FIELDS = {
    "player_id", "name", "team", "region", "role",
    "kills", "deaths", "acs", "adr", "kast_pct",
    "role_adjusted_value", "replacement_level", "rar_score", "investment_grade",
    "headshot_pct", "first_blood", "clutch_wins", "agent", "economy_rating",
    "adjusted_kill_value", "sim_rating", "age", "peak_age_estimate", "career_stage",
    "match_id", "map_name", "tournament", "patch_version", "realworld_time",
    "data_source", "extraction_timestamp", "checksum_sha256", "confidence_tier",
    "separation_flag", "partner_datapoint_ref", "reconstruction_notes", "record_id",
}


class TestKCRITRSchema:
    def test_37_field_count(self):
        """KCRITR schema must have exactly 37 fields."""
        fields = KCRITRRecord.__dataclass_fields__
        assert len(fields) == 37, (
            f"Expected 37 fields, got {len(fields)}: {sorted(fields.keys())}"
        )

    def test_all_expected_fields_present(self):
        """All named KCRITR fields must be present."""
        fields = set(KCRITRRecord.__dataclass_fields__.keys())
        missing = EXPECTED_FIELDS - fields
        assert not missing, f"Missing fields: {missing}"

    def test_separation_flag_always_zero_on_raw(self):
        """Raw extraction bridge records must always have separation_flag=0."""
        bridge = ExtractionBridge()
        vlr_data = {
            "player": "TestPlayer", "team": "TeamX", "acs": "250",
            "kills": "15", "deaths": "12", "kast": "75%", "adr": "130",
            "hs_pct": "22%", "first_blood": "1", "clutch_win": "0", "agent": "Jett",
        }
        record = bridge.translate(vlr_data, match_id="test_match_001", checksum="a" * 64)
        assert record.separation_flag == 0

    def test_bridge_maps_acs_correctly(self):
        """ACS field must be a float within plausible range."""
        bridge = ExtractionBridge()
        vlr_data = {"player": "X", "acs": "278", "kills": "15", "deaths": "10",
                    "kast": "70%", "adr": "120", "hs_pct": "25%",
                    "first_blood": "2", "clutch_win": "1", "agent": "Raze"}
        record = bridge.translate(vlr_data, match_id="m001", checksum="b" * 64)
        # Range assertion — not hardcoded exact value
        assert 100.0 < record.acs < 500.0

    def test_bridge_handles_missing_optional_fields(self):
        """Bridge should produce a valid record even with minimal input."""
        bridge = ExtractionBridge()
        record = bridge.translate({}, match_id="minimal_match", checksum="c" * 64)
        assert record.match_id == "minimal_match"
        assert record.separation_flag == 0
        assert record.data_source == "vlr_gg"
