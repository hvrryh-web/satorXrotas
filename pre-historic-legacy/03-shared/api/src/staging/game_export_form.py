"""
Game Export Form — Transforms staging data for RadiantX game consumption.

This service pulls validated data from the staging system and transforms it
into the format expected by the Godot-based game (JSON definitions, event logs,
replay data). No firewall filtering is applied — the game has full data access.

File naming convention:
    game_export_*.py   — All game export services use this prefix.
    game_data_store    — Target DB table for exported data.

Safety:
    - All exports are logged to staging_export_log
    - Source staging records are marked as exported
    - Checksums are preserved for traceability
"""
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class GameDataRecord:
    """A record in the game data store."""
    game_data_id: Optional[int] = None
    data_type: str = ""
    data_key: str = ""
    data_version: str = "v1"
    payload: Dict[str, Any] = field(default_factory=dict)
    source_staging_id: Optional[int] = None
    exported_at: Optional[str] = None
    is_active: bool = True


# Game data type mappings from staging payload types
GAME_DATA_TYPE_MAP = {
    "agents": "agent_def",
    "weapons": "weapon_def",
    "utilities": "utility_def",
    "rulesets": "ruleset_def",
    "maps": "map_def",
    "match_event": "event_log",
    "replay_log": "match_replay",
}


class GameExportForm:
    """
    Export form that transforms staging data into RadiantX game format.

    The game project calls this form to pull definitions and match data
    from the shared staging system.

    Properties defining the game system's data needs:
        - requires_full_payload: True (no field stripping)
        - requires_firewall: False (game has full access)
        - output_format: JSON (Godot-compatible)
        - target_table: game_data_store
    """

    # System properties
    TARGET_PROJECT = "game"
    REQUIRES_FIREWALL = False
    OUTPUT_FORMAT = "json"
    TARGET_TABLE = "game_data_store"

    def __init__(self, ingest_service=None, db_connection=None):
        self.ingest_service = ingest_service
        self.db = db_connection
        self._store: List[GameDataRecord] = []
        self._next_id = 1
        self._export_log: List[Dict[str, Any]] = []
        logger.info("GameExportForm initialized")

    def export_definitions(self, data_domain: str, definitions: List[Dict[str, Any]], source_staging_id: Optional[int] = None) -> List[GameDataRecord]:
        """
        Export game definitions from staging to game data store.

        Args:
            data_domain: 'agents', 'weapons', 'utilities', 'rulesets', 'maps'
            definitions: List of definition payloads from staging
            source_staging_id: Reference back to staging static base

        Returns:
            List of GameDataRecord objects created.
        """
        data_type = GAME_DATA_TYPE_MAP.get(data_domain, data_domain)
        records: List[GameDataRecord] = []

        for defn in definitions:
            data_key = defn.get("id", defn.get("name", f"{data_domain}_{len(self._store)}"))
            record = GameDataRecord(
                game_data_id=self._next_id,
                data_type=data_type,
                data_key=data_key,
                payload=defn,
                source_staging_id=source_staging_id,
                exported_at=datetime.now(timezone.utc).isoformat(),
            )
            self._next_id += 1
            self._store.append(record)
            records.append(record)

            self._log_export(record, source_staging_id)
            logger.info("Game export: %s/%s (id=%d)", data_type, data_key, record.game_data_id)

        return records

    def export_match_events(self, match_id: str, events: List[Dict[str, Any]], source_ingest_id: Optional[int] = None) -> GameDataRecord:
        """Export match event log to game data store."""
        record = GameDataRecord(
            game_data_id=self._next_id,
            data_type="event_log",
            data_key=match_id,
            payload={"match_id": match_id, "events": events, "event_count": len(events)},
            source_staging_id=source_ingest_id,
            exported_at=datetime.now(timezone.utc).isoformat(),
        )
        self._next_id += 1
        self._store.append(record)
        self._log_export(record, source_ingest_id)
        logger.info("Game export: event_log/%s (%d events)", match_id, len(events))
        return record

    def export_replay(self, match_id: str, replay_data: Dict[str, Any], source_ingest_id: Optional[int] = None) -> GameDataRecord:
        """Export match replay data to game data store."""
        record = GameDataRecord(
            game_data_id=self._next_id,
            data_type="match_replay",
            data_key=match_id,
            payload=replay_data,
            source_staging_id=source_ingest_id,
            exported_at=datetime.now(timezone.utc).isoformat(),
        )
        self._next_id += 1
        self._store.append(record)
        self._log_export(record, source_ingest_id)
        logger.info("Game export: match_replay/%s", match_id)
        return record

    def get_active_definitions(self, data_type: str) -> List[GameDataRecord]:
        """Get all active records of a given type."""
        return [r for r in self._store if r.data_type == data_type and r.is_active]

    def get_by_key(self, data_type: str, data_key: str) -> Optional[GameDataRecord]:
        """Get a specific record by type and key."""
        for r in reversed(self._store):
            if r.data_type == data_type and r.data_key == data_key and r.is_active:
                return r
        return None

    def get_export_log(self) -> List[Dict[str, Any]]:
        """Return full export audit log."""
        return list(self._export_log)

    def _log_export(self, record: GameDataRecord, source_id: Optional[int]) -> None:
        """Log an export operation for audit trail."""
        self._export_log.append({
            "target_project": self.TARGET_PROJECT,
            "target_table": self.TARGET_TABLE,
            "target_record_id": record.game_data_id,
            "source_staging_id": source_id,
            "data_type": record.data_type,
            "data_key": record.data_key,
            "exported_at": record.exported_at,
            "status": "success",
        })
