"""
Conflict detection and resolution for esports data extraction.
"""

import hashlib
import json
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta

from .models import ExtractionJob, GameType, JobStatus

logger = logging.getLogger(__name__)


class ConflictResolver:
    """
    Detects and resolves data conflicts:
    - Duplicate jobs
    - Content drift (data changed since last extraction)
    - Concurrent modifications
    - Rate limit violations
    """
    
    def __init__(self, db_pool=None, redis_client=None):
        self.db_pool = db_pool
        self.redis_client = redis_client
        self._lock_cache: Dict[str, datetime] = {}
    
    async def check_duplicate_job(self, job: ExtractionJob) -> Optional[str]:
        """
        Check if equivalent job already exists in database.
        
        Args:
            job: Job to check for duplicates
            
        Returns:
            ID of existing job if duplicate found, None otherwise
        """
        if not self.db_pool:
            return None
        
        try:
            async with self.db_pool.acquire() as conn:
                # Check for similar jobs in last 24 hours
                existing = await conn.fetchval(
                    """
                    SELECT id FROM extraction_jobs 
                    WHERE game = $1 
                      AND source = $2 
                      AND job_type = $3 
                      AND epoch = $4
                      AND (region IS NOT DISTINCT FROM $5)
                      AND (date_start IS NOT DISTINCT FROM $6)
                      AND (date_end IS NOT DISTINCT FROM $7)
                      AND status IN ('pending', 'assigned', 'processing', 'completed')
                      AND created_at > now() - interval '24 hours'
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    job.game.value if isinstance(job.game, GameType) else job.game,
                    job.source,
                    job.job_type,
                    job.epoch,
                    job.region,
                    job.date_start,
                    job.date_end
                )
                return existing
        except Exception as e:
            logger.error(f"Error checking for duplicate job: {e}")
            return None
    
    async def find_active_duplicate(self, job: ExtractionJob) -> Optional[Dict[str, Any]]:
        """
        Find an active (pending/processing) duplicate job.
        
        Args:
            job: Job to check
            
        Returns:
            Dict with existing job details if found
        """
        if not self.db_pool:
            return None
        
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT id, status, assigned_agent, created_at
                    FROM extraction_jobs 
                    WHERE game = $1 
                      AND source = $2 
                      AND job_type = $3 
                      AND epoch = $4
                      AND (region IS NOT DISTINCT FROM $5)
                      AND status IN ('pending', 'assigned', 'processing')
                      AND created_at > now() - interval '24 hours'
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    job.game.value if isinstance(job.game, GameType) else job.game,
                    job.source,
                    job.job_type,
                    job.epoch,
                    job.region
                )
                
                if row:
                    return {
                        "id": row["id"],
                        "status": row["status"],
                        "assigned_agent": row["assigned_agent"],
                        "created_at": row["created_at"]
                    }
                return None
        except Exception as e:
            logger.error(f"Error finding active duplicate: {e}")
            return None
    
    async def detect_content_drift(
        self,
        game: GameType,
        source: str,
        source_id: str,
        new_checksum: str,
        new_data: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Detect if content has changed since last extraction.
        
        Args:
            game: Game type
            source: Data source
            source_id: Unique identifier in source system
            new_checksum: Checksum of new data
            new_data: Optional new data for comparison
            
        Returns:
            Conflict info if drift detected, None otherwise
        """
        if not self.db_pool:
            return None
        
        try:
            async with self.db_pool.acquire() as conn:
                existing = await conn.fetchrow(
                    """
                    SELECT id, checksum, extracted_at, data_size
                    FROM raw_extractions 
                    WHERE game = $1 
                      AND source = $2 
                      AND source_id = $3
                    ORDER BY extracted_at DESC
                    LIMIT 1
                    """,
                    game.value if isinstance(game, GameType) else game,
                    source,
                    source_id
                )
                
                if not existing:
                    return None
                
                if existing["checksum"] != new_checksum:
                    return {
                        "type": "content_drift",
                        "existing_id": existing["id"],
                        "existing_checksum": existing["checksum"],
                        "new_checksum": new_checksum,
                        "last_extracted": existing["extracted_at"],
                        "data_size_delta": (
                            len(json.dumps(new_data)) - existing["data_size"]
                            if new_data and existing["data_size"] else None
                        )
                    }
                
                return None
        except Exception as e:
            logger.error(f"Error detecting content drift: {e}")
            return None
    
    async def resolve_conflict(self, conflict: Dict[str, Any]) -> str:
        """
        Determine resolution strategy for conflict.
        
        Args:
            conflict: Conflict information from detect methods
            
        Returns:
            Resolution strategy name
        """
        conflict_type = conflict.get("type")
        
        if conflict_type == "content_drift":
            # Strategy: Store new version, flag for review
            await self._flag_content_drift(conflict)
            return "store_and_flag"
        
        elif conflict_type == "concurrent_modification":
            # Strategy: Last-write-wins with merge attempt
            return await self._resolve_concurrent_modification(conflict)
        
        elif conflict_type == "rate_limit_violation":
            # Strategy: Back off and retry
            return "backoff"
        
        return "unknown_conflict_type"
    
    async def _flag_content_drift(self, conflict: Dict[str, Any]) -> None:
        """Flag content drift for manual review."""
        if not self.db_pool:
            return
        
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO content_drift_alerts 
                    (existing_extraction_id, new_checksum, detected_at, status)
                    VALUES ($1, $2, now(), 'open')
                    ON CONFLICT (existing_extraction_id, new_checksum) DO NOTHING
                    """,
                    conflict["existing_id"],
                    conflict["new_checksum"]
                )
        except Exception as e:
            logger.error(f"Error flagging content drift: {e}")
    
    async def _resolve_concurrent_modification(self, conflict: Dict[str, Any]) -> str:
        """Resolve concurrent modification conflict."""
        # For now, use last-write-wins
        # In production, this could implement merge strategies
        return "last_write_wins"
    
    async def acquire_extraction_lock(
        self,
        game: GameType,
        source: str,
        identifier: str,
        timeout: int = 300
    ) -> bool:
        """
        Acquire distributed lock for extraction.
        
        Args:
            game: Game type
            source: Data source
            identifier: Unique identifier being extracted
            timeout: Lock timeout in seconds
            
        Returns:
            True if lock acquired
        """
        lock_key = f"extraction:{game.value if isinstance(game, GameType) else game}:{source}:{identifier}"
        
        # Try Redis first if available
        if self.redis_client:
            try:
                acquired = await self.redis_client.set(
                    lock_key, 
                    "1", 
                    nx=True, 
                    ex=timeout
                )
                return acquired is not None
            except Exception as e:
                logger.warning(f"Redis lock failed, falling back to memory: {e}")
        
        # Fallback to in-memory lock
        now = datetime.utcnow()
        if lock_key in self._lock_cache:
            lock_time = self._lock_cache[lock_key]
            if now - lock_time < timedelta(seconds=timeout):
                return False
        
        self._lock_cache[lock_key] = now
        return True
    
    async def release_extraction_lock(
        self,
        game: GameType,
        source: str,
        identifier: str
    ) -> None:
        """Release distributed lock for extraction."""
        lock_key = f"extraction:{game.value if isinstance(game, GameType) else game}:{source}:{identifier}"
        
        if self.redis_client:
            try:
                await self.redis_client.delete(lock_key)
            except Exception as e:
                logger.warning(f"Error releasing Redis lock: {e}")
        
        # Remove from in-memory cache
        self._lock_cache.pop(lock_key, None)
    
    async def cleanup_old_locks(self, max_age_minutes: int = 10) -> int:
        """
        Clean up stale in-memory locks.
        
        Args:
            max_age_minutes: Maximum age in minutes
            
        Returns:
            Number of locks cleaned up
        """
        now = datetime.utcnow()
        max_age = timedelta(minutes=max_age_minutes)
        
        to_remove = [
            key for key, lock_time in self._lock_cache.items()
            if now - lock_time > max_age
        ]
        
        for key in to_remove:
            del self._lock_cache[key]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} stale locks")
        
        return len(to_remove)
    
    def compute_checksum(self, data: Any) -> str:
        """
        Compute checksum for data comparison.
        
        Args:
            data: Data to checksum (will be JSON serialized)
            
        Returns:
            MD5 checksum string
        """
        try:
            json_str = json.dumps(data, sort_keys=True, default=str)
            return hashlib.md5(json_str.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Error computing checksum: {e}")
            return hashlib.md5(str(data).encode()).hexdigest()
    
    async def record_extraction(
        self,
        game: GameType,
        source: str,
        source_id: str,
        checksum: str,
        data_size: int,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Record extraction to database.
        
        Args:
            game: Game type
            source: Data source
            source_id: Source identifier
            checksum: Data checksum
            data_size: Size of extracted data in bytes
            metadata: Optional metadata
            
        Returns:
            ID of recorded extraction
        """
        if not self.db_pool:
            return 0
        
        try:
            async with self.db_pool.acquire() as conn:
                record_id = await conn.fetchval(
                    """
                    INSERT INTO raw_extractions 
                    (game, source, source_id, checksum, data_size, metadata, extracted_at)
                    VALUES ($1, $2, $3, $4, $5, $6, now())
                    RETURNING id
                    """,
                    game.value if isinstance(game, GameType) else game,
                    source,
                    source_id,
                    checksum,
                    data_size,
                    json.dumps(metadata) if metadata else None
                )
                return record_id
        except Exception as e:
            logger.error(f"Error recording extraction: {e}")
            return 0
    
    async def get_extraction_history(
        self,
        game: GameType,
        source: str,
        source_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get extraction history for a specific item.
        
        Args:
            game: Game type
            source: Data source
            source_id: Source identifier
            limit: Maximum number of records
            
        Returns:
            List of extraction records
        """
        if not self.db_pool:
            return []
        
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, checksum, data_size, metadata, extracted_at
                    FROM raw_extractions 
                    WHERE game = $1 AND source = $2 AND source_id = $3
                    ORDER BY extracted_at DESC
                    LIMIT $4
                    """,
                    game.value if isinstance(game, GameType) else game,
                    source,
                    source_id,
                    limit
                )
                
                return [
                    {
                        "id": row["id"],
                        "checksum": row["checksum"],
                        "data_size": row["data_size"],
                        "metadata": row["metadata"],
                        "extracted_at": row["extracted_at"]
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error getting extraction history: {e}")
            return []
