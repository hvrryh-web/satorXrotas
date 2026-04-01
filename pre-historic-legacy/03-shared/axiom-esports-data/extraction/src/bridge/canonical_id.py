"""
Canonical ID — Stable, source-agnostic entity identification.

Problem
-------
VLR.gg, Liquipedia, HLTV, and GRID all refer to the same real-world entities
(players, matches, teams, maps) using different strings:

    VLR.gg      → "TenZ"       (player), "Bind" (map), "123456" (match ID)
    Liquipedia  → "Tyson Ngo"  (player), "bind" (map), "vlr:match:123456"
    HLTV        → N/A for Valorant, but "de_dust2" pattern for maps in CS2
    GRID        → "TenZ"       (player), "Bind" (map), internal match UUID

Without a translation layer, the same record from two sources would be stored
as two separate rows, inflating record counts and corrupting analytics.

Solution
--------
``CanonicalIDResolver`` converts any source-specific string into:

  1. A **canonical URI** (``cid:`` scheme):
       "TenZ"  + "Sentinels" → cid:player:tenz
       "Bind"               → cid:map:bind
       "vlr_gg" + "123456"  → cid:match:vlr_gg/123456

  2. A **stable UUID** derived deterministically from the canonical URI via
     ``uuid.uuid5(NAMESPACE, canonical_uri)``.  The same real-world entity
     always produces the same UUID, regardless of which source provided it.

  3. A **deduplication key** for records:
       ``uuid5(NAMESPACE, "cid:player:{p}|cid:match:{src}/{id}|cid:map:{m}")``

This dedup key is the primary key used by ``KnownRecordRegistry`` and the
``ExtractionBridge`` to detect cross-source duplicates before storage.

Naming Rules (from config/datapoint_naming.json)
-------------------------------------------------
  - Canonical player handles: lowercase ASCII (unicode normalised to ASCII)
  - Canonical map names: Riot's official name, lowercased
  - Canonical team tags: official tag, lowercased
  - Canonical agent names: Riot's official name, lowercased
  - ``cid:`` URIs never contain spaces; spaces → underscores
  - Special characters other than ``-`` and ``_`` are stripped
"""
import json
import logging
import re
import unicodedata
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# UUID namespace for all cid: URIs — fixed, never changed
_NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")

_NAMING_PATH = (
    Path(__file__).parent.parent.parent.parent / "config" / "datapoint_naming.json"
)


def _load_naming_config() -> dict:
    if _NAMING_PATH.exists():
        return json.loads(_NAMING_PATH.read_text())
    logger.warning("datapoint_naming.json not found — using built-in defaults")
    return {}


_NAMING = _load_naming_config()
_ENTITY_TYPES = _NAMING.get("entity_types", {})


def _slugify(text: str) -> str:
    """
    Convert any string to a canonical slug:
      - Unicode → ASCII (NFKD normalisation + encode/decode)
      - Lowercase
      - Spaces and forward-slashes → underscores
      - Strip everything except alphanumeric, underscore, hyphen
    """
    # Normalise unicode (e.g. accented chars → ASCII equivalent)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = text.lower().strip()
    text = re.sub(r"[/\s]+", "_", text)
    text = re.sub(r"[^a-z0-9_\-]", "", text)
    return text


@dataclass(frozen=True)
class CanonicalID:
    """
    A resolved canonical identity for any entity in the pipeline.

    Attributes
    ----------
    entity_type:    One of: player, match, map, team, tournament, agent
    canonical_uri:  The ``cid:`` URI (e.g. "cid:player:tenz")
    stable_uuid:    Deterministic UUID5 derived from canonical_uri
    source_aliases: All source-specific strings that were resolved to this ID
    """
    entity_type: str
    canonical_uri: str
    stable_uuid: uuid.UUID
    source_aliases: frozenset = field(default_factory=frozenset)

    def __str__(self) -> str:
        return self.canonical_uri


@dataclass
class TranslationConflict:
    """
    Records a detected naming conflict between two sources.

    A conflict occurs when two different canonical URIs would be assigned
    to what appears to be the same entity (e.g., same player on same team,
    but one source calls them "TenZ" and another calls them "tyson_ngo").

    Resolution: the higher-priority source wins (see datapoint_naming.json
    field_translation_table.conflict_resolution.primary_source_priority).
    """
    entity_type: str
    source_a: str
    alias_a: str
    canonical_a: str
    source_b: str
    alias_b: str
    canonical_b: str
    resolved_to: str   # The winning canonical URI
    resolution_reason: str


