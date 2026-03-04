"""
Axiom Esports Data Pipeline
============================

Production-ready pipeline orchestrator for coordinating extraction, verification,
and storage of esports match data with deduplication.

Main entry point:
    from pipeline.orchestrator import PipelineOrchestrator
    
    orchestrator = PipelineOrchestrator()
    await orchestrator.run(mode="delta", epochs=[1, 2, 3])

Scheduling and Execution:
    from pipeline.scheduler import PipelineScheduler
    from pipeline.runner import PipelineRunner
    from pipeline.daemon import PipelineDaemon
    
    scheduler = PipelineScheduler()
    await scheduler.schedule_cron('daily-delta', '0 6 * * *', {'mode': 'delta'})
    
    runner = PipelineRunner()
    run = await runner.start_run(config)

CLI Usage:
    axiom-pipeline run --mode=delta --epochs=1,2,3
    axiom-pipeline schedule add --name=daily --cron="0 6 * * *" --mode=delta
    axiom-pipeline status
    axiom-pipeline logs --run-id=abc123 --follow

Pipeline Stages:
    1. DISCOVER: Find match IDs from VLR.gg
    2. FETCH: Download raw HTML (respects registry.should_skip())
    3. VERIFY: Checksum validation, integrity checks
    4. PARSE: Extract structured data from HTML
    5. TRANSFORM: Map to KCRITR schema via extraction_bridge
    6. CROSSREF: Validate against HLTV (if available)
    7. STORE: Write to PostgreSQL
    8. INDEX: Update extraction_log

Components:
    - orchestrator: Main pipeline controller
    - stage_tracker: Per-match stage completion tracking
    - metrics: Prometheus-compatible metrics exporter
    - dead_letter: Failed record queue with retry logic
    - config: Environment-based configuration management
    - scheduler: Cron, webhook, and event-based job scheduling
    - runner: Pipeline execution with lifecycle management
    - daemon: Background service for scheduled jobs
    - state_store: PostgreSQL persistence for runs and checkpoints
    - cli: Rich command-line interface

Installation:
    pip install -e .
    # or
    pip install axiom-pipeline
"""

from pipeline.config import PipelineConfig
from pipeline.daemon import PipelineDaemon
from pipeline.dead_letter import DeadLetterQueue
from pipeline.metrics import PipelineMetrics
from pipeline.models import (
    Checkpoint,
    HealthStatus,
    JobStatus,
    LogEntry,
    RunInstance,
    RunMetrics,
    RunStatus,
    RunSummary,
    ScheduledJob,
    TriggerType,
)
from pipeline.runner import PipelineRunner
from pipeline.scheduler import PipelineScheduler
from pipeline.stage_tracker import StageTracker
from pipeline.state_store import StateStore

__version__ = "1.0.0"

__all__ = [
    # Core components
    "PipelineOrchestrator",
    "PipelineMode",
    "PipelineStage",
    "StageTracker",
    "PipelineMetrics",
    "DeadLetterQueue",
    "PipelineConfig",
    # Scheduling & Execution
    "PipelineScheduler",
    "PipelineRunner",
    "PipelineDaemon",
    # State Management
    "StateStore",
    # Models
    "RunInstance",
    "RunStatus",
    "RunSummary",
    "RunMetrics",
    "ScheduledJob",
    "JobStatus",
    "TriggerType",
    "Checkpoint",
    "LogEntry",
    "HealthStatus",
]

# Deferred import for orchestrator to avoid circular imports
def __getattr__(name):
    if name in ("PipelineOrchestrator", "PipelineMode", "PipelineStage"):
        from pipeline.orchestrator import PipelineOrchestrator, PipelineMode, PipelineStage
        if name == "PipelineOrchestrator":
            return PipelineOrchestrator
        elif name == "PipelineMode":
            return PipelineMode
        elif name == "PipelineStage":
            return PipelineStage
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
