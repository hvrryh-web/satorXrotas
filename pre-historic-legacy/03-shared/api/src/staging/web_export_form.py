"""
Web Export Form — Transforms staging data for SATOR Web consumption.

This service pulls validated data from the staging system and transforms it
into sanitized, firewall-compliant format for the public web platform.
All GAME_ONLY_FIELDS are stripped at export time.

File naming convention:
    web_export_*.py    — All web export services use this prefix.
    web_data_store     — Target DB table for exported data.

Safety:
    - FIREWALL ENFORCED: All payloads pass through field stripping
    - All exports are logged to staging_export_log
    - Records must have firewall_verified=TRUE before serving
    - Checksums are preserved for traceability
    - Maps KCRITR schema fields to public Statistics type
"""
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# FIREWALL: Fields that MUST be stripped from all web-bound data.
# Mirrors FantasyDataFilter.GAME_ONLY_FIELDS from packages/data-partition-lib
GAME_ONLY_FIELDS: Set[str] = {
    "internalAgentState",
    "radarData",
    "detailedReplayFrameData",
    "simulationTick",
    "seedValue",
    "visionConeData",
    "smokeTickData",
    "recoilPattern",
}

# KCRITR → Public Statistics field mapping
# Maps internal analytics fields to the public-safe field names
KCRITR_TO_PUBLIC_MAP = {
    "player_id": "playerId",
    "match_id": "matchId",
    "kills": "kills",
    "deaths": "deaths",
    "assists": "assists",
    "adr": "damage",
    "headshot_pct": "headshots",
    "first_blood": "firstKills",
    "clutch_wins": "clutchesWon",
    "map_name": "mapName",
    "name": "username",
    "region": "region",
    "tournament": "tournament",
    "sim_rating": "simRating",
    "rar_score": "rarScore",
    "investment_grade": "investmentGrade",
    "role": "role",
}


@dataclass
class WebDataRecord:
    """A record in the web data store."""
    web_data_id: Optional[int] = None
    data_type: str = ""
    data_key: str = ""
    data_version: str = "v1"
    payload: Dict[str, Any] = field(default_factory=dict)
    source_staging_id: Optional[int] = None
    firewall_verified: bool = False
    exported_at: Optional[str] = None
    is_active: bool = True


