"""
Pydantic models for all coordinator entities.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Literal, Any
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class GameType(str, Enum):
    """Supported esports games."""
    COUNTER_STRIKE = "cs"
    VALORANT = "valorant"


class JobStatus(str, Enum):
    """Job lifecycle states."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SourceType(str, Enum):
    """Supported data sources."""
    HLTV = "hltv"
    VLR = "vlr"
    LIQUIPEDIA = "liquipedia"
    ESL = "esl"
    BLAST = "blast"
    PGL = "pgl"
    FACEIT = "faceit"
    RIOT = "riot"


class ExtractionJob(BaseModel):
    """
    Represents a single data extraction job.
    
    Attributes:
        id: Unique job identifier
        game: Target game (CS or Valorant)
        source: Data source (hltv, vlr, etc.)
        job_type: Type of extraction (match_list, match_detail, player_stats)
        priority: Job priority (1-10, higher is more urgent)
        epoch: Data epoch (1-3)
        region: Optional geographic region filter
        date_start: Optional start date filter
        date_end: Optional end date filter
        status: Current job status
        assigned_agent: ID of agent currently processing this job
        created_at: Job creation timestamp
        started_at: When job processing began
        completed_at: When job finished
        retry_count: Number of retry attempts
        max_retries: Maximum allowed retries
        dependencies: List of job IDs that must complete first
        metadata: Additional job-specific data
        error_message: Error description if job failed
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game: GameType
    source: str = Field(..., description="Data source: hltv, vlr, liquipedia, etc.")
    job_type: str = Field(..., description="Type: match_list, match_detail, player_stats, etc.")
    priority: int = Field(default=5, ge=1, le=10, description="Priority 1-10 (higher = more urgent)")
    epoch: int = Field(default=1, ge=1, le=3, description="Data epoch 1-3")
    region: Optional[str] = None
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    status: JobStatus = JobStatus.PENDING
    assigned_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    dependencies: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    
    model_config = {
        "use_enum_values": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat(),
        }
    }
    
    @field_validator('source')
    @classmethod
    def validate_source(cls, v: str) -> str:
        """Normalize source names."""
        return v.lower().strip()
    
    def to_priority_tuple(self) -> tuple:
        """
        Generate priority tuple for heapq ordering.
        Returns: (negative_priority, timestamp, job_id) for ascending sort
        """
        return (-self.priority, self.created_at.timestamp(), self.id)
    
    def is_ready(self) -> bool:
        """Check if job is ready to be processed."""
        return self.status == JobStatus.PENDING and self.retry_count < self.max_retries
    
    def mark_started(self, agent_id: str) -> None:
        """Mark job as started by an agent."""
        self.status = JobStatus.PROCESSING
        self.assigned_agent = agent_id
        self.started_at = datetime.utcnow()
    
    def mark_completed(self) -> None:
        """Mark job as successfully completed."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
    
    def mark_failed(self, error: str) -> None:
        """Mark job as failed with error message."""
        self.status = JobStatus.FAILED
        self.error_message = error
        self.completed_at = datetime.utcnow()
    
    def can_retry(self) -> bool:
        """Check if job can be retried."""
        return self.retry_count < self.max_retries


class Agent(BaseModel):
    """
    Represents an extraction agent.
    
    Attributes:
        id: Unique agent identifier
        game_specialization: List of games this agent can handle
        source_capabilities: List of sources this agent can extract from
        status: Current agent status
        current_job_id: ID of job currently being processed
        last_heartbeat: Last heartbeat timestamp
        total_jobs_completed: Lifetime completed jobs count
        total_jobs_failed: Lifetime failed jobs count
        rate_limit_remaining: Remaining rate limit by source
    """
    id: str
    game_specialization: List[GameType] = Field(default_factory=list)
    source_capabilities: List[str] = Field(default_factory=list)
    status: Literal["idle", "busy", "offline"] = "idle"
    current_job_id: Optional[str] = None
    last_heartbeat: datetime = Field(default_factory=datetime.utcnow)
    total_jobs_completed: int = 0
    total_jobs_failed: int = 0
    rate_limit_remaining: Dict[str, int] = Field(default_factory=dict)
    
    model_config = {
        "use_enum_values": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat(),
        }
    }
    
    def is_available(self) -> bool:
        """Check if agent is available for new work."""
        return self.status == "idle"
    
    def can_handle(self, job: ExtractionJob) -> bool:
        """Check if agent can handle a specific job."""
        game_match = job.game in [g.value if isinstance(g, str) else g for g in self.game_specialization]
        source_match = job.source in self.source_capabilities
        return game_match and source_match and self.is_available()
    
    def update_heartbeat(self) -> None:
        """Update agent heartbeat timestamp."""
        self.last_heartbeat = datetime.utcnow()
    
    def assign_job(self, job_id: str) -> None:
        """Assign a job to this agent."""
        self.status = "busy"
        self.current_job_id = job_id
    
    def release_job(self, success: bool = True) -> None:
        """Release current job."""
        self.status = "idle"
        self.current_job_id = None
        if success:
            self.total_jobs_completed += 1
        else:
            self.total_jobs_failed += 1


class JobBatch(BaseModel):
    """
    Batch of jobs for efficient processing.
    
    Attributes:
        batch_id: Unique batch identifier
        game: Target game for all jobs in batch
        jobs: List of extraction jobs
        created_at: Batch creation timestamp
        assigned_agent: ID of agent processing this batch
    """
    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game: GameType
    jobs: List[ExtractionJob] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_agent: Optional[str] = None
    
    model_config = {
        "use_enum_values": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat(),
        }
    }
    
    def add_job(self, job: ExtractionJob) -> None:
        """Add a job to the batch."""
        if job.game != self.game:
            raise ValueError(f"Job game {job.game} doesn't match batch game {self.game}")
        self.jobs.append(job)
    
    def size(self) -> int:
        """Get number of jobs in batch."""
        return len(self.jobs)
    
    def is_empty(self) -> bool:
        """Check if batch has no jobs."""
        return len(self.jobs) == 0


class JobResult(BaseModel):
    """
    Result of a job execution.
    
    Attributes:
        job_id: ID of the job
        success: Whether execution succeeded
        data: Extracted data (if successful)
        error: Error message (if failed)
        records_extracted: Number of records extracted
        checksum: Data checksum for integrity
        metadata: Additional result metadata
        completed_at: Completion timestamp
    """
    job_id: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    records_extracted: int = 0
    checksum: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat(),
        }
    }


class QueueStats(BaseModel):
    """Statistics for a single queue."""
    pending: int = 0
    by_priority: Dict[int, int] = Field(default_factory=dict)
    by_source: Dict[str, int] = Field(default_factory=dict)


class CoordinatorStats(BaseModel):
    """Overall coordinator statistics."""
    cs: QueueStats = Field(default_factory=QueueStats)
    valorant: QueueStats = Field(default_factory=QueueStats)
    pending_dependencies: int = 0
    total_agents: int = 0
    idle_agents: int = 0
    busy_agents: int = 0
    offline_agents: int = 0


class RateLimitStatus(BaseModel):
    """Rate limit status for a source."""
    source: str
    limit: int
    remaining: int
    reset_at: Optional[datetime] = None
    window_seconds: int = 60
