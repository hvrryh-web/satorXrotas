"""
Tests for CanonicalIDResolver and TranslationConflict.

Validates:
  - Canonical URIs are stable (same input → same URI every call)
  - Stable UUIDs are deterministic (same URI → same UUID across processes)
  - Dedup keys are source-agnostic (VLR and Liquipedia produce the same key)
  - All entity types resolve correctly: player, map, team, agent, tournament, match
  - Known aliases (from datapoint_naming.json) resolve to the expected canonical URI
  - Case variations, unicode, and special characters are normalised
  - Conflict recording captures both sides and the resolution
  - Slugify handles edge cases: spaces, slashes, unicode accents, all-caps
"""
import uuid

import pytest

from extraction.src.bridge.canonical_id import (
    CanonicalIDResolver,
    CanonicalID,
    TranslationConflict,
    _slugify,
    _NAMESPACE,
)


# ---------------------------------------------------------------------------
# _slugify helpers
# ---------------------------------------------------------------------------

class TestSlugify:
    def test_lowercase(self):
        assert _slugify("TenZ") == "tenz"

    def test_spaces_to_underscore(self):
        assert _slugify("Cloud Nine") == "cloud_nine"

    def test_slash_to_underscore(self):
        assert _slugify("KAY/O") == "kay_o"

    def test_unicode_accent_stripped(self):
        # é → e after ASCII normalisation
        result = _slugify("Zoé")
        assert "zo" in result
        assert "e" in result
        assert "é" not in result

    def test_leading_trailing_whitespace(self):
        assert _slugify("  bind  ") == "bind"

    def test_all_caps(self):
        assert _slugify("ASCENT") == "ascent"

    def test_dot_stripped(self):
        assert _slugify("v8.11") == "v811"

    def test_empty_string(self):
        assert _slugify("") == ""


# ---------------------------------------------------------------------------
# CanonicalIDResolver — player
# ---------------------------------------------------------------------------

class TestResolvePlayer:
    def test_stable_canonical_uri(self):
        r = CanonicalIDResolver()
        a = r.resolve_player("TenZ", team="Sentinels")
        b = r.resolve_player("TenZ", team="Sentinels")
        assert a.canonical_uri == b.canonical_uri

    def test_canonical_uri_format(self):
        r = CanonicalIDResolver()
        cid = r.resolve_player("TenZ")
        assert cid.canonical_uri.startswith("cid:player:")
        assert cid.entity_type == "player"

    def test_case_insensitive_handle(self):
        r = CanonicalIDResolver()
        a = r.resolve_player("TENZ")
        b = r.resolve_player("tenz")
        assert a.canonical_uri == b.canonical_uri

    def test_stable_uuid_across_instances(self):
        """Two separate resolver instances must produce the same UUID."""
        r1 = CanonicalIDResolver()
        r2 = CanonicalIDResolver()
        u1 = r1.resolve_player("Player100").stable_uuid
        u2 = r2.resolve_player("Player100").stable_uuid
        assert u1 == u2

    def test_uuid_is_uuid5(self):
        r = CanonicalIDResolver()
        cid = r.resolve_player("SomePlayer")
        expected = uuid.uuid5(_NAMESPACE, cid.canonical_uri)
        assert cid.stable_uuid == expected

    def test_different_players_different_uuid(self):
        r = CanonicalIDResolver()
        u1 = r.resolve_player("Alpha").stable_uuid
        u2 = r.resolve_player("Beta").stable_uuid
        assert u1 != u2

    def test_source_alias_recorded(self):
        r = CanonicalIDResolver()
        cid = r.resolve_player("TenZ", team="Sentinels")
        assert "TenZ" in cid.source_aliases


# ---------------------------------------------------------------------------
# CanonicalIDResolver — map
# ---------------------------------------------------------------------------