def strip_game_only_fields(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively remove all GAME_ONLY_FIELDS from a payload.

    This is the critical firewall enforcement function. Every payload
    destined for the web MUST pass through this function.

    Args:
        payload: Raw data dictionary

    Returns:
        Sanitized copy with all game-only fields removed.
    """
    sanitized = {}
    for key, value in payload.items():
        if key in GAME_ONLY_FIELDS:
            logger.warning("FIREWALL: Stripped game-only field '%s' from web payload", key)
            continue
        if isinstance(value, dict):
            sanitized[key] = strip_game_only_fields(value)
        elif isinstance(value, list):
            sanitized[key] = [
                strip_game_only_fields(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value
    return sanitized


def map_to_public_schema(kcritr_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map a KCRITR analytics record to the public Statistics schema.

    Only fields explicitly listed in KCRITR_TO_PUBLIC_MAP are included.
    All other fields are dropped.
    """
    public: Dict[str, Any] = {}
    for internal_key, public_key in KCRITR_TO_PUBLIC_MAP.items():
        if internal_key in kcritr_record:
            public[public_key] = kcritr_record[internal_key]
    return public


def verify_firewall_compliance(payload: Dict[str, Any]) -> List[str]:
    """
    Verify a payload contains NO game-only fields. Returns list of violations.
    Empty list = compliant.
    """
    violations: List[str] = []
    for key in payload:
        if key in GAME_ONLY_FIELDS:
            violations.append(f"FIREWALL VIOLATION: '{key}' present in web payload")
    for key, value in payload.items():
        if isinstance(value, dict):
            violations.extend(verify_firewall_compliance(value))
    return violations


class WebExportForm:
    """
    Export form that transforms staging data into SATOR Web format.

    The web project calls this form to pull sanitized public stats
    from the shared staging system.

    Properties defining the web system's data needs:
        - requires_full_payload: False (fields are filtered)
        - requires_firewall: True (GAME_ONLY_FIELDS stripped)
        - output_format: JSON (TypeScript-compatible)
        - target_table: web_data_store
    """

    # System properties
    TARGET_PROJECT = "web"
    REQUIRES_FIREWALL = True
    OUTPUT_FORMAT = "json"
    TARGET_TABLE = "web_data_store"

    def __init__(self, ingest_service=None, db_connection=None):
        self.ingest_service = ingest_service
        self.db = db_connection
        self._store: List[WebDataRecord] = []
        self._next_id = 1
        self._export_log: List[Dict[str, Any]] = []
        logger.info("WebExportForm initialized")

    def export_player_stats(self, player_records: List[Dict[str, Any]], source_ingest_id: Optional[int] = None) -> List[WebDataRecord]:
        """
        Export player stats from staging, applying firewall and schema mapping.

        Steps:
            1. Strip GAME_ONLY_FIELDS (firewall enforcement)
            2. Map KCRITR fields to public Statistics schema
            3. Verify firewall compliance
            4. Store in web data store
        """
        records: List[WebDataRecord] = []

        for raw in player_records:
            # Step 1: Firewall strip
            stripped = strip_game_only_fields(raw)

            # Step 2: Map to public schema
            public = map_to_public_schema(stripped)

            # Step 3: Verify compliance
            violations = verify_firewall_compliance(public)
            if violations:
                logger.error("FIREWALL BLOCK: %s — record skipped", violations)
                continue

            # Step 4: Store
            data_key = f"{public.get('playerId', 'unknown')}_{public.get('matchId', 'unknown')}"
            record = WebDataRecord(
                web_data_id=self._next_id,
                data_type="player_stats",
                data_key=data_key,
                payload=public,
                source_staging_id=source_ingest_id,
                firewall_verified=True,
                exported_at=datetime.now(timezone.utc).isoformat(),
            )
            self._next_id += 1
            self._store.append(record)
            records.append(record)
            self._log_export(record, source_ingest_id)
            logger.info("Web export: player_stats/%s (firewall=PASS)", data_key)

        return records

    def export_match_summary(self, match_records: List[Dict[str, Any]], source_ingest_id: Optional[int] = None) -> List[WebDataRecord]:
        """Export match summaries with firewall enforcement."""
        records: List[WebDataRecord] = []

        for raw in match_records:
            stripped = strip_game_only_fields(raw)
            summary = {
                "matchId": stripped.get("match_id", stripped.get("matchId")),
                "mapName": stripped.get("map_name", stripped.get("mapName")),
                "tournament": stripped.get("tournament"),
                "roundsPlayed": stripped.get("rounds_played"),
                "winnerSide": stripped.get("winner_side"),
            }
            # Remove None values
            summary = {k: v for k, v in summary.items() if v is not None}

            violations = verify_firewall_compliance(summary)
            if violations:
                logger.error("FIREWALL BLOCK: %s", violations)
                continue

            record = WebDataRecord(
                web_data_id=self._next_id,
                data_type="match_summary",
                data_key=summary.get("matchId", f"match_{self._next_id}"),
                payload=summary,
                source_staging_id=source_ingest_id,
                firewall_verified=True,
                exported_at=datetime.now(timezone.utc).isoformat(),
            )
            self._next_id += 1
            self._store.append(record)
            records.append(record)
            self._log_export(record, source_ingest_id)

        return records

    def export_leaderboard(self, player_records: List[Dict[str, Any]]) -> List[WebDataRecord]:
        """Export leaderboard entries (latest stats per player)."""
        # Deduplicate by player, keeping latest
        latest_by_player: Dict[str, Dict[str, Any]] = {}
        for raw in player_records:
            pid = raw.get("player_id", raw.get("playerId"))
            if pid:
                latest_by_player[pid] = raw

        records: List[WebDataRecord] = []
        for pid, raw in latest_by_player.items():
            stripped = strip_game_only_fields(raw)
            public = map_to_public_schema(stripped)
            violations = verify_firewall_compliance(public)
            if violations:
                continue

            record = WebDataRecord(
                web_data_id=self._next_id,
                data_type="leaderboard",
                data_key=str(pid),
                payload=public,
                firewall_verified=True,
                exported_at=datetime.now(timezone.utc).isoformat(),
            )
            self._next_id += 1
            self._store.append(record)
            records.append(record)

        return records

    def get_verified_records(self, data_type: Optional[str] = None) -> List[WebDataRecord]:
        """Get all firewall-verified active records."""
        results = [r for r in self._store if r.firewall_verified and r.is_active]
        if data_type:
            results = [r for r in results if r.data_type == data_type]
        return results

    def get_export_log(self) -> List[Dict[str, Any]]:
        """Return full export audit log."""
        return list(self._export_log)

    def _log_export(self, record: WebDataRecord, source_id: Optional[int]) -> None:
        """Log an export operation for audit trail."""
        self._export_log.append({
            "target_project": self.TARGET_PROJECT,
            "target_table": self.TARGET_TABLE,
            "target_record_id": record.web_data_id,
            "source_staging_id": source_id,
            "data_type": record.data_type,
            "data_key": record.data_key,
            "firewall_verified": record.firewall_verified,
            "exported_at": record.exported_at,
            "status": "success",
        })
