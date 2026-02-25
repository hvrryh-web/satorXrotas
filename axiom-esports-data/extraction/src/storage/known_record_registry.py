"""
Known Record Registry — Listing service for verified database records.

The registry is the single source of truth about what the pipeline has
already collected.  EpochHarvester MUST consult the registry via
``should_skip(match_id)`` before every fetch, so that:

  - Fully-processed matches are never re-scraped unnecessarily.
  - Excluded matches (corrupted, manual, schema-conflicted) are permanently
    bypassed until deliberately reinstated.
  - The DB exclusion list stays in sync with the file-based fallback.

Operating contract is defined in ``config/harvest_protocol.json``.
Both this service and EpochHarvester read that file to stay aligned.

Completeness definition (from harvest_protocol.json):
  A match_id is COMPLETE when:
    - At least 10 player records exist for that match
    - kills / deaths / acs / adr / kast_pct are all non-null
    - separation_flag = 0 (raw)
    - http_status = 200
    - checksum_sha256 is present
    - confidence_tier >= 50.0

Conflict rules (from harvest_protocol.json):
  - CHECKSUM_CONFLICT  → flag_content_drift, store new version, emit WARNING
  - PARTIAL_WRITE      → delete_and_retry (max 3), emit ERROR
  - CONCURRENT_SCRAPE  → first_writer_wins (dedup by checksum)
  - EPOCH_BOUNDARY     → assign to lower epoch
  - SCHEMA_DRIFT       → exclude + cache raw, emit CRITICAL, block analytics
"""
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_PROTOCOL_PATH = Path(__file__).parent.parent.parent.parent / "config" / "harvest_protocol.json"


def _load_protocol() -> dict:
    """Load the shared harvest protocol contract."""
    if _PROTOCOL_PATH.exists():
        return json.loads(_PROTOCOL_PATH.read_text())
    logger.warning("harvest_protocol.json not found at %s — using defaults", _PROTOCOL_PATH)
    return {}


PROTOCOL = _load_protocol()
_COMPLETENESS = PROTOCOL.get("completeness_definition", {})
_SKIP_POLICY = PROTOCOL.get("skip_policy", {})
_CONFLICT = PROTOCOL.get("conflict_resolution", {})

# Completeness thresholds (fall back to safe defaults)
MIN_PLAYER_COUNT = _COMPLETENESS.get("required_player_count_min", 10)
REQUIRED_NON_NULL = _COMPLETENESS.get("required_fields_non_null",
                                       ["kills", "deaths", "acs", "adr", "kast_pct"])
MIN_CONFIDENCE_TIER = _COMPLETENESS.get("required_confidence_tier_min", 50.0)


@dataclass
class ExclusionEntry:
    """A single entry in the exclusion list."""
    match_id: str
    reason_code: str           # One of the codes in harvest_protocol.json exclusion_reasons
    notes: str = ""
    excluded_at: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()
    )
    excluded_by: str = "system"   # "system" or agent/script name
    reinstated: bool = False       # Set True if manually reinstated


@dataclass
class RegistryStats:
    complete: int = 0
    pending: int = 0
    excluded: int = 0
    total_known: int = 0

    def as_dict(self) -> dict:
        return {
            "complete": self.complete,
            "pending": self.pending,
            "excluded": self.excluded,
            "total_known": self.total_known,
            "skip_rate_pct": round(
                100.0 * (self.complete + self.excluded) / max(self.total_known, 1), 1
            ),
        }


