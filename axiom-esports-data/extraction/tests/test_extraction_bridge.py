"""Tests for ExtractionBridge transform() and translate() methods."""
import pytest

from extraction.src.bridge.extraction_bridge import ExtractionBridge, KCRITRRecord
from extraction.src.parsers.match_parser import RawMatchData


def _make_raw_match(num_players: int = 2) -> RawMatchData:
    players = [
        {
            "player": f"Player{i}",
            "team": "TeamA",
            "agent": "Jett",
            "rating": "1.10",
            "acs": "230",
            "kills": "16",
            "deaths": "13",
            "assists": "4",
            "kast": "72%",
            "adr": "135",
            "hs_pct": "22%",
            "first_blood": "2",
            "clutch_win": "1",
        }
        for i in range(num_players)
    ]
    return RawMatchData(
        vlr_match_id="test_match_99",
        tournament="VCT 2024",
        map_name="Haven",
        match_date="1700000000",
        patch_version="8.11",
        players=players,
    )


class TestExtractionBridgeTransform:
    def test_transform_returns_list(self):
        bridge = ExtractionBridge()
        raw = _make_raw_match(2)
        records = bridge.transform(raw)
        assert isinstance(records, list)

    def test_transform_count_matches_players(self):
        bridge = ExtractionBridge()
        raw = _make_raw_match(3)
        records = bridge.transform(raw)
        assert len(records) == 3

    def test_transform_empty_players(self):
        bridge = ExtractionBridge()
        raw = _make_raw_match(0)
        records = bridge.transform(raw)
        assert records == []

    def test_transform_separation_flag_zero(self):
        """All records from transform() must have separation_flag=0 (raw)."""
        bridge = ExtractionBridge()
        raw = _make_raw_match(2)
        for record in bridge.transform(raw):
            assert record.separation_flag == 0

    def test_transform_data_source_vlr_gg(self):
        bridge = ExtractionBridge()
        raw = _make_raw_match(1)
        record = bridge.transform(raw)[0]
        assert record.data_source == "vlr_gg"

    def test_transform_match_id_propagated(self):
        bridge = ExtractionBridge()
        raw = _make_raw_match(1)
        record = bridge.transform(raw)[0]
        assert record.match_id == "test_match_99"

    def test_transform_map_name_propagated(self):
        bridge = ExtractionBridge()
        raw = _make_raw_match(1)
        record = bridge.transform(raw)[0]
        assert record.map_name == "Haven"

    def test_transform_checksum_is_64_chars(self):
        bridge = ExtractionBridge()
        raw = _make_raw_match(1)
        record = bridge.transform(raw)[0]
        assert record.checksum_sha256 is not None
        assert len(record.checksum_sha256) == 64

    def test_transform_extraction_timestamp_set(self):
        bridge = ExtractionBridge()
        raw = _make_raw_match(1)
        record = bridge.transform(raw)[0]
        assert record.extraction_timestamp is not None
        assert isinstance(record.extraction_timestamp, str)

    def test_transform_acs_plausible_range(self):
        """ACS in produced records must be within plausible competitive range."""
        bridge = ExtractionBridge()
        raw = _make_raw_match(1)
        record = bridge.transform(raw)[0]
        assert record.acs is not None
        assert 50.0 < record.acs < 600.0

    def test_transform_produces_kcritr_records(self):
        bridge = ExtractionBridge()
        raw = _make_raw_match(2)
        for record in bridge.transform(raw):
            assert isinstance(record, KCRITRRecord)
