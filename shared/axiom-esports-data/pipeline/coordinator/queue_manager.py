"""
Queue management with priority and fairness.
"""

import asyncio
import heapq
import logging
from typing import List, Optional, Dict, Set, Tuple
from collections import deque
from datetime import datetime

from .models import ExtractionJob, Agent, GameType, JobStatus, QueueStats

logger = logging.getLogger(__name__)


class QueueManager:
    """
    Manages job queues with:
    - Priority ordering
    - Game isolation
    - Fairness between games
    - Dependency resolution
    - Duplicate detection
    """
    
    def __init__(self):
        # Priority queues: list of tuples (-priority, timestamp, job)
        self.cs_queue: List[Tuple[int, float, ExtractionJob]] = []
        self.val_queue: List[Tuple[int, float, ExtractionJob]] = []
        
        # Job storage for lookup
        self._jobs: Dict[str, ExtractionJob] = {}
        
        # Dependency tracking
        self.pending_dependencies: Dict[str, List[str]] = {}
        self.completed_jobs: Set[str] = set()
        
        # For duplicate detection
        self._job_signatures: Set[str] = set()
        
        # Concurrency control
        self._lock = asyncio.Lock()
        
        # Fairness tracking
        self._last_game_assigned: Optional[GameType] = None
        self._assignment_count: Dict[GameType, int] = {
            GameType.COUNTER_STRIKE: 0,
            GameType.VALORANT: 0
        }
    
    def _get_queue(self, game: GameType) -> List[Tuple[int, float, ExtractionJob]]:
        """Get the appropriate queue for a game."""
        return self.cs_queue if game == GameType.COUNTER_STRIKE else self.val_queue
    
    def _generate_signature(self, job: ExtractionJob) -> str:
        """Generate a unique signature for duplicate detection."""
        # Create signature based on key identifying fields
        sig_parts = [
            job.game.value if hasattr(job.game, 'value') else str(job.game),
            job.source.lower(),
            job.job_type.lower(),
            str(job.epoch),
            job.region or "",
            job.date_start.isoformat() if job.date_start else "",
            job.date_end.isoformat() if job.date_end else ""
        ]
        return "|".join(sig_parts)
    
    async def _is_duplicate(self, job: ExtractionJob) -> bool:
        """Check if an equivalent job already exists in queues."""
        signature = self._generate_signature(job)
        
        # Check if signature exists
        if signature in self._job_signatures:
            # Check if the existing job is still active
            for existing_job in self._jobs.values():
                if self._generate_signature(existing_job) == signature:
                    if existing_job.status in [JobStatus.PENDING, JobStatus.ASSIGNED, JobStatus.PROCESSING]:
                        return True
                    # Remove from signatures if completed/failed
                    if existing_job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                        self._job_signatures.discard(signature)
        
        return False
    
    async def enqueue(self, job: ExtractionJob) -> bool:
        """
        Add job to appropriate queue.
        
        Args:
            job: The extraction job to enqueue
            
        Returns:
            True if job was enqueued, False if duplicate or dependency pending
        """
        async with self._lock:
            # Check for duplicates
            if await self._is_duplicate(job):
                logger.info(f"Skipping duplicate job: {job.id}")
                return False
            
            # Store job reference
            self._jobs[job.id] = job
            self._job_signatures.add(self._generate_signature(job))
            
            # Check dependencies
            if job.dependencies:
                unresolved = [d for d in job.dependencies if d not in self.completed_jobs]
                if unresolved:
                    self.pending_dependencies[job.id] = unresolved
                    job.status = JobStatus.PENDING
                    logger.info(f"Job {job.id} waiting for dependencies: {unresolved}")
                    return True  # Job is stored but not queued yet
            
            # Add to priority queue
            queue = self._get_queue(job.game)
            heapq.heappush(queue, (-job.priority, job.created_at.timestamp(), job))
            job.status = JobStatus.PENDING
            
            logger.info(
                f"Enqueued {job.game} job: {job.job_type} from {job.source} "
                f"(priority {job.priority}, id: {job.id})"
            )
            return True
    
    async def dequeue(self, agent: Agent) -> Optional[ExtractionJob]:
        """
        Get next job suitable for agent.
        
        Uses fair scheduling between games and respects agent capabilities.
        
        Args:
            agent: The agent requesting work
            
        Returns:
            Next suitable job or None if no work available
        """
        async with self._lock:
            # Check pending dependencies first
            await self._resolve_pending_dependencies()
            
            # Determine game order based on fairness
            games = list(agent.game_specialization)
            if len(games) > 1:
                # Prioritize the game with fewer recent assignments
                games.sort(key=lambda g: self._assignment_count.get(g, 0))
            
            # Try to get job from agent's specialized games
            for game in games:
                queue = self._get_queue(game)
                
                # Find job agent can handle
                temp_queue = []
                job = None
                
                while queue and not job:
                    priority_neg, timestamp, candidate = heapq.heappop(queue)
                    
                    # Skip if job is no longer valid
                    if candidate.id not in self._jobs or candidate.status != JobStatus.PENDING:
                        continue
                    
                    # Check if agent can handle this source
                    if candidate.source in agent.source_capabilities:
                        job = candidate
                    else:
                        temp_queue.append((priority_neg, timestamp, candidate))
                
                # Restore unmatched jobs to queue
                for item in temp_queue:
                    heapq.heappush(queue, item)
                
                if job:
                    job.status = JobStatus.ASSIGNED
                    job.assigned_agent = agent.id
                    self._assignment_count[game] += 1
                    self._last_game_assigned = game
                    
                    logger.info(
                        f"Dequeued {job.game} job {job.id} for agent {agent.id} "
                        f"({job.job_type} from {job.source})"
                    )
                    return job
            
            return None
    
    async def dequeue_batch(self, agent: Agent, max_size: int = 10) -> List[ExtractionJob]:
        """
        Get a batch of jobs for an agent.
        
        Args:
            agent: The agent requesting work
            max_size: Maximum number of jobs to return
            
        Returns:
            List of jobs assigned to the agent
        """
        jobs = []
        for _ in range(max_size):
            job = await self.dequeue(agent)
            if job:
                jobs.append(job)
            else:
                break
        
        if jobs:
            logger.info(f"Dequeued batch of {len(jobs)} jobs for agent {agent.id}")
        
        return jobs
    
    async def _resolve_pending_dependencies(self) -> int:
        """
        Move jobs whose dependencies are now resolved to their queues.
        
        Returns:
            Number of jobs moved to queues
        """
        resolved = []
        
        for job_id, deps in list(self.pending_dependencies.items()):
            if all(d in self.completed_jobs for d in deps):
                resolved.append(job_id)
        
        moved = 0
        for job_id in resolved:
            job = self._jobs.get(job_id)
            if job:
                del self.pending_dependencies[job_id]
                
                # Add to queue
                queue = self._get_queue(job.game)
                heapq.heappush(queue, (-job.priority, job.created_at.timestamp(), job))
                moved += 1
                
                logger.info(f"Job {job_id} dependencies resolved, moved to queue")
        
        return moved
    
    async def mark_completed(self, job_id: str) -> None:
        """Mark job as completed and trigger dependent jobs."""
        async with self._lock:
            self.completed_jobs.add(job_id)
            
            # Update job status if we have it
            if job_id in self._jobs:
                self._jobs[job_id].mark_completed()
            
            await self._resolve_pending_dependencies()
    
    async def mark_failed(self, job_id: str, error: str) -> None:
        """Mark job as failed."""
        async with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].mark_failed(error)
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job."""
        async with self._lock:
            if job_id not in self._jobs:
                return False
            
            job = self._jobs[job_id]
            if job.status not in [JobStatus.PENDING, JobStatus.ASSIGNED]:
                return False  # Can only cancel pending/assigned jobs
            
            job.status = JobStatus.CANCELLED
            
            # Remove from queue if present
            queue = self._get_queue(job.game)
            queue[:] = [item for item in queue if item[2].id != job_id]
            heapq.heapify(queue)
            
            # Remove from pending dependencies
            if job_id in self.pending_dependencies:
                del self.pending_dependencies[job_id]
            
            logger.info(f"Cancelled job {job_id}")
            return True
    
    async def get_job(self, job_id: str) -> Optional[ExtractionJob]:
        """Get a job by ID."""
        return self._jobs.get(job_id)
    
    def _count_by_priority(self, queue: List[Tuple[int, float, ExtractionJob]]) -> Dict[int, int]:
        """Count jobs by priority level."""
        counts: Dict[int, int] = {}
        for _, _, job in queue:
            counts[job.priority] = counts.get(job.priority, 0) + 1
        return counts
    
    def _count_by_source(self, queue: List[Tuple[int, float, ExtractionJob]]) -> Dict[str, int]:
        """Count jobs by source."""
        counts: Dict[str, int] = {}
        for _, _, job in queue:
            counts[job.source] = counts.get(job.source, 0) + 1
        return counts
    
    def get_queue_stats(self) -> Dict:
        """Get statistics for both queues."""
        return {
            "cs": {
                "pending": len(self.cs_queue),
                "by_priority": self._count_by_priority(self.cs_queue),
                "by_source": self._count_by_source(self.cs_queue)
            },
            "valorant": {
                "pending": len(self.val_queue),
                "by_priority": self._count_by_priority(self.val_queue),
                "by_source": self._count_by_source(self.val_queue)
            },
            "pending_dependencies": len(self.pending_dependencies),
            "completed_jobs": len(self.completed_jobs),
            "total_jobs": len(self._jobs)
        }
    
    def get_queue_stats_model(self) -> QueueStats:
        """Get queue statistics as a QueueStats model."""
        cs_stats = QueueStats(
            pending=len(self.cs_queue),
            by_priority=self._count_by_priority(self.cs_queue),
            by_source=self._count_by_source(self.cs_queue)
        )
        return cs_stats
    
    async def requeue_job(self, job_id: str) -> bool:
        """
        Requeue a job (e.g., after agent failure).
        
        Args:
            job_id: ID of job to requeue
            
        Returns:
            True if job was requeued
        """
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            if job.retry_count >= job.max_retries:
                logger.warning(f"Job {job_id} exceeded max retries, not requeueing")
                return False
            
            job.retry_count += 1
            job.status = JobStatus.PENDING
            job.assigned_agent = None
            job.started_at = None
            
            queue = self._get_queue(job.game)
            heapq.heappush(queue, (-job.priority, job.created_at.timestamp(), job))
            
            logger.info(f"Requeued job {job_id} (retry {job.retry_count}/{job.max_retries})")
            return True
    
    async def purge_completed(self, max_age_hours: int = 24) -> int:
        """
        Purge old completed jobs from memory.
        
        Args:
            max_age_hours: Maximum age in hours to keep
            
        Returns:
            Number of jobs purged
        """
        async with self._lock:
            now = datetime.utcnow()
            to_purge = []
            
            for job_id, job in self._jobs.items():
                if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                    if job.completed_at:
                        age_hours = (now - job.completed_at).total_seconds() / 3600
                        if age_hours > max_age_hours:
                            to_purge.append(job_id)
            
            for job_id in to_purge:
                del self._jobs[job_id]
                self.completed_jobs.discard(job_id)
                self._job_signatures.discard(self._generate_signature(self._jobs.get(job_id)))
            
            if to_purge:
                logger.info(f"Purged {len(to_purge)} old jobs from memory")
            
            return len(to_purge)
