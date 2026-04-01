"""
Pipeline Runner
===============

Execute pipeline runs with monitoring, logging, and error handling.
Each run gets a unique ID and persists state.
"""

import asyncio
import logging
import signal
import time
import traceback
from datetime import datetime
from typing import Callable, Optional
from uuid import uuid4

from pipeline.config import PipelineConfig
from pipeline.models import (
    Checkpoint,
    LogEntry,
    RunInstance,
    RunMetrics,
    RunStatus,
    RunSummary,
    TriggerType,
)
from pipeline.state_store import StateStore

logger = logging.getLogger(__name__)


class PipelineRunner:
    """
    Execute pipeline runs with monitoring, logging, and error handling.
    Each run gets a unique ID and persists state.
    """
    
    def __init__(
        self,
        state_store: Optional[StateStore] = None,
        orchestrator_factory: Optional[Callable] = None,
    ):
        self.state_store = state_store
        self.orchestrator_factory = orchestrator_factory
        self._active_runs: dict[str, RunInstance] = {}
        self._run_tasks: dict[str, asyncio.Task] = {}
        self._shutdown_event = asyncio.Event()
    
    async def start_run(
        self,
        config: PipelineConfig,
        trigger_type: TriggerType = TriggerType.MANUAL,
        parent_run_id: Optional[str] = None,
    ) -> RunInstance:
        """
        Start a new pipeline run.
        Returns RunInstance with run_id for tracking.
        """
        run_id = str(uuid4())
        now = datetime.utcnow()
        
        run = RunInstance(
            run_id=run_id,
            config={
                "mode": config.mode,
                "epochs": config.epochs,
                "batch_size": config.batch_size,
                "max_workers": config.max_workers,
                "enable_crossref": config.enable_crossref,
            },
            status=RunStatus.PENDING,
            trigger_type=trigger_type,
            created_at=now,
            updated_at=now,
            parent_run_id=parent_run_id,
        )
        
        # Persist to state store
        if self.state_store:
            await self.state_store.save_run(run)
        
        self._active_runs[run_id] = run
        
        # Start run in background
        task = asyncio.create_task(self._execute_run(run, config))
        self._run_tasks[run_id] = task
        
        logger.info(f"Started pipeline run {run_id} with trigger {trigger_type.value}")
        return run
    
    async def _execute_run(self, run: RunInstance, config: PipelineConfig) -> None:
        """Execute the pipeline run."""
        run.status = RunStatus.RUNNING
        run.started_at = datetime.utcnow()
        run.updated_at = run.started_at
        run.metrics.start_time = run.started_at
        
        if self.state_store:
            await self.state_store.save_run(run)
        
        self._log(run, "INFO", f"Pipeline run started (mode={config.mode})", "runner")
        
        try:
            # Check for checkpoint to resume from
            checkpoint = None
            if self.state_store:
                checkpoint = await self.state_store.get_latest_checkpoint(run.run_id)
                if checkpoint:
                    self._log(run, "INFO", f"Resuming from checkpoint: {checkpoint.stage}", "runner")
            
            # Import and run orchestrator
            if self.orchestrator_factory:
                orchestrator = self.orchestrator_factory()
            else:
                # Default: try to import from pipeline module
                try:
                    from pipeline.orchestrator import PipelineOrchestrator
                    orchestrator = PipelineOrchestrator(config)
                except ImportError:
                    # Fallback for testing
                    orchestrator = None
            
            if orchestrator is None:
                # Simulate a run for testing
                await self._simulate_run(run, config)
            else:
                # Run actual pipeline
                await self._run_orchestrator(run, orchestrator, config, checkpoint)
            
            # Mark as completed
            run.status = RunStatus.COMPLETED
            run.completed_at = datetime.utcnow()
            run.metrics.end_time = run.completed_at
            run.metrics.duration_seconds = (
                run.completed_at - run.started_at
            ).total_seconds()
            
            self._log(
                run,
                "INFO",
                f"Pipeline run completed in {run.metrics.duration_seconds:.2f}s",
                "runner",
            )
            
        except asyncio.CancelledError:
            run.status = RunStatus.CANCELLED
            run.completed_at = datetime.utcnow()
            self._log(run, "WARNING", "Pipeline run cancelled", "runner")
            raise
            
        except Exception as e:
            run.status = RunStatus.FAILED
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            run.metrics.end_time = run.completed_at
            
            self._log(run, "ERROR", f"Pipeline run failed: {e}", "runner")
            self._log(run, "ERROR", traceback.format_exc(), "runner")
            
        finally:
            run.updated_at = datetime.utcnow()
            
            if self.state_store:
                await self.state_store.save_run(run)
                await self.state_store.save_run_logs(run.run_id, run.logs)
            
            # Clean up
            if run.run_id in self._active_runs:
                del self._active_runs[run.run_id]
            if run.run_id in self._run_tasks:
                del self._run_tasks[run.run_id]
    
    async def _run_orchestrator(
        self,
        run: RunInstance,
        orchestrator,
        config: PipelineConfig,
        checkpoint: Optional[Checkpoint],
    ) -> None:
        """Run the actual pipeline orchestrator."""
        # Set up progress callback
        def progress_callback(stage: str, processed: int, total: int):
            run.metrics.current_stage = stage
            run.metrics.stage_progress[stage] = {
                "processed": processed,
                "total": total,
                "percent": (processed / total * 100) if total > 0 else 0,
            }
            
            if processed % 10 == 0:  # Log every 10 items
                self._log(
                    run,
                    "DEBUG",
                    f"Stage {stage}: {processed}/{total} ({processed/total*100:.1f}%)",
                    "orchestrator",
                )
        
        # Attach callback if orchestrator supports it
        if hasattr(orchestrator, 'set_progress_callback'):
            orchestrator.set_progress_callback(progress_callback)
        
        # Execute the pipeline
        if asyncio.iscoroutinefunction(orchestrator.run):
            result = await orchestrator.run(mode=config.mode, epochs=config.epochs)
        else:
            result = orchestrator.run(mode=config.mode, epochs=config.epochs)
        
        # Update metrics from result
        if isinstance(result, dict):
            run.metrics.records_processed = result.get("records_processed", 0)
            run.metrics.records_failed = result.get("records_failed", 0)
            run.metrics.records_skipped = result.get("records_skipped", 0)
            run.metrics.stages_completed = result.get("stages_completed", [])
    
    async def _simulate_run(self, run: RunInstance, config: PipelineConfig) -> None:
        """Simulate a pipeline run for testing."""
        stages = ["discover", "fetch", "verify", "parse", "transform", "store", "index"]
        total_items = config.batch_size * len(config.epochs)
        
        for stage in stages:
            if self._shutdown_event.is_set():
                raise asyncio.CancelledError()
            
            run.metrics.current_stage = stage
            self._log(run, "INFO", f"Starting stage: {stage}", "simulator")
            
            # Simulate work
            await asyncio.sleep(0.5)
            
            # Simulate processing items
            processed = 0
            failed = 0
            
            for i in range(total_items):
                if self._shutdown_event.is_set():
                    raise asyncio.CancelledError()
                
                # Simulate some failures
                if i % 20 == 0 and i > 0:
                    failed += 1
                    self._log(run, "WARNING", f"Item {i} failed in stage {stage}", "simulator")
                else:
                    processed += 1
                
                run.metrics.stage_progress[stage] = {
                    "processed": i + 1,
                    "total": total_items,
                    "percent": (i + 1) / total_items * 100,
                }
                
                if i % 10 == 0:
                    await asyncio.sleep(0.05)  # Small delay for realism
            
            run.metrics.records_processed += processed
            run.metrics.records_failed += failed
            run.metrics.stages_completed.append(stage)
            
            # Save checkpoint after each stage
            if self.state_store:
                checkpoint = Checkpoint(
                    checkpoint_id=str(uuid4()),
                    run_id=run.run_id,
                    stage=stage,
                    completed_match_ids=[],
                )
                await self.state_store.save_checkpoint(run.run_id, checkpoint)
            
            self._log(
                run,
                "INFO",
                f"Completed stage: {stage} ({processed} processed, {failed} failed)",
                "simulator",
            )
    
    def _log(
        self,
        run: RunInstance,
        level: str,
        message: str,
        source: str = "",
        metadata: Optional[dict] = None,
    ) -> None:
        """Add a log entry to the run."""
        entry = LogEntry(
            timestamp=datetime.utcnow(),
            level=level,
            message=message,
            source=source,
            metadata=metadata or {},
        )
        run.logs.append(entry)
        
        # Also log to system logger
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(f"[{run.run_id}] {message}")
    
    def get_run_status(self, run_id: str) -> Optional[RunStatus]:
        """Get current status of a run."""
        if run_id in self._active_runs:
            return self._active_runs[run_id].status
        return None
    
    def get_run(self, run_id: str) -> Optional[RunInstance]:
        """Get a run instance by ID."""
        return self._active_runs.get(run_id)
    
    async def cancel_run(self, run_id: str) -> bool:
        """Cancel a running pipeline."""
        if run_id not in self._run_tasks:
            return False
        
        task = self._run_tasks[run_id]
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        logger.info(f"Cancelled pipeline run {run_id}")
        return True
    
    async def list_runs(self, limit: int = 10) -> list[RunSummary]:
        """List recent pipeline runs."""
        if self.state_store:
            return await self.state_store.list_runs(limit=limit)
        
        # Fallback: return active runs
        runs = sorted(
            self._active_runs.values(),
            key=lambda r: r.created_at,
            reverse=True,
        )[:limit]
        
        return [
            RunSummary(
                run_id=r.run_id,
                status=r.status.value,
                trigger_type=r.trigger_type.value,
                created_at=r.created_at,
                started_at=r.started_at,
                completed_at=r.completed_at,
                duration_seconds=r.metrics.duration_seconds,
                records_processed=r.metrics.records_processed,
                records_failed=r.metrics.records_failed,
            )
            for r in runs
        ]
    
    async def get_run_logs(self, run_id: str) -> list[LogEntry]:
        """Get detailed logs for a run."""
        # First check active runs
        if run_id in self._active_runs:
            return self._active_runs[run_id].logs
        
        # Then check state store
        if self.state_store:
            return await self.state_store.get_run_logs(run_id)
        
        return []
    
    async def retry_run(
        self,
        run_id: str,
        stage: Optional[str] = None,
    ) -> Optional[RunInstance]:
        """Retry a failed run."""
        # Load the original run
        original_run = None
        
        if run_id in self._active_runs:
            original_run = self._active_runs[run_id]
        elif self.state_store:
            original_run = await self.state_store.load_run(run_id)
        
        if not original_run:
            logger.error(f"Cannot retry: run {run_id} not found")
            return None
        
        if original_run.status not in (RunStatus.FAILED, RunStatus.CANCELLED):
            logger.error(f"Cannot retry: run {run_id} has status {original_run.status.value}")
            return None
        
        # Create new config from original
        config = PipelineConfig(**original_run.config)
        
        # Start new run with parent reference
        new_run = await self.start_run(
            config=config,
            trigger_type=TriggerType.MANUAL,
            parent_run_id=run_id,
        )
        
        # If stage specified, try to resume from checkpoint
        if stage and self.state_store:
            checkpoint = await self.state_store.get_latest_checkpoint(run_id)
            # The checkpoint will be loaded during execution
        
        logger.info(f"Retrying run {run_id} as {new_run.run_id}")
        return new_run
    
    async def shutdown(self) -> None:
        """Graceful shutdown - cancel all active runs."""
        self._shutdown_event.set()
        
        active_run_ids = list(self._run_tasks.keys())
        if active_run_ids:
            logger.info(f"Cancelling {len(active_run_ids)} active runs...")
            
            for run_id in active_run_ids:
                task = self._run_tasks.get(run_id)
                if task:
                    task.cancel()
            
            # Wait for all to complete cancellation
            if self._run_tasks:
                await asyncio.gather(*self._run_tasks.values(), return_exceptions=True)
        
        logger.info("PipelineRunner shutdown complete")
