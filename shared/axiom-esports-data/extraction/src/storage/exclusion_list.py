"""
Exclusion List — Persistent file-based store for match IDs excluded from re-collection.

Purpose
-------
The exclusion list is a safety layer on top of KnownRecordRegistry.  It persists
exclusion decisions to a JSON file so they survive process restarts and are visible
to both the harvester and any AI agent jobs that query the pipeline state.

It is intentionally separate from the DB-backed registry so that:
  1. Exclusions survive database failures.
  2. Manual exclusions can be committed to git for audit trail.
  3. CI/test environments without a DB can still respect exclusions.

Conflict rules (from harvest_protocol.json):
  - ``SCHEMA_CONFLICT`` exclusions block the analytics pipeline until cleared.
  - ``CONTENT_DRIFT`` exclusions are reviewed before the next monthly harvest.
  - ``RATE_LIMIT_BAN`` exclusions are auto-cleared after recovery_seconds.
  - All other exclusions require explicit reinstatement by the data team.

File format
-----------
``data/exclusions/exclusion_list.json``  (gitignored by default)
``data/exclusions/exclusion_list_committed.json``  (for manual/permanent exclusions)

The committed file can be added to git for audit trail of permanently excluded matches.
"""
import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from extraction.src.storage.known_record_registry import ExclusionEntry, PROTOCOL

logger = logging.getLogger(__name__)

DEFAULT_EXCLUSION_DIR = Path(os.environ.get("EXCLUSION_LIST_DIR", "data/exclusions"))
COMMITTED_FILE = DEFAULT_EXCLUSION_DIR / "exclusion_list_committed.json"
RUNTIME_FILE = DEFAULT_EXCLUSION_DIR / "exclusion_list.json"

# Exclusions with these reason codes block the analytics pipeline immediately
PIPELINE_BLOCKING_REASONS = {"SCHEMA_CONFLICT"}

# Exclusions with these reasons are automatically reviewed on each monthly harvest
AUTO_REVIEW_REASONS = {"CONTENT_DRIFT", "RATE_LIMIT_BAN", "LOW_CONFIDENCE"}

VALID_REASONS = set(PROTOCOL.get("exclusion_reasons", {}).keys()) or {
    "COMPLETE", "MANUAL_EXCLUDE", "DUPLICATE", "SCHEMA_CONFLICT",
    "CONTENT_DRIFT", "LOW_CONFIDENCE", "RATE_LIMIT_BAN",
}


