"""
Extraction Bridge — Translates raw VLR extraction schema to 37-field KCRITR schema.
Mirrors the AgentBridge pattern from RadiantX: decouples scrape schema from analytics input.
"""
import logging
from dataclasses import dataclass
from typing import Any, Optional
from uuid import UUID, uuid4, uuid5, NAMESPACE_DNS

logger = logging.getLogger(__name__)


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
        "team":         "team",
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
    ) -> KCRITRRecord:
        """
        Translate a single VLR parsed row into a KCRITRRecord.
        Logs any unmapped fields as warnings for schema drift monitoring.
        """
        unmapped = [k for k in vlr_data if k not in self.VLR_TO_KCRITR_MAP]
        if unmapped:
            logger.warning("Unmapped VLR fields (potential schema drift): %s", unmapped)

        return KCRITRRecord(
            player_id=self._stable_player_id(
                vlr_data.get("player", ""), vlr_data.get("team", "")
            ),
            name=vlr_data.get("player", ""),
            team=vlr_data.get("team"),
            region=vlr_data.get("region"),
            role=None,  # Assigned by role_classifier.py in parsers
            kills=self._safe_int(vlr_data.get("kills")),
            deaths=self._safe_int(vlr_data.get("deaths")),
            acs=self._safe_float(vlr_data.get("acs")),
            adr=self._safe_float(vlr_data.get("adr")),
            kast_pct=self._safe_float(vlr_data.get("kast")),
            role_adjusted_value=None,   # Computed by analytics layer
            replacement_level=None,
            rar_score=None,
            investment_grade=None,
            headshot_pct=self._safe_float(vlr_data.get("hs_pct")),
            first_blood=self._safe_int(vlr_data.get("first_blood")),
            clutch_wins=self._safe_int(vlr_data.get("clutch_win")),
            agent=vlr_data.get("agent"),
            economy_rating=None,
            adjusted_kill_value=None,   # Computed by economy_inference.py
            sim_rating=None,
            age=None,
            peak_age_estimate=None,
            career_stage=None,
            match_id=match_id,
            map_name=vlr_data.get("map"),
            tournament=vlr_data.get("tournament"),
            patch_version=vlr_data.get("patch"),
            realworld_time=vlr_data.get("match_date"),
            data_source="vlr_gg",
            extraction_timestamp=None,
            checksum_sha256=checksum,
            confidence_tier=confidence_tier,
            separation_flag=separation_flag,
            partner_datapoint_ref=None,
            reconstruction_notes=None,
            record_id=None,
        )

    @staticmethod
    def _stable_player_id(name: str, team: str) -> UUID:
        """
        Derive a deterministic UUID (v5) from player name + team.
        Ensures the same player always receives the same UUID across parse calls.
        Uses uuid5 (SHA-1 namespace-based) per RFC 4122.
        """
        key = f"{name.strip().lower()}:{team.strip().lower()}"
        return uuid5(NAMESPACE_DNS, key)

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
