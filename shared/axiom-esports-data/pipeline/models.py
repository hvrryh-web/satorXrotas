"""
Pipeline Data Models
====================

Core data models for pipeline scheduling, execution, and state management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Optional
from uuid import uuid4


class RunStatus(Enum):
    """Pipeline run status states."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class JobStatus(Enum):
    """Scheduled job status states."""
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    ERROR = "error"


class TriggerType(Enum):
    """Types of pipeline triggers."""
    CRON = "cron"
    MANUAL = "manual"
    WEBHOOK = "webhook"
    EVENT = "event"


@dataclass
class LogEntry:
    """Single log entry for a pipeline run."""
    timestamp: datetime
    level: str  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message: str
    source: str = ""  # Component that generated the log
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "message": self.message,
            "source": self.source,
            "metadata": self.metadata,
        }


@dataclass
class Checkpoint:
    """Pipeline execution checkpoint for resumption."""
    checkpoint_id: str
    run_id: str
    stage: str
    completed_match_ids: list[str]
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        return {
            "checkpoint_id": self.checkpoint_id,
            "run_id": self.run_id,
            "stage": self.stage,
            "completed_match_ids": self.completed_match_ids,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class RunMetrics:
    """Metrics collected during a pipeline run."""
    records_processed: int = 0
    records_failed: int = 0
    records_skipped: int = 0
    stages_completed: list[str] = field(default_factory=list)
    current_stage: Optional[str] = None
    stage_progress: dict = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "records_processed": self.records_processed,
            "records_failed": self.records_failed,
            "records_skipped": self.records_skipped,
            "stages_completed": self.stages_completed,
            "current_stage": self.current_stage,
            "stage_progress": self.stage_progress,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
        }


@dataclass
class RunInstance:
    """Complete pipeline run instance."""
    run_id: str
    config: dict[str, Any]
    status: RunStatus
    trigger_type: TriggerType
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metrics: RunMetrics = field(default_factory=RunMetrics)
    logs: list[LogEntry] = field(default_factory=list)
    error_message: Optional[str] = None
    retry_count: int = 0
    parent_run_id: Optional[str] = None  # For retry chains
    
    def __post_init__(self):
        if not self.run_id:
            self.run_id = str(uuid4())
    
    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "config": self.config,
            "status": self.status.value,
            "trigger_type": self.trigger_type.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metrics": self.metrics.to_dict(),
            "logs": [log.to_dict() for log in self.logs],
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "parent_run_id": self.parent_run_id,
        }


@dataclass
class RunSummary:
    """Summary of a pipeline run for listing."""
    run_id: str
    status: str
    trigger_type: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: float
    records_processed: int
    records_failed: int
    
    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "trigger_type": self.trigger_type,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "records_processed": self.records_processed,
            "records_failed": self.records_failed,
        }


@dataclass
class ScheduledJob:
    """Scheduled pipeline job configuration."""
    job_id: str
    name: str
    description: str
    trigger_type: TriggerType
    cron_expression: Optional[str]  # For CRON triggers
    webhook_secret: Optional[str]   # For WEBHOOK triggers
    event_filter: Optional[dict]    # For EVENT triggers
    pipeline_args: dict[str, Any]
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    run_count: int = 0
    failure_count: int = 0
    
    def __post_init__(self):
        if not self.job_id:
            self.job_id = str(uuid4())
    
    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "name": self.name,
            "description": self.description,
            "trigger_type": self.trigger_type.value,
            "cron_expression": self.cron_expression,
            "event_filter": self.event_filter,
            "pipeline_args": self.pipeline_args,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "run_count": self.run_count,
            "failure_count": self.failure_count,
        }


@dataclass
class HealthStatus:
    """Daemon health status."""
    status: str  # healthy, degraded, unhealthy
    version: str
    uptime_seconds: float
    active_runs: int
    queued_runs: int
    scheduled_jobs: int
    last_check_at: datetime
    checks: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "version": self.version,
            "uptime_seconds": self.uptime_seconds,
            "active_runs": self.active_runs,
            "queued_runs": self.queued_runs,
            "scheduled_jobs": self.scheduled_jobs,
            "last_check_at": self.last_check_at.isoformat(),
            "checks": self.checks,
        }