class KnownRecordRegistry:
    """
    Listing service that gates every EpochHarvester fetch decision.

    The registry maintains two in-process sets (populated from DB on startup):
      ``_complete``  — match IDs that fully satisfy completeness_definition
      ``_excluded``  — match IDs on the exclusion list (with reason codes)

    ``should_skip(match_id)``  is the primary entry point for the harvester.
    It returns True when a match is either complete or excluded, meaning the
    harvester should bypass it without any network I/O.

    When a DB connection is available (via DATABASE_URL env var) both sets
    are pre-populated at construction time.  Without a DB the registry
    operates in memory-only mode, which is safe for unit tests and CI.
    """

    VALID_EXCLUSION_REASONS = set(
        PROTOCOL.get("exclusion_reasons", {}).keys()
    ) or {
        "COMPLETE", "MANUAL_EXCLUDE", "DUPLICATE", "SCHEMA_CONFLICT",
        "CONTENT_DRIFT", "LOW_CONFIDENCE", "RATE_LIMIT_BAN",
    }

    def __init__(self, db_url: Optional[str] = None) -> None:
        self._db_url = db_url or os.environ.get("DATABASE_URL")
        self._complete: set[str] = set()       # match_ids fully processed
        self._excluded: dict[str, ExclusionEntry] = {}  # match_id → ExclusionEntry
        self._pending: set[str] = set()        # known but not complete

        if self._db_url:
            self._load_from_db()

    # ------------------------------------------------------------------
    # Primary query interface — used by EpochHarvester
    # ------------------------------------------------------------------

    def is_known(self, match_id: str) -> bool:
        """True if the match_id appears in any tracked set."""
        return (
            match_id in self._complete
            or match_id in self._excluded
            or match_id in self._pending
        )

    def is_complete(self, match_id: str) -> bool:
        """True if all completeness criteria are satisfied for this match."""
        return match_id in self._complete

    def is_excluded(self, match_id: str) -> bool:
        """True if the match is on the exclusion list and not reinstated."""
        entry = self._excluded.get(match_id)
        return entry is not None and not entry.reinstated

    def should_skip(self, match_id: str) -> bool:
        """
        Primary guard for EpochHarvester.  Returns True when no fetch is needed.

        Skip when:
          - skip_if_complete  (harvest_protocol.json default: true)
          - skip_if_excluded  (harvest_protocol.json default: true)
        """
        if _SKIP_POLICY.get("skip_if_complete", True) and self.is_complete(match_id):
            logger.debug("SKIP %s — already complete", match_id)
            return True
        if _SKIP_POLICY.get("skip_if_excluded", True) and self.is_excluded(match_id):
            entry = self._excluded[match_id]
            logger.debug("SKIP %s — excluded (%s)", match_id, entry.reason_code)
            return True
        return False

    def should_skip_checksum(self, match_id: str, new_checksum: str) -> bool:
        """
        True when content has not changed since last collection.

        Used *after* a fetch to decide whether to write a new record.
        Implements the ``skip_if_checksum_unchanged`` policy.
        """
        if not _SKIP_POLICY.get("skip_if_checksum_unchanged", True):
            return False
        stored = self._known_checksums.get(match_id)
        if stored and stored == new_checksum:
            logger.debug("SKIP %s — checksum unchanged (%s…)", match_id, new_checksum[:12])
            return True
        return False

    # ------------------------------------------------------------------
    # Mutation interface — called by harvester and bridge on completion
    # ------------------------------------------------------------------

    def mark_complete(self, match_id: str, checksum: Optional[str] = None) -> None:
        """Called by ExtractionBridge after a valid KCRITR write."""
        self._complete.add(match_id)
        self._pending.discard(match_id)
        if checksum:
            self._known_checksums[match_id] = checksum
        logger.debug("Registry: marked %s COMPLETE", match_id)
        if self._db_url:
            self._db_mark_complete(match_id)

    def mark_excluded(
        self,
        match_id: str,
        reason_code: str,
        notes: str = "",
        excluded_by: str = "system",
    ) -> None:
        """
        Add match_id to the exclusion list.

        reason_code must be one of the codes defined in harvest_protocol.json.
        Raises ValueError for unknown reason codes to enforce the shared contract.
        """
        if reason_code not in self.VALID_EXCLUSION_REASONS:
            raise ValueError(
                f"Unknown exclusion reason '{reason_code}'. "
                f"Valid codes: {sorted(self.VALID_EXCLUSION_REASONS)}"
            )
        entry = ExclusionEntry(
            match_id=match_id,
            reason_code=reason_code,
            notes=notes,
            excluded_by=excluded_by,
        )
        self._excluded[match_id] = entry
        self._pending.discard(match_id)
        self._complete.discard(match_id)
        logger.info(
            "Registry: excluded %s — reason=%s  notes=%s",
            match_id, reason_code, notes[:80] if notes else "",
        )
        if self._db_url:
            self._db_mark_excluded(entry)

    def reinstate(self, match_id: str) -> None:
        """Undo an exclusion (e.g., after fixing a schema parser)."""
        entry = self._excluded.get(match_id)
        if entry:
            entry.reinstated = True
            self._pending.add(match_id)
            logger.info("Registry: reinstated %s (was excluded: %s)", match_id, entry.reason_code)

    def add_pending(self, match_id: str) -> None:
        """Register a match_id that is known but not yet complete (delta seed)."""
        if not self.is_excluded(match_id) and not self.is_complete(match_id):
            self._pending.add(match_id)

    # ------------------------------------------------------------------
    # List / stats interface
    # ------------------------------------------------------------------

    def list_pending(self) -> list[str]:
        """Match IDs known but not complete — primary delta-mode work queue."""
        return sorted(self._pending)

    def list_excluded(self) -> list[ExclusionEntry]:
        """Full exclusion list (including reinstated entries)."""
        return list(self._excluded.values())

    def get_stats(self) -> RegistryStats:
        return RegistryStats(
            complete=len(self._complete),
            pending=len(self._pending),
            excluded=sum(1 for e in self._excluded.values() if not e.reinstated),
            total_known=len(self._complete) + len(self._pending) + len(self._excluded),
        )

    # ------------------------------------------------------------------
    # DB integration (async-safe wrappers called from sync context)
    # ------------------------------------------------------------------

    @property
    def _known_checksums(self) -> dict:
        if not hasattr(self, "_checksums_cache"):
            self._checksums_cache: dict[str, str] = {}
        return self._checksums_cache

    def _load_from_db(self) -> None:
        """Pre-populate complete/excluded/pending sets from the DB."""
        try:
            import psycopg2  # type: ignore

            conn = psycopg2.connect(self._db_url)
            cur = conn.cursor()

            # Complete: matches where is_complete = TRUE in extraction_log
            cur.execute(
                """
                SELECT entity_id, last_modified_hash
                FROM extraction_log
                WHERE source = 'vlr_gg'
                  AND entity_type = 'match'
                  AND is_complete = TRUE
                """
            )
            for row in cur.fetchall():
                mid, checksum = row
                self._complete.add(mid)
                if checksum:
                    self._known_checksums[mid] = checksum

            # Excluded: matches flagged in schema_drift_log or with error_count > threshold
            cur.execute(
                """
                SELECT entity_id, last_error
                FROM extraction_log
                WHERE source = 'vlr_gg'
                  AND entity_type = 'match'
                  AND is_complete = FALSE
                  AND error_count >= 3
                """
            )
            for row in cur.fetchall():
                mid, last_error = row
                self._excluded[mid] = ExclusionEntry(
                    match_id=mid,
                    reason_code="MANUAL_EXCLUDE",
                    notes=f"error_count>=3: {last_error or ''}",
                    excluded_by="db_load",
                )

            # Pending: known but not complete and not excluded
            cur.execute(
                """
                SELECT entity_id
                FROM extraction_log
                WHERE source = 'vlr_gg'
                  AND entity_type = 'match'
                  AND is_complete = FALSE
                  AND error_count < 3
                """
            )
            for (mid,) in cur.fetchall():
                if mid not in self._excluded:
                    self._pending.add(mid)

            cur.close()
            conn.close()

            stats = self.get_stats()
            logger.info(
                "Registry loaded from DB: %s",
                stats.as_dict(),
            )

        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Registry could not load from DB (%s) — operating in memory-only mode",
                exc,
            )

    def _db_mark_complete(self, match_id: str) -> None:
        """Write completion flag back to extraction_log."""
        try:
            import psycopg2  # type: ignore

            conn = psycopg2.connect(self._db_url)
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE extraction_log
                SET is_complete = TRUE, last_extracted_at = NOW()
                WHERE source = 'vlr_gg'
                  AND entity_type = 'match'
                  AND entity_id = %s
                """,
                (match_id,),
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not update completion in DB for %s: %s", match_id, exc)

    def _db_mark_excluded(self, entry: ExclusionEntry) -> None:
        """Write exclusion reason to extraction_log last_error field."""
        try:
            import psycopg2  # type: ignore

            conn = psycopg2.connect(self._db_url)
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE extraction_log
                SET last_error = %s,
                    last_extracted_at = NOW()
                WHERE source = 'vlr_gg'
                  AND entity_type = 'match'
                  AND entity_id = %s
                """,
                (f"EXCLUDED:{entry.reason_code} — {entry.notes}", entry.match_id),
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Could not write exclusion to DB for %s: %s", entry.match_id, exc
            )
