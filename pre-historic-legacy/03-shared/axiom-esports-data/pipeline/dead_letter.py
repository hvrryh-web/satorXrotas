"""
Dead Letter Queue
=================

Queue for failed records with configurable retry logic.

Failed records are stored with their error context and can be
retried later with exponential backoff.

Example:
    dlq = DeadLetterQueue()
    
    # Add failed record
    dlq.enqueue("match_123", error, "fetch", payload={"url": "..."})
    
    # Retry all queued records
    results = dlq.retry_all(max_retries=3)
    print(f"Success: {results['success']}, Failed: {results['failed']}")
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Callable, Any

logger = logging.getLogger(__name__)


@dataclass
class DeadLetterEntry:
    """A single entry in the dead letter queue."""
    match_id: str
    stage: str
    error_message: str
    error_type: str
    payload: dict
    enqueued_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    retry_count: int = 0
    last_retry_at: Optional[str] = None
    status: str = "pending"  # pending, retrying, succeeded, failed
    
    def to_dict(self) -> dict:
        return {
            "match_id": self.match_id,
            "stage": self.stage,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "payload": self.payload,
            "enqueued_at": self.enqueued_at,
            "retry_count": self.retry_count,
            "last_retry_at": self.last_retry_at,
            "status": self.status,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "DeadLetterEntry":
        return cls(
            match_id=data["match_id"],
            stage=data["stage"],
            error_message=data["error_message"],
            error_type=data["error_type"],
            payload=data.get("payload", {}),
            enqueued_at=data["enqueued_at"],
            retry_count=data.get("retry_count", 0),
            last_retry_at=data.get("last_retry_at"),
            status=data.get("status", "pending"),
        )
    
    def can_retry(self, max_retries: int, backoff_seconds: float) -> bool:
        """Check if this entry is eligible for retry."""
        if self.status == "succeeded":
            return False
        if self.retry_count >= max_retries:
            return False
        
        # Check backoff period
        if self.last_retry_at:
            last_retry = datetime.fromisoformat(self.last_retry_at)
            next_retry = last_retry + timedelta(seconds=backoff_seconds * (2 ** self.retry_count))
            if datetime.now(timezone.utc) < next_retry:
                return False
        
        return True


class DeadLetterQueue:
    """Store failed records for later retry with exponential backoff.
    
    The dead letter queue persists failed records to disk and provides
    retry functionality with configurable backoff strategy.
    
    Example:
        dlq = DeadLetterQueue(Path("data/dead_letter"))
        
        # When a stage fails
        try:
            await process_match(match_id)
        except Exception as e:
            dlq.enqueue(match_id, e, "fetch", {"url": url})
        
        # Periodically retry
        if dlq.size() > 0:
            results = dlq.retry_all(
                processor=retry_function,
                max_retries=3,
                backoff_seconds=60
            )
    """
    
    def __init__(self, storage_path: Optional[Path] = None) -> None:
        """Initialize the dead letter queue.
        
        Args:
            storage_path: Directory to store dead letter entries
        """
        self.storage_path = storage_path or Path("data/dead_letter")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._entries: dict[str, DeadLetterEntry] = {}
        self._load_entries()
    
    def enqueue(
        self,
        match_id: str,
        error: Exception,
        stage: str,
        payload: Optional[dict] = None,
    ) -> None:
        """Add failed record to queue.
        
        Args:
            match_id: Unique identifier for the match
            error: Exception that caused the failure
            stage: Pipeline stage that failed
            payload: Additional context data for retry
        """
        entry = DeadLetterEntry(
            match_id=match_id,
            stage=stage,
            error_message=str(error)[:500],  # Truncate long messages
            error_type=type(error).__name__,
            payload=payload or {},
        )
        
        self._entries[match_id] = entry
        self._save_entry(entry)
        
        logger.warning(
            "Added match %s to dead letter queue (stage=%s, error=%s)",
            match_id, stage, entry.error_type
        )
    
    def dequeue(self, match_id: str) -> Optional[DeadLetterEntry]:
        """Remove and return an entry from the queue.
        
        Args:
            match_id: Match ID to dequeue
            
        Returns:
            The entry if found, None otherwise
        """
        entry = self._entries.pop(match_id, None)
        if entry:
            self._delete_entry_file(match_id)
        return entry
    
    def get(self, match_id: str) -> Optional[DeadLetterEntry]:
        """Get an entry without removing it.
        
        Args:
            match_id: Match ID to look up
            
        Returns:
            The entry if found, None otherwise
        """
        return self._entries.get(match_id)
    
    def size(self) -> int:
        """Get total number of entries in queue."""
        return len(self._entries)
    
    def size_by_status(self) -> dict[str, int]:
        """Get entry count grouped by status."""
        counts = {"pending": 0, "retrying": 0, "succeeded": 0, "failed": 0}
        for entry in self._entries.values():
            counts[entry.status] = counts.get(entry.status, 0) + 1
        return counts
    
    def list_pending(self, max_retries: int = 3) -> list[str]:
        """List match IDs that are pending retry.
        
        Args:
            max_retries: Maximum retry attempts
            
        Returns:
            List of match IDs eligible for retry
        """
        return [
            match_id for match_id, entry in self._entries.items()
            if entry.status in ("pending", "retrying") and entry.retry_count < max_retries
        ]
    
    def list_permanently_failed(self, max_retries: int = 3) -> list[str]:
        """List match IDs that have exceeded max retries.
        
        Args:
            max_retries: Maximum retry attempts
            
        Returns:
            List of match IDs that have failed permanently
        """
        return [
            match_id for match_id, entry in self._entries.items()
            if entry.status == "failed" or entry.retry_count >= max_retries
        ]
    
    def retry_all(
        self,
        processor: Optional[Callable[[str, dict], Any]] = None,
        max_retries: int = 3,
        backoff_seconds: float = 60.0,
    ) -> dict:
        """Retry all queued records.
        
        Args:
            processor: Function to process each entry (match_id, payload) -> result
            max_retries: Maximum retry attempts per entry
            backoff_seconds: Base backoff between retries
            
        Returns:
            Dictionary with success and failure counts
        """
        if processor is None:
            logger.warning("No processor provided for retry - marking all as failed")
            return self._mark_all_failed()
        
        results = {"success": 0, "failed": 0, "skipped": 0, "errors": []}
        
        for match_id, entry in list(self._entries.items()):
            if not entry.can_retry(max_retries, backoff_seconds):
                results["skipped"] += 1
                continue
            
            entry.retry_count += 1
            entry.last_retry_at = datetime.now(timezone.utc).isoformat()
            entry.status = "retrying"
            
            try:
                logger.info(
                    "Retrying match %s (attempt %d/%d)",
                    match_id, entry.retry_count, max_retries
                )
                
                processor(match_id, entry.payload)
                
                # Success - remove from queue
                entry.status = "succeeded"
                self._save_entry(entry)
                self._entries.pop(match_id, None)
                self._delete_entry_file(match_id)
                results["success"] += 1
                
                logger.info("Retry succeeded for match %s", match_id)
                
            except Exception as exc:
                entry.status = "failed" if entry.retry_count >= max_retries else "pending"
                self._save_entry(entry)
                results["failed"] += 1
                results["errors"].append({
                    "match_id": match_id,
                    "error": str(exc),
                    "attempt": entry.retry_count,
                })
                
                logger.warning(
                    "Retry %d/%d failed for match %s: %s",
                    entry.retry_count, max_retries, match_id, exc
                )
        
        return results
    
    def clear_succeeded(self) -> int:
        """Remove all succeeded entries from queue.
        
        Returns:
            Number of entries removed
        """
        to_remove = [
            match_id for match_id, entry in self._entries.items()
            if entry.status == "succeeded"
        ]
        
        for match_id in to_remove:
            self._entries.pop(match_id, None)
            self._delete_entry_file(match_id)
        
        logger.info("Cleared %d succeeded entries from dead letter queue", len(to_remove))
        return len(to_remove)
    
    def clear_all(self) -> int:
        """Remove all entries from queue (use with caution).
        
        Returns:
            Number of entries removed
        """
        count = len(self._entries)
        self._entries.clear()
        
        # Delete all files
        for f in self.storage_path.glob("*.json"):
            f.unlink()
        
        logger.warning("Cleared all %d entries from dead letter queue", count)
        return count
    
    def to_dict(self) -> dict:
        """Export all entries as dictionary."""
        return {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total_entries": len(self._entries),
            "by_status": self.size_by_status(),
            "entries": [e.to_dict() for e in self._entries.values()],
        }
    
    def save_report(self, path: Optional[Path] = None) -> Path:
        """Save queue report to file.
        
        Args:
            path: Output path (defaults to storage_path/report.json)
            
        Returns:
            Path to saved report
        """
        target = path or self.storage_path / "report.json"
        target.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return target
    
    # ------------------------------------------------------------------
    # Private methods
    # ------------------------------------------------------------------
    
    def _entry_file_path(self, match_id: str) -> Path:
        """Get file path for an entry."""
        safe_id = match_id.replace("/", "_").replace("\\", "_")
        return self.storage_path / f"{safe_id}.json"
    
    def _load_entries(self) -> None:
        """Load all entries from storage."""
        if not self.storage_path.exists():
            return
        
        for file_path in self.storage_path.glob("*.json"):
            if file_path.name == "report.json":
                continue
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                entry = DeadLetterEntry.from_dict(data)
                self._entries[entry.match_id] = entry
            except Exception as exc:
                logger.warning("Failed to load dead letter entry from %s: %s", file_path, exc)
        
        logger.debug("Loaded %d entries from dead letter queue", len(self._entries))
    
    def _save_entry(self, entry: DeadLetterEntry) -> None:
        """Save a single entry to disk."""
        file_path = self._entry_file_path(entry.match_id)
        file_path.write_text(json.dumps(entry.to_dict(), indent=2), encoding="utf-8")
    
    def _delete_entry_file(self, match_id: str) -> None:
        """Delete an entry file from disk."""
        file_path = self._entry_file_path(match_id)
        if file_path.exists():
            file_path.unlink()
    
    def _mark_all_failed(self) -> dict:
        """Mark all entries as failed (when no processor provided)."""
        for entry in self._entries.values():
            entry.status = "failed"
            self._save_entry(entry)
        
        return {
            "success": 0,
            "failed": len(self._entries),
            "skipped": 0,
            "errors": [],
        }
