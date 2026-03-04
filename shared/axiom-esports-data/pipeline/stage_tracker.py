"""
Pipeline Stage Tracker
======================

Tracks which pipeline stages each match has completed.
Enables stage-by-stage resumption and idempotent processing.

The tracker maintains state in memory with optional persistence
to the database for cross-process coordination.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class StageState:
    """State for a single match's pipeline progress."""
    match_id: str
    stages_completed: set[str] = field(default_factory=set)
    stages_failed: dict[str, str] = field(default_factory=dict)  # stage -> error
    last_updated: Optional[str] = None
    retry_count: int = 0
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> dict:
        return {
            "match_id": self.match_id,
            "stages_completed": sorted(self.stages_completed),
            "stages_failed": self.stages_failed,
            "last_updated": self.last_updated,
            "retry_count": self.retry_count,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "StageState":
        return cls(
            match_id=data["match_id"],
            stages_completed=set(data.get("stages_completed", [])),
            stages_failed=data.get("stages_failed", {}),
            last_updated=data.get("last_updated"),
            retry_count=data.get("retry_count", 0),
        )


class StageTracker:
    """Tracks pipeline stage completion per match.
    
    Provides idempotent pipeline processing by tracking which stages
    have already been completed for each match_id.
    
    Example:
        tracker = StageTracker()
        
        # Get stages that still need to run
        pending = tracker.get_pending_stages("match_123")
        
        # Mark stages complete as they finish
        tracker.mark_stage_complete("match_123", "fetch")
        tracker.mark_stage_complete("match_123", "parse")
        
        # Check if entire pipeline is done
        if tracker.is_complete("match_123"):
            print("Match fully processed!")
    """
    
    STAGES = [
        "discovered",
        "fetched",
        "verified",
        "parsed",
        "transformed",
        "crossref",
        "stored",
        "indexed",
    ]
    
    def __init__(
        self,
        db_url: Optional[str] = None,
        state_file: Optional[Path] = None,
    ) -> None:
        """Initialize the stage tracker.
        
        Args:
            db_url: PostgreSQL connection URL for persistence
            state_file: Local file for state backup
        """
        self._db_url = db_url or os.environ.get("DATABASE_URL")
        self._state_file = state_file
        self._states: dict[str, StageState] = {}
        self._dirty: set[str] = set()
        
        if self._state_file and self._state_file.exists():
            self._load_from_file()
    
    def get_pending_stages(self, match_id: str) -> list[str]:
        """Return stages that still need to run for this match.
        
        Args:
            match_id: Unique identifier for the match
            
        Returns:
            List of stage names not yet completed
        """
        state = self._get_state(match_id)
        return [s for s in self.STAGES if s not in state.stages_completed]
    
    def mark_stage_complete(self, match_id: str, stage: str) -> None:
        """Mark a stage as successfully completed.
        
        Args:
            match_id: Unique identifier for the match
            stage: Name of the completed stage
            
        Raises:
            ValueError: If stage name is not recognized
        """
        if stage not in self.STAGES:
            raise ValueError(f"Unknown stage '{stage}'. Valid stages: {self.STAGES}")
        
        state = self._get_state(match_id)
        state.stages_completed.add(stage)
        state.last_updated = datetime.now(timezone.utc).isoformat()
        
        # Remove from failed if it was there
        if stage in state.stages_failed:
            del state.stages_failed[stage]
        
        self._dirty.add(match_id)
        logger.debug("Marked %s complete for match %s", stage, match_id)
        
        # Persist if needed
        if self._db_url:
            self._persist_to_db(match_id, stage, success=True)
    
    def mark_stage_failed(
        self,
        match_id: str,
        stage: str,
        error: str,
    ) -> None:
        """Mark a stage as failed with error information.
        
        Args:
            match_id: Unique identifier for the match
            stage: Name of the failed stage
            error: Error message or description
        """
        if stage not in self.STAGES:
            raise ValueError(f"Unknown stage '{stage}'. Valid stages: {self.STAGES}")
        
        state = self._get_state(match_id)
        state.stages_failed[stage] = error
        state.retry_count += 1
        state.last_updated = datetime.now(timezone.utc).isoformat()
        
        self._dirty.add(match_id)
        logger.warning("Marked %s failed for match %s: %s", stage, match_id, error)
        
        if self._db_url:
            self._persist_to_db(match_id, stage, success=False, error=error)
    
    def is_stage_complete(self, match_id: str, stage: str) -> bool:
        """Check if a specific stage is done.
        
        Args:
            match_id: Unique identifier for the match
            stage: Name of the stage to check
            
        Returns:
            True if stage is completed, False otherwise
        """
        state = self._get_state(match_id)
        return stage in state.stages_completed
    
    def is_stage_failed(self, match_id: str, stage: str) -> bool:
        """Check if a specific stage has failed.
        
        Args:
            match_id: Unique identifier for the match
            stage: Name of the stage to check
            
        Returns:
            True if stage has failed, False otherwise
        """
        state = self._get_state(match_id)
        return stage in state.stages_failed
    
    def is_complete(self, match_id: str) -> bool:
        """Check if all stages are complete for this match.
        
        Args:
            match_id: Unique identifier for the match
            
        Returns:
            True if all stages completed, False otherwise
        """
        pending = self.get_pending_stages(match_id)
        return len(pending) == 0
    
    def get_stage_error(self, match_id: str, stage: str) -> Optional[str]:
        """Get error message for a failed stage.
        
        Args:
            match_id: Unique identifier for the match
            stage: Name of the stage
            
        Returns:
            Error message if stage failed, None otherwise
        """
        state = self._get_state(match_id)
        return state.stages_failed.get(stage)
    
    def get_retry_count(self, match_id: str) -> int:
        """Get number of retry attempts for this match.
        
        Args:
            match_id: Unique identifier for the match
            
        Returns:
            Number of times this match has been retried
        """
        state = self._get_state(match_id)
        return state.retry_count
    
    def reset_match(self, match_id: str) -> None:
        """Reset all stages for a match (for reprocessing).
        
        Args:
            match_id: Unique identifier for the match
        """
        self._states[match_id] = StageState(match_id=match_id)
        self._dirty.add(match_id)
        logger.info("Reset all stages for match %s", match_id)
    
    def reset_stage(self, match_id: str, stage: str) -> None:
        """Reset a specific stage for reprocessing.
        
        Args:
            match_id: Unique identifier for the match
            stage: Name of the stage to reset
        """
        state = self._get_state(match_id)
        state.stages_completed.discard(stage)
        state.stages_failed.pop(stage, None)
        state.last_updated = datetime.now(timezone.utc).isoformat()
        self._dirty.add(match_id)
        logger.info("Reset stage %s for match %s", stage, match_id)
    
    def get_stats(self) -> dict:
        """Get summary statistics of stage completion.
        
        Returns:
            Dictionary with completion statistics
        """
        total = len(self._states)
        complete = sum(1 for s in self._states.values() if self.is_complete(s.match_id))
        
        stage_counts = {}
        for stage in self.STAGES:
            count = sum(
                1 for s in self._states.values()
                if stage in s.stages_completed
            )
            stage_counts[stage] = count
        
        failed = sum(
            1 for s in self._states.values()
            if s.stages_failed
        )
        
        return {
            "total_matches": total,
            "complete_matches": complete,
            "incomplete_matches": total - complete,
            "failed_matches": failed,
            "completion_rate_pct": round(100 * complete / max(total, 1), 2),
            "stage_completion": stage_counts,
        }
    
    def list_incomplete(self) -> list[str]:
        """List all match IDs that are not fully complete.
        
        Returns:
            List of incomplete match IDs
        """
        return [
            match_id for match_id, state in self._states.items()
            if not self.is_complete(match_id)
        ]
    
    def save_to_file(self, path: Optional[Path] = None) -> None:
        """Persist state to JSON file.
        
        Args:
            path: Path to save to (defaults to state_file from init)
        """
        target = path or self._state_file
        if target is None:
            return
        
        data = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "states": {k: v.to_dict() for k, v in self._states.items()},
        }
        
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self._dirty.clear()
        logger.debug("Saved stage tracker state to %s", target)
    
    def _get_state(self, match_id: str) -> StageState:
        """Get or create state for a match."""
        if match_id not in self._states:
            self._states[match_id] = StageState(match_id=match_id)
        return self._states[match_id]
    
    def _load_from_file(self) -> None:
        """Load state from JSON file."""
        if not self._state_file or not self._state_file.exists():
            return
        
        try:
            data = json.loads(self._state_file.read_text(encoding="utf-8"))
            for match_id, state_data in data.get("states", {}).items():
                self._states[match_id] = StageState.from_dict(state_data)
            logger.info("Loaded stage tracker state for %d matches", len(self._states))
        except Exception as exc:
            logger.warning("Failed to load stage tracker state: %s", exc)
    
    def _persist_to_db(
        self,
        match_id: str,
        stage: str,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """Persist stage completion to database extraction_log."""
        try:
            import psycopg2  # type: ignore
            
            conn = psycopg2.connect(self._db_url)
            cur = conn.cursor()
            
            # Update extraction_log with stage progress
            status = "complete" if success else "failed"
            cur.execute(
                """
                INSERT INTO extraction_log (
                    source, entity_type, entity_id, stage_completed,
                    stage_status, last_error, last_extracted_at
                ) VALUES ('vlr_gg', 'match', %s, %s, %s, %s, NOW())
                ON CONFLICT (source, entity_type, entity_id) DO UPDATE SET
                    stage_completed = EXCLUDED.stage_completed,
                    stage_status = EXCLUDED.stage_status,
                    last_error = EXCLUDED.last_error,
                    last_extracted_at = EXCLUDED.last_extracted_at
                """,
                (match_id, stage, status, error),
            )
            
            conn.commit()
            cur.close()
            conn.close()
            
        except Exception as exc:
            logger.warning("Could not persist stage to DB for %s: %s", match_id, exc)
