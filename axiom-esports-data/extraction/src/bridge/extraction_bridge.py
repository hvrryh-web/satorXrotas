"""
Extraction Bridge — Translates raw VLR extraction schema to 37-field KCRITR schema.
Mirrors the AgentBridge pattern from RadiantX: decouples scrape schema from analytics input.

Canonical ID integration
------------------------
Player UUIDs are now assigned via ``CanonicalIDResolver.resolve_player()``, making them
stable and source-agnostic.  The same player extracted from VLR.gg and Liquipedia will
get the same UUID because both resolve to the same ``cid:player:{handle}`` URI.

Field name translation
----------------------
All raw field dicts are pre-processed by ``FieldTranslator.translate(source, raw)``
before any field lookups, so the bridge never hard-codes VLR-specific field names.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from extraction.src.bridge.canonical_id import CanonicalIDResolver
from extraction.src.bridge.field_translator import FieldTranslator

logger = logging.getLogger(__name__)

# Module-level singletons — one resolver and translator per process
_RESOLVER = CanonicalIDResolver()
_TRANSLATOR = FieldTranslator()


@dataclass
class KCRITRRecord:
    """Static definition of the 37-field KCRITR schema (mirrors *Def pattern)."""
    # Identity (5)
    player_id: UUID
    name: str
    team: Optional[str]
    region: Optional[str]
    role: Optional[str]

    # Performance (5)
    kills: Optional[int]
    deaths: Optional[int]
    acs: Optional[float]
    adr: Optional[float]
    kast_pct: Optional[float]

    # RAR Metrics (4)
    role_adjusted_value: Optional[float]
    replacement_level: Optional[float]
    rar_score: Optional[float]
    investment_grade: Optional[str]

    # Extended performance (10)
    headshot_pct: Optional[float]
    first_blood: Optional[int]
    clutch_wins: Optional[int]
    agent: Optional[str]
    economy_rating: Optional[float]
    adjusted_kill_value: Optional[float]
    sim_rating: Optional[float]
    age: Optional[int]
    peak_age_estimate: Optional[int]
    career_stage: Optional[str]

    # Match context (5)
    match_id: str
    map_name: Optional[str]
    tournament: Optional[str]
    patch_version: Optional[str]
    realworld_time: Optional[str]

    # Data provenance (8)
    data_source: str
    extraction_timestamp: Optional[str]
    checksum_sha256: Optional[str]
    confidence_tier: Optional[float]
    separation_flag: int
    partner_datapoint_ref: Optional[UUID]
    reconstruction_notes: Optional[str]
    record_id: Optional[int]


class ExtractionBridge:
    """
    Converts raw VLR.gg parsed data into KCRITRRecord instances.
    Handles field mapping, null coalescing, and unit conversion.
    """

    VLR_TO_KCRITR_MAP = {
        "player":       "name",
        "rating":       "role_adjusted_value",
        "acs":          "acs",
        "kills":        "kills",
        "deaths":       "deaths",
        "assists":      None,       # No direct KCRITR field
        "kast":         "kast_pct",
        "adr":          "adr",
        "hs_pct":       "headshot_pct",
        "first_blood":  "first_blood",
        "clutch_win":   "clutch_wins",
        "agent":        "agent",
    }

    def translate(
        self,
        vlr_data: dict[str, Any],
        match_id: str,
        checksum: str,
        confidence_tier: float = 75.0,
        separation_flag: int = 0,
        source: str = "vlr_gg",
    ) -> "KCRITRRecord":
        """
        Translate a single parsed row into a KCRITRRecord.

        Steps
        -----
        1. Normalise field names via ``FieldTranslator.translate(source, vlr_data)``.
        2. Resolve the player's stable UUID via ``CanonicalIDResolver``.
        3. Resolve canonical map/agent names for consistent downstream joins.
        4. Log unmapped fields for schema-drift monitoring.
        """
        # Step 1 — normalise field names
        canonical_data, unmapped = _TRANSLATOR.translate(source, vlr_data)
        if unmapped:
            logger.warning(
                "translate(%s): %d unmapped field(s): %s", source, len(unmapped), unmapped
            )

        # Fall back to raw dict lookup for any remaining fields not in the
        # canonical map (e.g. legacy callers that pre-translate their own dicts)
        def _get(canonical_key: str, raw_fallback: Optional[str] = None) -> Any:
            if canonical_key in canonical_data:
                return canonical_data[canonical_key]
            if raw_fallback and raw_fallback in vlr_data:
                return vlr_data[raw_fallback]
            return vlr_data.get(canonical_key)

        raw_name = _get("name", "player") or ""
        raw_team = _get("team") or ""

        # Step 2 — stable, source-agnostic player UUID
        player_cid = _RESOLVER.resolve_player(raw_name, team=raw_team or None, source=source)

        # Step 3 — canonical map and agent names
        raw_map = _get("map_name", "map")
        raw_agent = _get("agent")

        canonical_map: Optional[str] = None
        if raw_map:
            map_cid = _RESOLVER.resolve_map(raw_map, source=source)
            canonical_map = map_cid.canonical_uri

        canonical_agent: Optional[str] = None
        if raw_agent:
            agent_cid = _RESOLVER.resolve_agent(raw_agent, source=source)
            canonical_agent = agent_cid.canonical_uri

        return KCRITRRecord(
            player_id=player_cid.stable_uuid,
            name=raw_name,
            team=raw_team or None,
            region=_get("region"),
            role=None,  # Assigned by role_classifier.py
            kills=self._safe_int(_get("kills")),
            deaths=self._safe_int(_get("deaths")),
            acs=self._safe_float(_get("acs")),
            adr=self._safe_float(_get("adr")),
            kast_pct=self._safe_float(_get("kast_pct")),
            role_adjusted_value=None,
            replacement_level=None,
            rar_score=None,
            investment_grade=None,
            headshot_pct=self._safe_float(_get("headshot_pct")),
            first_blood=self._safe_int(_get("first_blood")),
            clutch_wins=self._safe_int(_get("clutch_wins")),
            agent=canonical_agent or raw_agent,
            economy_rating=None,
            adjusted_kill_value=None,
            sim_rating=None,
            age=None,
            peak_age_estimate=None,
            career_stage=None,
            match_id=match_id,
            map_name=canonical_map or raw_map,
            tournament=_get("tournament"),
            patch_version=_get("patch_version", "patch"),
            realworld_time=_get("realworld_time", "match_date"),
            data_source=source,
            extraction_timestamp=None,
            checksum_sha256=checksum,
            confidence_tier=confidence_tier,
            separation_flag=separation_flag,
            partner_datapoint_ref=None,
            reconstruction_notes=None,
            record_id=None,
        )

    @staticmethod
    def _safe_int(value: Any) -> Optional[int]:
        try:
            return int(value) if value is not None else None
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        try:
            return float(str(value).strip("%")) if value is not None else None
        except (ValueError, TypeError):
            return None

    def transform(self, raw: "RawMatchData") -> "list[KCRITRRecord]":
        """Convert a RawMatchData (from MatchParser) into a list of KCRITRRecords.

        Sets ``separation_flag=0`` (raw) for live records and ``separation_flag=9``
        for example-corpus records (match_id starting with "EXAMPLE_").
        Sets ``data_source='vlr_gg'`` and ``extraction_timestamp`` to UTC now.
        Checksums are computed per-player row via ``integrity_checker.compute_checksum``.

        Example records are NEVER stored in the live DB — callers must pass them
        to ``ExampleCorpus.security_check()`` and then discard them.
        """
        from extraction.src.storage.integrity_checker import compute_checksum
        from extraction.src.storage.example_corpus import ExampleCorpus, EXAMPLE_SEPARATION_FLAG

        is_example = ExampleCorpus.is_example(raw.vlr_match_id)
        sep_flag = EXAMPLE_SEPARATION_FLAG if is_example else 0

        records: list[KCRITRRecord] = []
        ts = datetime.now(tz=timezone.utc).isoformat()

        for player_row in raw.players:
            row_bytes = str(player_row).encode()
            checksum = compute_checksum(row_bytes)
            record = self.translate(
                vlr_data={
                    **player_row,
                    "map": raw.map_name,
                    "tournament": raw.tournament,
                    "patch": raw.patch_version,
                    "match_date": raw.match_date,
                },
                match_id=raw.vlr_match_id,
                checksum=checksum,
                confidence_tier=75.0,
                separation_flag=sep_flag,
            )
            record.extraction_timestamp = ts
            records.append(record)

        return records
