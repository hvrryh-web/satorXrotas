"""
Pipeline State Store
====================

Persistent state management for pipeline runs, schedules, and checkpoints.
Uses PostgreSQL for storage with asyncpg for async operations.
"""

import json
import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

from pipeline.config import PipelineConfig
from pipeline.models import (
    Checkpoint,
    JobStatus,
    LogEntry,
    RunInstance,
    RunMetrics,
    RunStatus,
    RunSummary,
    ScheduledJob,
    TriggerType,
)

try:
    import asyncpg
except ImportError:
    asyncpg = None

logger = logging.getLogger(__name__)


# SQL Schema for creating state store tables
SCHEMA_SQL = """
-- Pipeline runs table
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id UUID PRIMARY KEY,
    config JSONB NOT NULL,
    status VARCHAR(20) NOT NULL,
    trigger_type VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    metrics JSONB NOT NULL DEFAULT '{}',
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    parent_run_id UUID REFERENCES pipeline_runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status ON pipeline_runs(status);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_created_at ON pipeline_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_trigger_type ON pipeline_runs(trigger_type);

-- Pipeline run logs table
CREATE TABLE IF NOT EXISTS pipeline_run_logs (
    log_id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    level VARCHAR(10) NOT NULL,
    message TEXT NOT NULL,
    source VARCHAR(100),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_pipeline_run_logs_run_id ON pipeline_run_logs(run_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_run_logs_timestamp ON pipeline_run_logs(timestamp DESC);

-- Scheduled jobs table
CREATE TABLE IF NOT EXISTS pipeline_scheduled_jobs (
    job_id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    trigger_type VARCHAR(20) NOT NULL,
    cron_expression VARCHAR(100),
    webhook_secret VARCHAR(255),
    event_filter JSONB,
    pipeline_args JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    run_count INTEGER NOT NULL DEFAULT 0,
    failure_count INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_pipeline_scheduled_jobs_status ON pipeline_scheduled_jobs(status);
CREATE INDEX IF NOT EXISTS idx_pipeline_scheduled_jobs_next_run ON pipeline_scheduled_jobs(next_run_at);

-- Checkpoints table
CREATE TABLE IF NOT EXISTS pipeline_checkpoints (
    checkpoint_id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    stage VARCHAR(50) NOT NULL,
    completed_match_ids JSONB NOT NULL DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pipeline_checkpoints_run_id ON pipeline_checkpoints(run_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_checkpoints_created_at ON pipeline_checkpoints(created_at DESC);

-- Run history/triggers table for audit
CREATE TABLE IF NOT EXISTS pipeline_triggers (
    trigger_id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    trigger_type VARCHAR(20) NOT NULL,
    triggered_by VARCHAR(100),
    webhook_payload JSONB,
    triggered_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pipeline_triggers_run_id ON pipeline_triggers(run_id);

-- Daemon metrics table
CREATE TABLE IF NOT EXISTS pipeline_daemon_metrics (
    metric_id SERIAL PRIMARY KEY,
    daemon_id VARCHAR(100) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    metric_value JSONB NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pipeline_daemon_metrics_daemon ON pipeline_daemon_metrics(daemon_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_daemon_metrics_recorded ON pipeline_daemon_metrics(recorded_at DESC);
"""


