"""
Tests for FieldTranslator.

Validates:
  - All four sources (vlr_gg, liquipedia, hltv, grid) translate to canonical KCRITR names
  - Unmapped fields are returned and logged (schema-drift detection)
  - translate_and_merge applies correct priority when sources conflict
  - Higher-priority source's value is kept on conflict
  - Null incoming values do NOT overwrite existing values
  - canonical_to_source reverse lookup works for all registered sources
  - known_sources() and known_canonical_fields() return non-empty lists
  - Comment keys (prefixed '_') are silently skipped
"""
import pytest

from extraction.src.bridge.field_translator import FieldTranslator, FieldConflict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_vlr_row(**overrides) -> dict:
    base = {
        "player":     "TenZ",
        "team":       "Sentinels",
        "acs":        "287",
        "kills":      "24",
        "deaths":     "18",
        "kast":       "74%",
        "adr":        "152.3",
        "hs_pct":     "28%",
        "first_blood": "3",
        "clutch_win":  "1",
        "agent":       "Jett",
    }
    base.update(overrides)
    return base


def make_liquipedia_row(**overrides) -> dict:
    base = {
        "player_name": "TenZ",
        "team_name":   "Sentinels",
        "average_combat_score": "289",
        "kill_count":           "25",
        "death_count":          "17",
        "kast_percentage":      "75%",
        "average_damage_round": "154.0",
        "headshot_percentage":  "29%",
        "first_blood_count":    "3",
        "clutch_count":         "1",
        "agent_name":           "Jett",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Basic translation — vlr_gg
# ---------------------------------------------------------------------------

class TestVlrTranslation:
    def test_player_maps_to_name(self):
        t = FieldTranslator()
        out, _ = t.translate("vlr_gg", {"player": "TenZ"})
        assert out["name"] == "TenZ"

    def test_kast_maps_to_kast_pct(self):
        t = FieldTranslator()
        out, _ = t.translate("vlr_gg", {"kast": "74%"})
        assert out["kast_pct"] == "74%"

    def test_hs_pct_maps_to_headshot_pct(self):
        t = FieldTranslator()
        out, _ = t.translate("vlr_gg", {"hs_pct": "28%"})
        assert out["headshot_pct"] == "28%"

    def test_clutch_win_maps_to_clutch_wins(self):
        t = FieldTranslator()
        out, _ = t.translate("vlr_gg", {"clutch_win": "2"})
        assert out["clutch_wins"] == "2"

    def test_assists_mapped_to_none_excluded(self):
        """assists has no KCRITR canonical field — must be silently dropped."""
        t = FieldTranslator()
        out, _ = t.translate("vlr_gg", {"assists": "5"})
        assert "assists" not in out

    def test_full_row_no_unmapped(self):
        t = FieldTranslator()
        _, unmapped = t.translate("vlr_gg", make_vlr_row())
        assert unmapped == []

    def test_unknown_vlr_field_is_unmapped(self):
        t = FieldTranslator()
        _, unmapped = t.translate("vlr_gg", {"player": "X", "new_future_field": "42"})
        assert "new_future_field" in unmapped

    def test_comment_keys_skipped(self):
        t = FieldTranslator()
        out, unmapped = t.translate("vlr_gg", {"_comment": "ignore me", "player": "X"})
        assert "_comment" not in out
        assert "_comment" not in unmapped


# ---------------------------------------------------------------------------
# Basic translation — liquipedia
# ---------------------------------------------------------------------------

class TestLiquipediaTranslation:
    def test_player_name_maps_to_name(self):
        t = FieldTranslator()
        out, _ = t.translate("liquipedia", {"player_name": "TenZ"})
        assert out["name"] == "TenZ"

    def test_kill_count_maps_to_kills(self):
        t = FieldTranslator()
        out, _ = t.translate("liquipedia", {"kill_count": "25"})
        assert out["kills"] == "25"

    def test_kast_percentage_maps_to_kast_pct(self):
        t = FieldTranslator()
        out, _ = t.translate("liquipedia", {"kast_percentage": "75%"})
        assert out["kast_pct"] == "75%"

    def test_full_row_produces_canonical_keys(self):
        t = FieldTranslator()
        out, _ = t.translate("liquipedia", make_liquipedia_row())
        assert "name" in out
        assert "kills" in out
        assert "acs" in out


# ---------------------------------------------------------------------------
# Basic translation — hltv
# ---------------------------------------------------------------------------

class TestHltvTranslation:
    def test_nickname_maps_to_name(self):
        t = FieldTranslator()
        out, _ = t.translate("hltv", {"nickname": "s1mple"})
        assert out["name"] == "s1mple"

    def test_total_kills_maps_to_kills(self):
        t = FieldTranslator()
        out, _ = t.translate("hltv", {"total_kills": "22"})
        assert out["kills"] == "22"

    def test_dmg_per_round_maps_to_adr(self):
        t = FieldTranslator()
        out, _ = t.translate("hltv", {"dmg_per_round": "88.4"})
        assert out["adr"] == "88.4"


# ---------------------------------------------------------------------------
# Basic translation — grid
# ---------------------------------------------------------------------------

class TestGridTranslation:
    def test_player_handle_maps_to_name(self):
        t = FieldTranslator()
        out, _ = t.translate("grid", {"playerHandle": "TenZ"})
        assert out["name"] == "TenZ"

    def test_clutches_won_maps_to_clutch_wins(self):
        t = FieldTranslator()
        out, _ = t.translate("grid", {"clutchesWon": "3"})
        assert out["clutch_wins"] == "3"

    def test_kast_percent_maps_to_kast_pct(self):
        t = FieldTranslator()
        out, _ = t.translate("grid", {"kastPercent": "77%"})
        assert out["kast_pct"] == "77%"


# ---------------------------------------------------------------------------
# Unknown source
# ---------------------------------------------------------------------------

class TestUnknownSource:
    def test_unknown_source_all_unmapped(self):
        t = FieldTranslator()
        out, unmapped = t.translate("mystery_source", {"player": "X", "acs": "200"})
        assert out == {}
        assert "player" in unmapped
        assert "acs" in unmapped


# ---------------------------------------------------------------------------
# translate_and_merge — conflict resolution
# ---------------------------------------------------------------------------

class TestTranslateAndMerge:
    def test_no_conflict_merges_cleanly(self):
        t = FieldTranslator()
        existing = {"name": "TenZ", "kills": "24"}
        merged, conflicts = t.translate_and_merge(
            existing=existing,
            existing_source="vlr_gg",
            incoming={"kill_count": "24"},
            incoming_source="liquipedia",
        )
        assert merged["kills"] == "24"
        assert conflicts == []

    def test_vlr_wins_over_liquipedia_on_conflict(self):
        """vlr_gg has higher priority than liquipedia."""
        t = FieldTranslator()
        existing = {"acs": "287"}
        merged, conflicts = t.translate_and_merge(
            existing=existing,
            existing_source="vlr_gg",
            incoming={"average_combat_score": "299"},  # Different value
            incoming_source="liquipedia",
        )
        assert merged["acs"] == "287"  # vlr_gg value kept
        assert len(conflicts) == 1
        assert conflicts[0].source_winner == "vlr_gg"
        assert conflicts[0].source_loser == "liquipedia"

    def test_higher_priority_source_wins(self):
        """grid > liquipedia in the priority order."""
        t = FieldTranslator()
        existing = {"kills": "20"}
        merged, conflicts = t.translate_and_merge(
            existing=existing,
            existing_source="grid",
            incoming={"kill_count": "22"},
            incoming_source="liquipedia",
        )
        assert merged["kills"] == "20"  # grid kept
        assert conflicts[0].source_winner == "grid"

    def test_null_incoming_does_not_overwrite(self):
        t = FieldTranslator()
        existing = {"name": "TenZ"}
        merged, conflicts = t.translate_and_merge(
            existing=existing,
            existing_source="vlr_gg",
            incoming={"player_name": None},
            incoming_source="liquipedia",
        )
        assert merged["name"] == "TenZ"
        assert conflicts == []

    def test_new_field_from_incoming_added(self):
        """A field not in existing should always be taken from incoming."""
        t = FieldTranslator()
        existing = {"name": "TenZ"}
        merged, conflicts = t.translate_and_merge(
            existing=existing,
            existing_source="vlr_gg",
            incoming={"kast_percentage": "74%"},
            incoming_source="liquipedia",
        )
        assert merged["kast_pct"] == "74%"
        assert conflicts == []

    def test_conflict_dataclass_has_all_fields(self):
        t = FieldTranslator()
        existing = {"adr": "150"}
        merged, conflicts = t.translate_and_merge(
            existing=existing,
            existing_source="vlr_gg",
            incoming={"average_damage_round": "160"},
            incoming_source="liquipedia",
        )
        c = conflicts[0]
        assert isinstance(c, FieldConflict)
        assert c.canonical_field == "adr"
        assert c.value_winner == "150"
        assert c.value_loser == "160"


# ---------------------------------------------------------------------------
# Reverse lookup and metadata
# ---------------------------------------------------------------------------

class TestMetadata:
    def test_canonical_to_source_vlr(self):
        t = FieldTranslator()
        src_field = t.canonical_to_source("vlr_gg", "kast_pct")
        assert src_field == "kast"

    def test_canonical_to_source_liquipedia(self):
        t = FieldTranslator()
        src_field = t.canonical_to_source("liquipedia", "kills")
        assert src_field == "kill_count"

    def test_canonical_to_source_unknown_returns_none(self):
        t = FieldTranslator()
        assert t.canonical_to_source("vlr_gg", "nonexistent_field") is None

    def test_known_sources_not_empty(self):
        t = FieldTranslator()
        sources = t.known_sources()
        assert len(sources) >= 4
        assert "vlr_gg" in sources
        assert "liquipedia" in sources

    def test_known_canonical_fields_not_empty(self):
        t = FieldTranslator()
        fields = t.known_canonical_fields()
        assert len(fields) > 0
        assert "kills" in fields
        assert "acs" in fields
        assert "kast_pct" in fields