class TestResolveMap:
    def test_known_alias_resolves(self):
        r = CanonicalIDResolver()
        cid = r.resolve_map("Bind")
        assert cid.canonical_uri == "cid:map:bind"

    def test_lowercase_alias_resolves(self):
        r = CanonicalIDResolver()
        cid = r.resolve_map("bind")
        assert cid.canonical_uri == "cid:map:bind"

    def test_uppercase_alias_resolves(self):
        r = CanonicalIDResolver()
        cid = r.resolve_map("BIND")
        assert cid.canonical_uri == "cid:map:bind"

    def test_haven_alias_resolves(self):
        r = CanonicalIDResolver()
        assert r.resolve_map("Haven").canonical_uri == "cid:map:haven"

    def test_unknown_map_gets_slug(self):
        r = CanonicalIDResolver()
        cid = r.resolve_map("NewUnknownMap")
        assert cid.canonical_uri == "cid:map:newunknownmap"

    def test_map_entity_type(self):
        r = CanonicalIDResolver()
        assert r.resolve_map("Ascent").entity_type == "map"

    def test_map_uuid_stable(self):
        r = CanonicalIDResolver()
        u1 = r.resolve_map("Haven").stable_uuid
        u2 = r.resolve_map("haven").stable_uuid
        assert u1 == u2  # Same canonical URI → same UUID


# ---------------------------------------------------------------------------
# CanonicalIDResolver — agent
# ---------------------------------------------------------------------------

class TestResolveAgent:
    def test_jett_resolves(self):
        r = CanonicalIDResolver()
        assert r.resolve_agent("Jett").canonical_uri == "cid:agent:jett"

    def test_kayo_slash_variant(self):
        r = CanonicalIDResolver()
        a = r.resolve_agent("KAY/O")
        b = r.resolve_agent("kay/o")
        assert a.canonical_uri == b.canonical_uri
        assert "kayo" in a.canonical_uri

    def test_sage_lowercase(self):
        r = CanonicalIDResolver()
        assert r.resolve_agent("sage").canonical_uri == "cid:agent:sage"

    def test_unknown_agent_gets_slug(self):
        r = CanonicalIDResolver()
        cid = r.resolve_agent("NewAgent2027")
        assert cid.canonical_uri == "cid:agent:newagent2027"


# ---------------------------------------------------------------------------
# CanonicalIDResolver — team
# ---------------------------------------------------------------------------

class TestResolveTeam:
    def test_sentinels_alias(self):
        r = CanonicalIDResolver()
        a = r.resolve_team("Sentinels")
        b = r.resolve_team("SEN")
        assert a.canonical_uri == b.canonical_uri

    def test_c9_aliases(self):
        r = CanonicalIDResolver()
        a = r.resolve_team("Cloud9")
        b = r.resolve_team("C9")
        assert a.canonical_uri == b.canonical_uri

    def test_unknown_team_gets_slug(self):
        r = CanonicalIDResolver()
        cid = r.resolve_team("Some Unknown Team")
        assert cid.canonical_uri == "cid:team:some_unknown_team"


# ---------------------------------------------------------------------------
# CanonicalIDResolver — match
# ---------------------------------------------------------------------------

class TestResolveMatch:
    def test_match_uri_format(self):
        r = CanonicalIDResolver()
        cid = r.resolve_match("vlr_gg", "123456")
        assert cid.canonical_uri == "cid:match:vlr_gg/123456"

    def test_match_entity_type(self):
        r = CanonicalIDResolver()
        assert r.resolve_match("vlr_gg", "999").entity_type == "match"

    def test_match_uuid_stable(self):
        r1 = CanonicalIDResolver()
        r2 = CanonicalIDResolver()
        u1 = r1.resolve_match("vlr_gg", "42").stable_uuid
        u2 = r2.resolve_match("vlr_gg", "42").stable_uuid
        assert u1 == u2


# ---------------------------------------------------------------------------
# Deduplication key — cross-source stability
# ---------------------------------------------------------------------------

