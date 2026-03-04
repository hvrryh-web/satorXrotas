"""
Pipeline Scheduler
==================

Schedule and trigger pipeline runs.
Supports: cron schedules, webhooks, manual triggers, event-based.
"""

import asyncio
import hashlib
import hmac
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Optional
from uuid import uuid4

from pipeline.config import PipelineConfig
from pipeline.models import JobStatus, ScheduledJob, TriggerType
from pipeline.runner import PipelineRunner
from pipeline.state_store import StateStore

try:
    from croniter import croniter
    CRONITER_AVAILABLE = True
except ImportError:
    CRONITER_AVAILABLE = False
    croniter = None

logger = logging.getLogger(__name__)


class PipelineScheduler:
    """
    Schedule and trigger pipeline runs.
    Supports: cron schedules, webhooks, manual triggers, event-based.
    """
    
    def __init__(
        self,
        state_store: Optional[StateStore] = None,
        runner: Optional[PipelineRunner] = None,
    ):
        self.state_store = state_store
        self.runner = runner
        self._scheduled_jobs: dict[str, ScheduledJob] = {}
        self._webhook_secrets: dict[str, str] = {}
        self._event_handlers: list[Callable] = []
        self._running = False
        self._check_interval = 60  # Check cron jobs every 60 seconds
    
    async def schedule_cron(
        self,
        name: str,
        cron: str,
        pipeline_args: dict,
        description: str = "",
    ) -> ScheduledJob:
        """
        Schedule recurring pipeline run.
        Example: schedule_cron('daily-delta', '0 6 * * *', {'mode': 'delta'})
        """
        if not CRONITER_AVAILABLE:
            raise RuntimeError("croniter not installed. Run: pip install croniter")
        
        # Validate cron expression
        if not croniter.is_valid(cron):
            raise ValueError(f"Invalid cron expression: {cron}")
        
        now = datetime.utcnow()
        
        # Calculate next run time
        itr = croniter(cron, now)
        next_run = itr.get_next(datetime)
        
        job = ScheduledJob(
            job_id=str(uuid4()),
            name=name,
            description=description or f"Cron job: {cron}",
            trigger_type=TriggerType.CRON,
            cron_expression=cron,
            webhook_secret=None,
            event_filter=None,
            pipeline_args=pipeline_args,
            status=JobStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            next_run_at=next_run,
        )
        
        # Persist to state store
        if self.state_store:
            await self.state_store.save_scheduled_job(job)
        
        self._scheduled_jobs[job.job_id] = job
        
        logger.info(f"Scheduled cron job '{name}' with expression '{cron}'")
        return job
    
    async def trigger_manual(self, pipeline_args: dict) -> str:
        """Trigger immediate pipeline run, return run_id."""
        if not self.runner:
            raise RuntimeError("No runner configured")
        
        # Create config from args
        config = PipelineConfig(**pipeline_args)
        
        # Start run
        run = await self.runner.start_run(
            config=config,
            trigger_type=TriggerType.MANUAL,
        )
        
        # Record trigger
        if self.state_store:
            await self.state_store.record_trigger(
                run_id=run.run_id,
                trigger_type=TriggerType.MANUAL,
                triggered_by="manual",
            )
        
        logger.info(f"Manually triggered pipeline run: {run.run_id}")
        return run.run_id
    
    async def trigger_webhook(
        self,
        webhook_secret: str,
        payload: dict,
        signature: Optional[str] = None,
    ) -> str:
        """
        Trigger via webhook (for external integrations).
        
        Args:
            webhook_secret: The secret key for this webhook
            payload: The webhook payload
            signature: Optional HMAC signature for verification
        
        Returns:
            run_id of the triggered run
        """
        # Verify signature if provided
        if signature:
            expected = hmac.new(
                webhook_secret.encode(),
                str(payload).encode(),
                hashlib.sha256,
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected):
                raise PermissionError("Invalid webhook signature")
        
        # Find job by webhook secret
        job = None
        for j in self._scheduled_jobs.values():
            if j.webhook_secret == webhook_secret:
                job = j
                break
        
        if not job and self.state_store:
            # Search in database
            jobs = await self.state_store.list_scheduled_jobs()
            for j in jobs:
                if j.webhook_secret == webhook_secret:
                    job = j
                    break
        
        if not job:
            raise ValueError("No job found for webhook secret")
        
        if job.status != JobStatus.ACTIVE:
            raise RuntimeError(f"Job is not active: {job.status.value}")
        
        # Trigger run
        if not self.runner:
            raise RuntimeError("No runner configured")
        
        config = PipelineConfig(**job.pipeline_args)
        
        # Merge webhook payload into config if applicable
        if "webhook_data" in payload:
            config.__dict__.update(payload["webhook_data"])
        
        run = await self.runner.start_run(
            config=config,
            trigger_type=TriggerType.WEBHOOK,
        )
        
        # Update job stats
        job.last_run_at = datetime.utcnow()
        job.run_count += 1
        job.updated_at = job.last_run_at
        
        if self.state_store:
            await self.state_store.save_scheduled_job(job)
            await self.state_store.record_trigger(
                run_id=run.run_id,
                trigger_type=TriggerType.WEBHOOK,
                webhook_payload=payload,
            )
        
        logger.info(f"Webhook triggered pipeline run: {run.run_id}")
        return run.run_id
    
    async def create_webhook_job(
        self,
        name: str,
        pipeline_args: dict,
        description: str = "",
        secret: Optional[str] = None,
    ) -> ScheduledJob:
        """
        Create a webhook-triggered job.
        
        Args:
            name: Job name
            pipeline_args: Pipeline configuration arguments
            description: Job description
            secret: Optional webhook secret (generated if not provided)
        
        Returns:
            ScheduledJob with webhook_secret set
        """
        if secret is None:
            secret = hashlib.sha256(str(uuid4()).encode()).hexdigest()[:32]
        
        now = datetime.utcnow()
        
        job = ScheduledJob(
            job_id=str(uuid4()),
            name=name,
            description=description or f"Webhook job: {name}",
            trigger_type=TriggerType.WEBHOOK,
            cron_expression=None,
            webhook_secret=secret,
            event_filter=None,
            pipeline_args=pipeline_args,
            status=JobStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        
        if self.state_store:
            await self.state_store.save_scheduled_job(job)
        
        self._scheduled_jobs[job.job_id] = job
        self._webhook_secrets[secret] = job.job_id
        
        logger.info(f"Created webhook job '{name}' with secret '{secret[:8]}...'")
        return job
    
    async def create_event_job(
        self,
        name: str,
        event_filter: dict,
        pipeline_args: dict,
        description: str = "",
    ) -> ScheduledJob:
        """
        Create an event-triggered job.
        
        Args:
            name: Job name
            event_filter: Filter for events (e.g., {'type': 'match_completed'})
            pipeline_args: Pipeline configuration arguments
            description: Job description
        
        Returns:
            ScheduledJob
        """
        now = datetime.utcnow()
        
        job = ScheduledJob(
            job_id=str(uuid4()),
            name=name,
            description=description or f"Event job: {name}",
            trigger_type=TriggerType.EVENT,
            cron_expression=None,
            webhook_secret=None,
            event_filter=event_filter,
            pipeline_args=pipeline_args,
            status=JobStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        
        if self.state_store:
            await self.state_store.save_scheduled_job(job)
        
        self._scheduled_jobs[job.job_id] = job
        
        logger.info(f"Created event job '{name}' with filter {event_filter}")
        return job
    
    async def trigger_event(self, event_type: str, event_data: dict) -> list[str]:
        """
        Trigger event-based jobs.
        
        Args:
            event_type: Type of event
            event_data: Event payload
        
        Returns:
            List of triggered run_ids
        """
        run_ids = []
        
        event = {
            "type": event_type,
            "data": event_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Check all event jobs
        for job in list(self._scheduled_jobs.values()):
            if job.status != JobStatus.ACTIVE:
                continue
            if job.trigger_type != TriggerType.EVENT:
                continue
            
            # Check if event matches filter
            if not self._event_matches(job.event_filter, event):
                continue
            
            # Trigger run
            if self.runner:
                config = PipelineConfig(**job.pipeline_args)
                
                # Merge event data
                if "event_data" not in config.__dict__:
                    config.__dict__["event_data"] = {}
                config.__dict__["event_data"].update(event_data)
                
                run = await self.runner.start_run(
                    config=config,
                    trigger_type=TriggerType.EVENT,
                )
                
                run_ids.append(run.run_id)
                
                # Update job stats
                job.last_run_at = datetime.utcnow()
                job.run_count += 1
                job.updated_at = job.last_run_at
                
                if self.state_store:
                    await self.state_store.save_scheduled_job(job)
        
        logger.info(f"Event '{event_type}' triggered {len(run_ids)} pipeline runs")
        return run_ids
    
    def _event_matches(self, filter_dict: dict, event: dict) -> bool:
        """Check if event matches the filter."""
        if not filter_dict:
            return True
        
        for key, value in filter_dict.items():
            if key not in event:
                return False
            if isinstance(value, dict) and isinstance(event[key], dict):
                if not self._event_matches(value, event[key]):
                    return False
            elif event[key] != value:
                return False
        
        return True
    
    async def list_scheduled_jobs(self) -> list[ScheduledJob]:
        """List all scheduled jobs."""
        if self.state_store:
            return await self.state_store.list_scheduled_jobs()
        
        return list(self._scheduled_jobs.values())
    
    async def get_job(self, job_id: str) -> Optional[ScheduledJob]:
        """Get a job by ID."""
        if job_id in self._scheduled_jobs:
            return self._scheduled_jobs[job_id]
        
        if self.state_store:
            return await self.state_store.get_scheduled_job(job_id)
        
        return None
    
    async def get_job_by_name(self, name: str) -> Optional[ScheduledJob]:
        """Get a job by name."""
        for job in self._scheduled_jobs.values():
            if job.name == name:
                return job
        
        if self.state_store:
            return await self.state_store.get_scheduled_job_by_name(name)
        
        return None
    
    async def pause_job(self, job_id: str) -> bool:
        """Pause a scheduled job."""
        job = await self.get_job(job_id)
        if not job:
            return False
        
        job.status = JobStatus.PAUSED
        job.updated_at = datetime.utcnow()
        
        if self.state_store:
            await self.state_store.save_scheduled_job(job)
        
        if job_id in self._scheduled_jobs:
            self._scheduled_jobs[job_id] = job
        
        logger.info(f"Paused job '{job.name}' ({job_id})")
        return True
    
    async def resume_job(self, job_id: str) -> bool:
        """Resume a paused job."""
        job = await self.get_job(job_id)
        if not job:
            return False
        
        job.status = JobStatus.ACTIVE
        job.updated_at = datetime.utcnow()
        
        # Recalculate next run for cron jobs
        if job.cron_expression and CRONITER_AVAILABLE:
            itr = croniter(job.cron_expression, datetime.utcnow())
            job.next_run_at = itr.get_next(datetime)
        
        if self.state_store:
            await self.state_store.save_scheduled_job(job)
        
        if job_id in self._scheduled_jobs:
            self._scheduled_jobs[job_id] = job
        
        logger.info(f"Resumed job '{job.name}' ({job_id})")
        return True
    
    async def delete_job(self, job_id: str) -> bool:
        """Delete a scheduled job."""
        job = await self.get_job(job_id)
        if not job:
            return False
        
        if self.state_store:
            await self.state_store.delete_scheduled_job(job_id)
        
        if job_id in self._scheduled_jobs:
            del self._scheduled_jobs[job_id]
        
        if job.webhook_secret and job.webhook_secret in self._webhook_secrets:
            del self._webhook_secrets[job.webhook_secret]
        
        logger.info(f"Deleted job '{job.name}' ({job_id})")
        return True
    
    async def run_scheduler_loop(self) -> None:
        """Main scheduler loop - checks cron jobs and triggers them."""
        if not CRONITER_AVAILABLE:
            logger.warning("croniter not installed, scheduler loop will not run")
            return
        
        self._running = True
        logger.info("Scheduler loop started")
        
        while self._running:
            try:
                await self._check_cron_jobs()
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
            
            # Wait for next check
            for _ in range(self._check_interval):
                if not self._running:
                    break
                await asyncio.sleep(1)
        
        logger.info("Scheduler loop stopped")
    
    async def _check_cron_jobs(self) -> None:
        """Check and trigger due cron jobs."""
        now = datetime.utcnow()
        
        # Reload jobs from store to get updates
        if self.state_store:
            jobs = await self.state_store.list_scheduled_jobs(status=JobStatus.ACTIVE)
            for job in jobs:
                if job.trigger_type == TriggerType.CRON:
                    self._scheduled_jobs[job.job_id] = job
        
        for job in list(self._scheduled_jobs.values()):
            if job.status != JobStatus.ACTIVE:
                continue
            if job.trigger_type != TriggerType.CRON:
                continue
            if not job.cron_expression:
                continue
            
            # Check if it's time to run
            if job.next_run_at and now >= job.next_run_at:
                if self.runner:
                    try:
                        config = PipelineConfig(**job.pipeline_args)
                        run = await self.runner.start_run(
                            config=config,
                            trigger_type=TriggerType.CRON,
                        )
                        
                        # Update job stats
                        job.last_run_at = now
                        job.run_count += 1
                        
                        # Calculate next run
                        itr = croniter(job.cron_expression, now)
                        job.next_run_at = itr.get_next(datetime)
                        job.updated_at = now
                        
                        if self.state_store:
                            await self.state_store.save_scheduled_job(job)
                        
                        logger.info(
                            f"Triggered cron job '{job.name}', next run at {job.next_run_at}"
                        )
                        
                    except Exception as e:
                        job.failure_count += 1
                        logger.error(f"Failed to trigger cron job '{job.name}': {e}")
                        
                        if job.failure_count >= 5:
                            job.status = JobStatus.ERROR
                            logger.error(f"Job '{job.name}' disabled due to failures")
                        
                        if self.state_store:
                            await self.state_store.save_scheduled_job(job)
    
    def stop(self) -> None:
        """Stop the scheduler loop."""
        self._running = False
    
    async def load_jobs(self) -> None:
        """Load jobs from state store."""
        if self.state_store:
            jobs = await self.state_store.list_scheduled_jobs()
            for job in jobs:
                self._scheduled_jobs[job.job_id] = job
                if job.webhook_secret:
                    self._webhook_secrets[job.webhook_secret] = job.job_id
            
            logger.info(f"Loaded {len(jobs)} scheduled jobs from database")