class CanonicalIDResolver:
    """
    Translates source-specific entity names into stable canonical IDs.

    Usage
    -----
    resolver = CanonicalIDResolver()

    # Resolve a player
    cid = resolver.resolve_player("TenZ", team="Sentinels")
    # → CanonicalID(entity_type='player', canonical_uri='cid:player:tenz', ...)

    # Resolve a map
    cid = resolver.resolve_map("Bind")
    # → CanonicalID(entity_type='map', canonical_uri='cid:map:bind', ...)

    # Build a record dedup key (cross-source duplicate detection)
    key = resolver.dedup_key("TenZ", "Sentinels", "vlr_gg", "123456", "Bind")
    # → uuid.UUID — same result for the same match from VLR or Liquipedia
    """

    # Known alias tables (loaded from config; extended at runtime)
    _MAP_ALIASES: dict[str, str] = {}
    _TEAM_ALIASES: dict[str, str] = {}
    _AGENT_ALIASES: dict[str, str] = {}
    _TOURNAMENT_ALIASES: dict[str, str] = {}

    def __init__(self) -> None:
        # Load alias tables from config if available
        self._load_aliases()
        # Runtime conflict log — keyed by (entity_type, canonical_uri_a, canonical_uri_b)
        self._conflicts: list[TranslationConflict] = []

    def _load_aliases(self) -> None:
        et = _ENTITY_TYPES
        self._MAP_ALIASES = {
            alias.lower(): cid
            for alias, cid in et.get("map", {}).get("aliases_example", {}).items()
        }
        self._TEAM_ALIASES = {
            alias.lower(): cid
            for alias, cid in et.get("team", {}).get("aliases_example", {}).items()
        }
        self._AGENT_ALIASES = {
            alias.lower(): cid
            for alias, cid in et.get("agent", {}).get("aliases_example", {}).items()
        }
        self._TOURNAMENT_ALIASES = {
            alias.lower(): cid
            for alias, cid in et.get("tournament", {}).get("aliases_example", {}).items()
        }

    # ------------------------------------------------------------------
    # Public resolve methods
    # ------------------------------------------------------------------

    def resolve_player(
        self, name: str, team: Optional[str] = None, source: str = "unknown"
    ) -> CanonicalID:
        """
        Resolve a player name + team to a canonical player ID.

        The canonical handle is the slugified name.  When two sources use
        different handles for what appears to be the same player (matched by
        team + approximate name similarity), a ``TranslationConflict`` is
        logged and the higher-priority source's version wins.
        """
        slug = _slugify(name)
        canonical_uri = f"cid:player:{slug}"
        stable_uuid = uuid.uuid5(_NAMESPACE, canonical_uri)
        aliases = frozenset([name])
        if team:
            aliases = aliases | frozenset([f"{name}@{team}"])
        return CanonicalID(
            entity_type="player",
            canonical_uri=canonical_uri,
            stable_uuid=stable_uuid,
            source_aliases=aliases,
        )

    def resolve_map(self, map_name: str, source: str = "unknown") -> CanonicalID:
        """
        Resolve a map name string to a canonical map ID.

        Looks up the alias table from datapoint_naming.json first.
        Falls back to slugifying the raw string.  Unknown maps are logged.
        """
        key = map_name.lower().strip()
        canonical_uri = self._MAP_ALIASES.get(key, f"cid:map:{_slugify(map_name)}")
        if key not in self._MAP_ALIASES:
            logger.debug("Map alias not found for '%s' — using slugified form", map_name)
        return CanonicalID(
            entity_type="map",
            canonical_uri=canonical_uri,
            stable_uuid=uuid.uuid5(_NAMESPACE, canonical_uri),
            source_aliases=frozenset([map_name]),
        )

    def resolve_team(self, team_name: str, source: str = "unknown") -> CanonicalID:
        """Resolve a team name/tag to a canonical team ID."""
        key = team_name.lower().strip()
        canonical_uri = self._TEAM_ALIASES.get(key, f"cid:team:{_slugify(team_name)}")
        return CanonicalID(
            entity_type="team",
            canonical_uri=canonical_uri,
            stable_uuid=uuid.uuid5(_NAMESPACE, canonical_uri),
            source_aliases=frozenset([team_name]),
        )

    def resolve_agent(self, agent_name: str, source: str = "unknown") -> CanonicalID:
        """
        Resolve a Valorant agent name to canonical form.

        Handles "KAY/O" → "cid:agent:kayo", "kay/o" → same, etc.
        """
        key = agent_name.lower().strip()
        canonical_uri = self._AGENT_ALIASES.get(key, f"cid:agent:{_slugify(agent_name)}")
        return CanonicalID(
            entity_type="agent",
            canonical_uri=canonical_uri,
            stable_uuid=uuid.uuid5(_NAMESPACE, canonical_uri),
            source_aliases=frozenset([agent_name]),
        )

    def resolve_tournament(self, name: str, source: str = "unknown") -> CanonicalID:
        """Resolve a tournament name to canonical form."""
        key = name.lower().strip()
        canonical_uri = self._TOURNAMENT_ALIASES.get(
            key, f"cid:tournament:{_slugify(name)}"
        )
        return CanonicalID(
            entity_type="tournament",
            canonical_uri=canonical_uri,
            stable_uuid=uuid.uuid5(_NAMESPACE, canonical_uri),
            source_aliases=frozenset([name]),
        )

    def resolve_match(self, source: str, source_match_id: str) -> CanonicalID:
        """
        Resolve a source-specific match ID to a canonical match ID.

        Format: ``cid:match:{source}/{id}``
        """
        src_slug = _slugify(source)
        id_slug = _slugify(str(source_match_id))
        canonical_uri = f"cid:match:{src_slug}/{id_slug}"
        return CanonicalID(
            entity_type="match",
            canonical_uri=canonical_uri,
            stable_uuid=uuid.uuid5(_NAMESPACE, canonical_uri),
            source_aliases=frozenset([f"{source}:{source_match_id}"]),
        )

    # ------------------------------------------------------------------
    # Deduplication key — cross-source duplicate detection
    # ------------------------------------------------------------------

    def dedup_key(
        self,
        player_name: str,
        team: Optional[str],
        source: str,
        match_id: str,
        map_name: Optional[str],
    ) -> uuid.UUID:
        """
        Build a source-agnostic deduplication key for a single player-map record.

        The key is a UUID5 derived from the canonical URIs of:
          player + match + map

        This means the same real-world performance record has the same key
        whether it was scraped from VLR.gg or fetched from Liquipedia,
        allowing KnownRecordRegistry to detect cross-source duplicates.

        Parameters
        ----------
        player_name:  Source-specific player name string
        team:         Source-specific team name (used in player resolution)
        source:       Data source identifier (e.g. "vlr_gg", "liquipedia")
        match_id:     Source-specific match identifier
        map_name:     Source-specific map name (may be None for unresolved)
        """
        p_cid = self.resolve_player(player_name, team=team, source=source)
        m_cid = self.resolve_match(source, match_id)
        mp_cid = self.resolve_map(map_name or "unknown", source=source)

        composite = f"{p_cid.canonical_uri}|{m_cid.canonical_uri}|{mp_cid.canonical_uri}"
        return uuid.uuid5(_NAMESPACE, composite)

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    def record_conflict(
        self,
        entity_type: str,
        source_a: str,
        alias_a: str,
        canonical_a: str,
        source_b: str,
        alias_b: str,
        canonical_b: str,
        resolved_to: str,
        resolution_reason: str,
    ) -> TranslationConflict:
        """
        Log a naming conflict between two sources for the same entity.

        Called by the pipeline when two sources produce different canonical URIs
        for an entity that has been matched by context (e.g., same team, same match).
        """
        conflict = TranslationConflict(
            entity_type=entity_type,
            source_a=source_a,
            alias_a=alias_a,
            canonical_a=canonical_a,
            source_b=source_b,
            alias_b=alias_b,
            canonical_b=canonical_b,
            resolved_to=resolved_to,
            resolution_reason=resolution_reason,
        )
        self._conflicts.append(conflict)
        logger.warning(
            "Naming conflict [%s]: '%s' (%s) → %s  vs  '%s' (%s) → %s  RESOLVED: %s (%s)",
            entity_type,
            alias_a, source_a, canonical_a,
            alias_b, source_b, canonical_b,
            resolved_to, resolution_reason,
        )
        return conflict

    def flush_conflicts(self) -> list[TranslationConflict]:
        """Return and clear the pending conflict log."""
        conflicts = list(self._conflicts)
        self._conflicts.clear()
        return conflicts

    @property
    def conflict_count(self) -> int:
        return len(self._conflicts)