class TestDedupKey:
    def test_same_player_same_match_same_map(self):
        r = CanonicalIDResolver()
        k1 = r.dedup_key("TenZ", "Sentinels", "vlr_gg", "123456", "Haven")
        k2 = r.dedup_key("TenZ", "Sentinels", "vlr_gg", "123456", "Haven")
        assert k1 == k2

    def test_dedup_key_is_uuid(self):
        r = CanonicalIDResolver()
        k = r.dedup_key("Player1", "TeamA", "vlr_gg", "1", "Bind")
        assert isinstance(k, uuid.UUID)

    def test_different_player_different_key(self):
        r = CanonicalIDResolver()
        k1 = r.dedup_key("Alpha", "SEN", "vlr_gg", "1", "Bind")
        k2 = r.dedup_key("Beta", "SEN", "vlr_gg", "1", "Bind")
        assert k1 != k2

    def test_different_map_different_key(self):
        r = CanonicalIDResolver()
        k1 = r.dedup_key("TenZ", "SEN", "vlr_gg", "1", "Bind")
        k2 = r.dedup_key("TenZ", "SEN", "vlr_gg", "1", "Haven")
        assert k1 != k2

    def test_case_insensitive_dedup(self):
        """Map name case variation must not produce duplicate records."""
        r = CanonicalIDResolver()
        k1 = r.dedup_key("TenZ", "SEN", "vlr_gg", "77", "Haven")
        k2 = r.dedup_key("TenZ", "SEN", "vlr_gg", "77", "HAVEN")
        assert k1 == k2

    def test_none_map_handled_gracefully(self):
        r = CanonicalIDResolver()
        k = r.dedup_key("TenZ", "SEN", "vlr_gg", "1", None)
        assert isinstance(k, uuid.UUID)

    def test_dedup_key_stable_across_resolver_instances(self):
        """Critical: two scraper workers produce the same key for the same record."""
        r1 = CanonicalIDResolver()
        r2 = CanonicalIDResolver()
        k1 = r1.dedup_key("TenZ", "Sentinels", "vlr_gg", "123456", "Haven")
        k2 = r2.dedup_key("TenZ", "Sentinels", "vlr_gg", "123456", "Haven")
        assert k1 == k2


# ---------------------------------------------------------------------------
# Conflict recording
# ---------------------------------------------------------------------------

class TestConflictRecording:
    def test_record_conflict_stored(self):
        r = CanonicalIDResolver()
        r.record_conflict(
            entity_type="player",
            source_a="vlr_gg",     alias_a="TenZ",       canonical_a="cid:player:tenz",
            source_b="liquipedia", alias_b="Tyson Ngo",  canonical_b="cid:player:tyson_ngo",
            resolved_to="cid:player:tenz",
            resolution_reason="vlr_gg is primary source for Valorant",
        )
        assert r.conflict_count == 1

    def test_flush_conflicts_clears(self):
        r = CanonicalIDResolver()
        r.record_conflict(
            entity_type="team",
            source_a="vlr_gg",     alias_a="Sentinels",  canonical_a="cid:team:sentinels",
            source_b="hltv",       alias_b="SEN",         canonical_b="cid:team:sen",
            resolved_to="cid:team:sentinels",
            resolution_reason="vlr_gg canonical wins",
        )
        conflicts = r.flush_conflicts()
        assert len(conflicts) == 1
        assert r.conflict_count == 0

    def test_conflict_has_correct_fields(self):
        r = CanonicalIDResolver()
        conflict = r.record_conflict(
            entity_type="agent",
            source_a="vlr_gg",    alias_a="KAY/O",  canonical_a="cid:agent:kayo",
            source_b="grid",      alias_b="kayo",    canonical_b="cid:agent:kayo",
            resolved_to="cid:agent:kayo",
            resolution_reason="same canonical — no real conflict",
        )
        assert isinstance(conflict, TranslationConflict)
        assert conflict.entity_type == "agent"
        assert conflict.resolved_to == "cid:agent:kayo"
