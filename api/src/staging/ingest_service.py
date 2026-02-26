"""
Staging Ingest Service — Central data intake for the SATOR staging system.

All data entering the platform (from game, analytics, scrapers, or manual entry)
passes through this service. It validates, checksums, and queues data for export
to project-specific stores.

Safety Protocols:
    - All payloads are checksummed (SHA-256) before storage
    - Duplicate detection via checksum prevents re-ingestion
    - Payloads are validated against expected schemas before acceptance
    - Web-bound data is firewall-checked at ingest time
    - All operations are logged for auditability
"""
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SourceSystem(str, Enum):
    GAME = "game"
    ANALYTICS = "analytics"
    SCRAPER = "scraper"
    MANUAL = "manual"


class PayloadType(str, Enum):
    MATCH_EVENT = "match_event"
    PLAYER_STAT = "player_stat"
    GAME_DEFINITION = "game_definition"
    REPLAY_LOG = "replay_log"


class IngestStatus(str, Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"
    EXPORTED = "exported"


# Firewall: fields that must NEVER appear in web-bound data
GAME_ONLY_FIELDS = frozenset([
    "internalAgentState",
    "radarData",
    "detailedReplayFrameData",
    "simulationTick",
    "seedValue",
    "visionConeData",
    "smokeTickData",
    "recoilPattern",
])

# Required fields per payload type
REQUIRED_FIELDS: Dict[str, List[str]] = {
    PayloadType.MATCH_EVENT: ["match_id", "event_type", "tick"],
    PayloadType.PLAYER_STAT: ["player_id", "match_id"],
    PayloadType.GAME_DEFINITION: ["id", "data_domain"],
    PayloadType.REPLAY_LOG: ["match_id", "events"],
}


@dataclass
class IngestRecord:
    """A single record in the staging ingest queue."""
    ingest_id: Optional[int] = None
    source_system: str = ""
    payload_type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    checksum_sha256: str = ""
    status: str = IngestStatus.PENDING
    validation_errors: List[str] = field(default_factory=list)
    ingested_at: Optional[str] = None
    validated_at: Optional[str] = None
    exported_at: Optional[str] = None
    target_project: Optional[str] = None
    ingested_by: str = "system"


def compute_checksum(payload: Dict[str, Any]) -> str:
    """Compute SHA-256 checksum of a JSON payload (deterministic serialization)."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_payload(payload_type: str, payload: Dict[str, Any]) -> List[str]:
    """Validate payload against expected schema. Returns list of errors (empty = valid)."""
    errors: List[str] = []

    required = REQUIRED_FIELDS.get(payload_type, [])
    for field_name in required:
        if field_name not in payload:
            errors.append(f"Missing required field: {field_name}")

    if not payload:
        errors.append("Payload is empty")

    return errors


def check_firewall(payload: Dict[str, Any]) -> List[str]:
    """Check payload for game-only fields that must not reach the web. Returns violations."""
    violations: List[str] = []
    for key in payload:
        if key in GAME_ONLY_FIELDS:
            violations.append(f"FIREWALL VIOLATION: game-only field '{key}' found in payload")
    # Recurse into nested dicts
    for key, value in payload.items():
        if isinstance(value, dict):
            nested = check_firewall(value)
            violations.extend(nested)
    return violations


class StagingIngestService:
    """
    Central ingest service for the SATOR staging system.

    Usage:
        service = StagingIngestService(db_connection)
        record = service.ingest(
            source_system="game",
            payload_type="match_event",
            payload={"match_id": "m001", "event_type": "kill", "tick": 100},
            ingested_by="match_engine"
        )
    """

    def __init__(self, db_connection=None):
        """
        Initialize with optional DB connection.
        If None, operates in memory-only mode (for testing/dev).
        """
        self.db = db_connection
        self._queue: List[IngestRecord] = []
        self._next_id = 1
        logger.info("StagingIngestService initialized (db=%s)", "connected" if db_connection else "memory-only")

    def ingest(
        self,
        source_system: str,
        payload_type: str,
        payload: Dict[str, Any],
        ingested_by: str = "system",
        target_project: Optional[str] = None,
    ) -> IngestRecord:
        """
        Ingest a data payload into the staging queue.

        Steps:
            1. Compute checksum
            2. Check for duplicates
            3. Validate payload structure
            4. Check firewall (for web-bound data)
            5. Queue for export

        Returns:
            IngestRecord with status and any validation errors.
        """
        now = datetime.now(timezone.utc).isoformat()
        checksum = compute_checksum(payload)

        # Duplicate check
        for existing in self._queue:
            if existing.checksum_sha256 == checksum:
                logger.info("Duplicate payload detected (checksum=%s) — skipping", checksum[:12])
                return existing

        record = IngestRecord(
            ingest_id=self._next_id,
            source_system=source_system,
            payload_type=payload_type,
            payload=payload,
            checksum_sha256=checksum,
            ingested_at=now,
            ingested_by=ingested_by,
            target_project=target_project,
        )
        self._next_id += 1

        # Validate
        errors = validate_payload(payload_type, payload)

        # Firewall check for web-bound data
        if target_project in ("web", "both"):
            fw_violations = check_firewall(payload)
            errors.extend(fw_violations)

        if errors:
            record.status = IngestStatus.REJECTED
            record.validation_errors = errors
            logger.warning("Payload rejected: %s", errors)
        else:
            record.status = IngestStatus.VALIDATED
            record.validated_at = now
            logger.info("Payload ingested and validated (id=%d, type=%s)", record.ingest_id, payload_type)

        self._queue.append(record)

        # Persist to DB if available
        if self.db:
            self._persist_record(record)

        return record

    def get_pending(self, target_project: Optional[str] = None) -> List[IngestRecord]:
        """Get all validated records pending export, optionally filtered by project."""
        results = [r for r in self._queue if r.status == IngestStatus.VALIDATED]
        if target_project:
            results = [r for r in results if r.target_project in (target_project, "both", None)]
        return results

    def mark_exported(self, ingest_id: int, target_project: str) -> None:
        """Mark a record as exported to a project."""
        for record in self._queue:
            if record.ingest_id == ingest_id:
                record.status = IngestStatus.EXPORTED
                record.exported_at = datetime.now(timezone.utc).isoformat()
                record.target_project = target_project
                logger.info("Record %d exported to %s", ingest_id, target_project)
                return
        raise ValueError(f"Ingest record {ingest_id} not found")

    def get_stats(self) -> Dict[str, Any]:
        """Return staging queue statistics."""
        total = len(self._queue)
        by_status = {}
        for record in self._queue:
            by_status[record.status] = by_status.get(record.status, 0) + 1
        return {
            "total_records": total,
            "by_status": by_status,
            "queue_healthy": total < 10000,  # warn if queue is large
        }

    def _persist_record(self, record: IngestRecord) -> None:
        """Persist an IngestRecord to the database (placeholder for DB integration)."""
        # TODO: Implement actual DB insert when connection is available
        logger.debug("Would persist record %d to DB", record.ingest_id)