class StateStore:
    """
    Persist pipeline state to PostgreSQL.
    Stores: run history, schedules, checkpoints, metrics.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url
        self.pool = None
        self._initialized = False
    
    async def connect(self) -> "StateStore":
        """Connect to the database."""
        if asyncpg is None:
            raise RuntimeError("asyncpg not installed. Run: pip install asyncpg")
        
        if self.pool is not None:
            return self
        
        if not self.database_url:
            config = PipelineConfig.from_env()
            self.database_url = config.database_url
        
        if not self.database_url:
            raise ValueError("Database URL not provided")
        
        self.pool = await asyncpg.create_pool(
            dsn=self.database_url,
            min_size=2,
            max_size=10,
            command_timeout=30,
        )
        
        logger.info("StateStore connected to database")
        return self
    
    async def disconnect(self) -> None:
        """Disconnect from the database."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("StateStore disconnected")
    
    async def initialize_schema(self) -> None:
        """Initialize the database schema."""
        if not self.pool:
            raise RuntimeError("Not connected to database")
        
        async with self.pool.acquire() as conn:
            await conn.execute(SCHEMA_SQL)
        
        self._initialized = True
        logger.info("StateStore schema initialized")
    
    async def save_run(self, run: RunInstance) -> None:
        """Persist run to database."""
        if not self.pool:
            raise RuntimeError("Not connected to database")
        
        async with self.pool.acquire() as conn:
            # Upsert run
            await conn.execute(
                """
                INSERT INTO pipeline_runs (
                    run_id, config, status, trigger_type, created_at, updated_at,
                    started_at, completed_at, metrics, error_message, retry_count, parent_run_id
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (run_id) DO UPDATE SET
                    config = EXCLUDED.config,
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at,
                    started_at = EXCLUDED.started_at,
                    completed_at = EXCLUDED.completed_at,
                    metrics = EXCLUDED.metrics,
                    error_message = EXCLUDED.error_message,
                    retry_count = EXCLUDED.retry_count
                """,
                run.run_id,
                json.dumps(run.config),
                run.status.value,
                run.trigger_type.value,
                run.created_at,
                run.updated_at,
                run.started_at,
                run.completed_at,
                json.dumps(run.metrics.to_dict()),
                run.error_message,
                run.retry_count,
                run.parent_run_id,
            )
    
    async def load_run(self, run_id: str) -> Optional[RunInstance]:
        """Load run from database."""
        if not self.pool:
            raise RuntimeError("Not connected to database")
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT run_id, config, status, trigger_type, created_at, updated_at,
                       started_at, completed_at, metrics, error_message, retry_count, parent_run_id
                FROM pipeline_runs WHERE run_id = $1
                """,
                run_id,
            )
            
            if not row:
                return None
            
            return self._row_to_run_instance(row)
    
    async def list_runs(
        self,
        limit: int = 10,
        status: Optional[RunStatus] = None,
        trigger_type: Optional[TriggerType] = None,
    ) -> list[RunSummary]:
        """List recent pipeline runs."""
        if not self.pool:
            raise RuntimeError("Not connected to database")
        
        conditions = []
        params = []
        param_idx = 1
        
        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status.value)
            param_idx += 1
        
        if trigger_type:
            conditions.append(f"trigger_type = ${param_idx}")
            params.append(trigger_type.value)
            param_idx += 1
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT run_id, status, trigger_type, created_at, started_at, completed_at,
                       COALESCE(metrics->>'duration_seconds', '0')::float as duration_seconds,
                       COALESCE(metrics->>'records_processed', '0')::int as records_processed,
                       COALESCE(metrics->>'records_failed', '0')::int as records_failed
                FROM pipeline_runs
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ${param_idx}
                """,
                *params,
                limit,
            )
            
            return [
                RunSummary(
                    run_id=row["run_id"],
                    status=row["status"],
                    trigger_type=row["trigger_type"],
                    created_at=row["created_at"],
                    started_at=row["started_at"],
                    completed_at=row["completed_at"],
                    duration_seconds=row["duration_seconds"],
                    records_processed=row["records_processed"],
                    records_failed=row["records_failed"],
                )
                for row in rows
            ]
    
    async def save_run_logs(self, run_id: str, logs: list[LogEntry]) -> None:
        """Save logs for a run."""
        if not self.pool or not logs:
            return
        
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                for log in logs:
                    await conn.execute(
                        """
                        INSERT INTO pipeline_run_logs 
                        (run_id, timestamp, level, message, source, metadata)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        """,
                        run_id,
                        log.timestamp,
                        log.level,
                        log.message,
                        log.source,
                        json.dumps(log.metadata),
                    )
    
    async def get_run_logs(self, run_id: str, limit: int = 1000) -> list[LogEntry]:
        """Get logs for a run."""
        if not self.pool:
            raise RuntimeError("Not connected to database")
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT timestamp, level, message, source, metadata
                FROM pipeline_run_logs
                WHERE run_id = $1
                ORDER BY timestamp DESC
                LIMIT $2
                """,
                run_id,
                limit,
            )
            
            return [
                LogEntry(
                    timestamp=row["timestamp"],
                    level=row["level"],
                    message=row["message"],
                    source=row["source"] or "",
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                )
                for row in reversed(rows)  # Return in chronological order
            ]
    
    async def save_checkpoint(self, run_id: str, checkpoint: Checkpoint) -> None:
        """Save progress checkpoint."""
        if not self.pool:
            raise RuntimeError("Not connected to database")
        
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO pipeline_checkpoints 
                (checkpoint_id, run_id, stage, completed_match_ids, metadata, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (checkpoint_id) DO UPDATE SET
                    stage = EXCLUDED.stage,
                    completed_match_ids = EXCLUDED.completed_match_ids,
                    metadata = EXCLUDED.metadata
                """,
                checkpoint.checkpoint_id,
                run_id,
                checkpoint.stage,
                json.dumps(checkpoint.completed_match_ids),
                json.dumps(checkpoint.metadata),
                checkpoint.created_at,
            )
    
    async def get_latest_checkpoint(self, run_id: str) -> Optional[Checkpoint]:
        """Load latest checkpoint for resumption."""
        if not self.pool:
            raise RuntimeError("Not connected to database")
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT checkpoint_id, stage, completed_match_ids, metadata, created_at
                FROM pipeline_checkpoints
                WHERE run_id = $1
                ORDER BY created_at DESC
                LIMIT 1
                """,
                run_id,
            )
            
            if not row:
                return None
            
            return Checkpoint(
                checkpoint_id=row["checkpoint_id"],
                run_id=run_id,
                stage=row["stage"],
                completed_match_ids=json.loads(row["completed_match_ids"]),
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                created_at=row["created_at"],
            )
    
    async def save_scheduled_job(self, job: ScheduledJob) -> None:
        """Save a scheduled job."""
        if not self.pool:
            raise RuntimeError("Not connected to database")
        
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO pipeline_scheduled_jobs (
                    job_id, name, description, trigger_type, cron_expression,
                    webhook_secret, event_filter, pipeline_args, status,
                    created_at, updated_at, last_run_at, next_run_at, run_count, failure_count
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                ON CONFLICT (job_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    trigger_type = EXCLUDED.trigger_type,
                    cron_expression = EXCLUDED.cron_expression,
                    webhook_secret = EXCLUDED.webhook_secret,
                    event_filter = EXCLUDED.event_filter,
                    pipeline_args = EXCLUDED.pipeline_args,
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at,
                    last_run_at = EXCLUDED.last_run_at,
                    next_run_at = EXCLUDED.next_run_at,
                    run_count = EXCLUDED.run_count,
                    failure_count = EXCLUDED.failure_count
                """,
                job.job_id,
                job.name,
                job.description,
                job.trigger_type.value,
                job.cron_expression,
                job.webhook_secret,
                json.dumps(job.event_filter) if job.event_filter else None,
                json.dumps(job.pipeline_args),
                job.status.value,
                job.created_at,
                job.updated_at,
                job.last_run_at,
                job.next_run_at,
                job.run_count,
                job.failure_count,
            )
    
    async def get_scheduled_job(self, job_id: str) -> Optional[ScheduledJob]:
        """Get a scheduled job by ID."""
        if not self.pool:
            raise RuntimeError("Not connected to database")
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT job_id, name, description, trigger_type, cron_expression,
                       webhook_secret, event_filter, pipeline_args, status,
                       created_at, updated_at, last_run_at, next_run_at, run_count, failure_count
                FROM pipeline_scheduled_jobs WHERE job_id = $1
                """,
                job_id,
            )
            
            if not row:
                return None
            
            return self._row_to_scheduled_job(row)
    
    async def get_scheduled_job_by_name(self, name: str) -> Optional[ScheduledJob]:
        """Get a scheduled job by name."""
        if not self.pool:
            raise RuntimeError("Not connected to database")
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT job_id, name, description, trigger_type, cron_expression,
                       webhook_secret, event_filter, pipeline_args, status,
                       created_at, updated_at, last_run_at, next_run_at, run_count, failure_count
                FROM pipeline_scheduled_jobs WHERE name = $1
                """,
                name,
            )
            
            if not row:
                return None
            
            return self._row_to_scheduled_job(row)
    
    async def list_scheduled_jobs(self, status: Optional[JobStatus] = None) -> list[ScheduledJob]:
        """List all scheduled jobs."""
        if not self.pool:
            raise RuntimeError("Not connected to database")
        
        query = """
            SELECT job_id, name, description, trigger_type, cron_expression,
                   webhook_secret, event_filter, pipeline_args, status,
                   created_at, updated_at, last_run_at, next_run_at, run_count, failure_count
            FROM pipeline_scheduled_jobs
        """
        params = []
        
        if status:
            query += " WHERE status = $1"
            params.append(status.value)
        
        query += " ORDER BY created_at DESC"
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [self._row_to_scheduled_job(row) for row in rows]
    
    async def delete_scheduled_job(self, job_id: str) -> bool:
        """Delete a scheduled job."""
        if not self.pool:
            raise RuntimeError("Not connected to database")
        
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM pipeline_scheduled_jobs WHERE job_id = $1",
                job_id,
            )
            # result is like "DELETE 1" or "DELETE 0"
            return result != "DELETE 0"
    
    async def record_trigger(
        self,
        run_id: str,
        trigger_type: TriggerType,
        triggered_by: Optional[str] = None,
        webhook_payload: Optional[dict] = None,
    ) -> None:
        """Record a trigger event."""
        if not self.pool:
            return
        
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO pipeline_triggers (run_id, trigger_type, triggered_by, webhook_payload)
                VALUES ($1, $2, $3, $4)
                """,
                run_id,
                trigger_type.value,
                triggered_by,
                json.dumps(webhook_payload) if webhook_payload else None,
            )
    
    def _row_to_run_instance(self, row) -> RunInstance:
        """Convert a database row to RunInstance."""
        metrics_dict = json.loads(row["metrics"]) if row["metrics"] else {}
        metrics = RunMetrics(
            records_processed=metrics_dict.get("records_processed", 0),
            records_failed=metrics_dict.get("records_failed", 0),
            records_skipped=metrics_dict.get("records_skipped", 0),
            stages_completed=metrics_dict.get("stages_completed", []),
            current_stage=metrics_dict.get("current_stage"),
            stage_progress=metrics_dict.get("stage_progress", {}),
            start_time=datetime.fromisoformat(metrics_dict["start_time"]) if metrics_dict.get("start_time") else None,
            end_time=datetime.fromisoformat(metrics_dict["end_time"]) if metrics_dict.get("end_time") else None,
            duration_seconds=metrics_dict.get("duration_seconds", 0.0),
        )
        
        return RunInstance(
            run_id=str(row["run_id"]),
            config=json.loads(row["config"]) if row["config"] else {},
            status=RunStatus(row["status"]),
            trigger_type=TriggerType(row["trigger_type"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            metrics=metrics,
            error_message=row["error_message"],
            retry_count=row["retry_count"],
            parent_run_id=str(row["parent_run_id"]) if row["parent_run_id"] else None,
        )
    
    def _row_to_scheduled_job(self, row) -> ScheduledJob:
        """Convert a database row to ScheduledJob."""
        return ScheduledJob(
            job_id=str(row["job_id"]),
            name=row["name"],
            description=row["description"] or "",
            trigger_type=TriggerType(row["trigger_type"]),
            cron_expression=row["cron_expression"],
            webhook_secret=row["webhook_secret"],
            event_filter=json.loads(row["event_filter"]) if row["event_filter"] else None,
            pipeline_args=json.loads(row["pipeline_args"]) if row["pipeline_args"] else {},
            status=JobStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            last_run_at=row["last_run_at"],
            next_run_at=row["next_run_at"],
            run_count=row["run_count"],
            failure_count=row["failure_count"],
        )