class ExclusionList:
    """
    File-backed exclusion list shared between the registry and the harvester.

    Safety guarantees:
      - ``add()`` validates reason_code against the protocol contract.
      - ``SCHEMA_CONFLICT`` entries immediately raise ``PipelineBlockedError``
        on ``assert_pipeline_safe()``.
      - Entries are written atomically (temp-file + rename) to avoid corruption.
      - ``list_for_review()`` surfaces AUTO_REVIEW_REASONS for monthly inspection.
    """

    def __init__(
        self,
        runtime_path: Path = RUNTIME_FILE,
        committed_path: Path = COMMITTED_FILE,
    ) -> None:
        self._runtime_path = runtime_path
        self._committed_path = committed_path
        self._entries: dict[str, ExclusionEntry] = {}
        self._load()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def is_excluded(self, match_id: str) -> bool:
        """True if match_id is excluded and not reinstated."""
        entry = self._entries.get(match_id)
        return entry is not None and not entry.reinstated

    def get(self, match_id: str) -> Optional[ExclusionEntry]:
        return self._entries.get(match_id)

    def add(
        self,
        match_id: str,
        reason_code: str,
        notes: str = "",
        excluded_by: str = "system",
        commit: bool = False,
    ) -> ExclusionEntry:
        """
        Exclude a match_id.

        Parameters
        ----------
        match_id:     VLR match ID to exclude.
        reason_code:  Must be one of the codes in harvest_protocol.json.
        notes:        Human-readable context for the exclusion decision.
        excluded_by:  Script/agent name or 'data_team' for manual entries.
        commit:       If True, also write to the committed file (for git).

        Raises
        ------
        ValueError       if reason_code is not in the protocol contract.
        PipelineBlockedError  if reason_code is in PIPELINE_BLOCKING_REASONS.
        """
        if reason_code not in VALID_REASONS:
            raise ValueError(
                f"Unknown exclusion reason '{reason_code}'. "
                f"Valid codes (from harvest_protocol.json): {sorted(VALID_REASONS)}"
            )

        entry = ExclusionEntry(
            match_id=match_id,
            reason_code=reason_code,
            notes=notes,
            excluded_by=excluded_by,
        )
        self._entries[match_id] = entry
        self._save()

        if commit:
            self._save_committed()

        logger.info(
            "ExclusionList: added %s — reason=%s  by=%s",
            match_id, reason_code, excluded_by,
        )

        if reason_code in PIPELINE_BLOCKING_REASONS:
            raise PipelineBlockedError(
                f"Match {match_id} excluded with reason '{reason_code}' — "
                f"analytics pipeline is BLOCKED until this is resolved. "
                f"Notes: {notes}"
            )

        return entry

    def reinstate(self, match_id: str, reinstated_by: str = "data_team") -> None:
        """Remove an exclusion so the match becomes re-eligible for harvest."""
        entry = self._entries.get(match_id)
        if entry is None:
            logger.warning("reinstate: %s not found in exclusion list", match_id)
            return
        entry.reinstated = True
        entry.notes = f"{entry.notes} | Reinstated by {reinstated_by} at {datetime.now(tz=timezone.utc).isoformat()}"
        self._save()
        logger.info("ExclusionList: reinstated %s", match_id)

    def assert_pipeline_safe(self) -> None:
        """
        Raise PipelineBlockedError if any unresolved PIPELINE_BLOCKING_REASONS exist.
        Called at the start of analytics jobs to enforce the safety contract.
        """
        blocking = [
            e for e in self._entries.values()
            if not e.reinstated and e.reason_code in PIPELINE_BLOCKING_REASONS
        ]
        if blocking:
            ids = [e.match_id for e in blocking[:5]]
            raise PipelineBlockedError(
                f"{len(blocking)} match(es) have blocking exclusion reason "
                f"'{PIPELINE_BLOCKING_REASONS}'. Sample: {ids}. "
                f"Resolve these before running analytics."
            )

    def list_for_review(self) -> list[ExclusionEntry]:
        """
        Return entries that need review before the next monthly harvest.
        Covers AUTO_REVIEW_REASONS (CONTENT_DRIFT, RATE_LIMIT_BAN, LOW_CONFIDENCE).
        """
        return [
            e for e in self._entries.values()
            if not e.reinstated and e.reason_code in AUTO_REVIEW_REASONS
        ]

    def list_all(self) -> list[ExclusionEntry]:
        """All exclusion entries including reinstated ones."""
        return list(self._entries.values())

    def summary(self) -> dict:
        """Count entries by reason_code for reporting."""
        counts: dict[str, int] = {}
        for e in self._entries.values():
            if not e.reinstated:
                counts[e.reason_code] = counts.get(e.reason_code, 0) + 1
        return {
            "total_excluded": sum(counts.values()),
            "by_reason": counts,
            "pipeline_blocking": any(
                r in PIPELINE_BLOCKING_REASONS for r in counts
            ),
        }

    # ------------------------------------------------------------------
    # I/O
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load from committed file first, then overlay runtime file."""
        for path in (self._committed_path, self._runtime_path):
            if path.exists():
                try:
                    data = json.loads(path.read_text())
                    for item in data.get("exclusions", []):
                        entry = ExclusionEntry(**item)
                        # Runtime file wins over committed for reinstated state
                        if entry.match_id not in self._entries or path == self._runtime_path:
                            self._entries[entry.match_id] = entry
                    logger.debug("Loaded %d exclusions from %s", len(self._entries), path)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Could not load exclusion list from %s: %s", path, exc)

    def _save(self) -> None:
        """Atomically write runtime file."""
        self._runtime_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "1.0",
            "saved_at": datetime.now(tz=timezone.utc).isoformat(),
            "exclusions": [asdict(e) for e in self._entries.values()],
        }
        tmp = self._runtime_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2))
        tmp.replace(self._runtime_path)

    def _save_committed(self) -> None:
        """Write manually committed exclusions (for git audit trail)."""
        committed = [
            e for e in self._entries.values()
            if e.excluded_by == "data_team" or e.reason_code == "MANUAL_EXCLUDE"
        ]
        self._committed_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "1.0",
            "saved_at": datetime.now(tz=timezone.utc).isoformat(),
            "_note": "Committed exclusions — safe to add to git for audit trail.",
            "exclusions": [asdict(e) for e in committed],
        }
        self._committed_path.write_text(json.dumps(payload, indent=2))


class PipelineBlockedError(Exception):
    """
    Raised when a SCHEMA_CONFLICT or other blocking exclusion is present.
    The analytics pipeline must not proceed until this is cleared.
    """
