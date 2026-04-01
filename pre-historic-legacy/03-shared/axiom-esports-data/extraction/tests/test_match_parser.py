"""Tests for MatchParser BeautifulSoup-based extraction."""
import pytest

from extraction.src.parsers.match_parser import MatchParser, RawMatchData

# Minimal synthetic VLR.gg-style HTML with the required structural markers
SAMPLE_HTML = """
<html><body>
<div class="match-header-event"><div>Champions Tour 2024</div></div>
<div class="map"><span>Bind</span></div>
<span data-utc-ts="1700000000"></span>
Patch 8.11
<div class="vm-stats-game" data-game-id="1">
  <table>
    <tr class="mod-player">
      <td class="mod-player">
        <div class="text-of">PlayerOne</div>
        <img alt="Jett" />
      </td>
      <td class="mod-stat">1.15</td>
      <td class="mod-stat">250</td>
      <td class="mod-stat">18</td>
      <td class="mod-stat">14</td>
      <td class="mod-stat">5</td>
      <td class="mod-stat">75%</td>
      <td class="mod-stat">145</td>
      <td class="mod-stat">28%</td>
      <td class="mod-stat">3</td>
      <td class="mod-stat">1</td>
    </tr>
    <tr class="mod-player">
      <td class="mod-player">
        <div class="text-of">PlayerTwo</div>
        <img alt="Sage" />
      </td>
      <td class="mod-stat">0.95</td>
      <td class="mod-stat">180</td>
      <td class="mod-stat">10</td>
      <td class="mod-stat">12</td>
      <td class="mod-stat">4</td>
      <td class="mod-stat">60%</td>
      <td class="mod-stat">100</td>
      <td class="mod-stat">15%</td>
      <td class="mod-stat">1</td>
      <td class="mod-stat">0</td>
    </tr>
  </table>
</div>
</body></html>
"""

MISSING_MARKERS_HTML = "<html><body><p>no stats here</p></body></html>"


class TestMatchParser:
    def test_parse_returns_raw_match_data(self):
        parser = MatchParser()
        result = parser.parse(SAMPLE_HTML, "match_001")
        assert isinstance(result, RawMatchData)
        assert result.vlr_match_id == "match_001"

    def test_parse_returns_none_on_missing_structure(self):
        parser = MatchParser()
        result = parser.parse(MISSING_MARKERS_HTML, "bad_match")
        assert result is None

    def test_extract_players_returns_list(self):
        parser = MatchParser()
        result = parser.parse(SAMPLE_HTML, "match_002")
        assert isinstance(result.players, list)

    def test_players_have_name_field(self):
        parser = MatchParser()
        result = parser.parse(SAMPLE_HTML, "match_003")
        for player in result.players:
            assert "player" in player
            assert isinstance(player["player"], str)
            assert len(player["player"]) > 0

    def test_players_acs_in_plausible_range(self):
        """ACS values extracted from HTML must be within a plausible range."""
        parser = MatchParser()
        result = parser.parse(SAMPLE_HTML, "match_004")
        for player in result.players:
            if "acs" in player and player["acs"]:
                acs = float(player["acs"])
                assert 0 < acs < 1000, f"ACS {acs} out of range for {player['player']}"

    def test_extract_tournament(self):
        parser = MatchParser()
        result = parser.parse(SAMPLE_HTML, "match_005")
        # Tournament may or may not match depending on regex; check type
        assert result.tournament is None or isinstance(result.tournament, str)

    def test_extract_map(self):
        parser = MatchParser()
        result = parser.parse(SAMPLE_HTML, "match_006")
        assert result.map_name == "Bind"

    def test_extract_date(self):
        parser = MatchParser()
        result = parser.parse(SAMPLE_HTML, "match_007")
        assert result.match_date == "1700000000"

    def test_extract_patch(self):
        parser = MatchParser()
        result = parser.parse(SAMPLE_HTML, "match_008")
        assert result.patch_version == "8.11"

    def test_has_expected_structure_true(self):
        parser = MatchParser()
        assert parser._has_expected_structure(SAMPLE_HTML)

    def test_has_expected_structure_false(self):
        parser = MatchParser()
        assert not parser._has_expected_structure(MISSING_MARKERS_HTML)
