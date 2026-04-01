"""
FastAPI application for the Central Job Coordinator API.

Exposes REST endpoints for:
- Job management
- Agent registration and heartbeat
- Queue monitoring
- Health checks
- Administrative operations
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

# Coordinator imports
from .models import (
    ExtractionJob, Agent, GameType, JobStatus, JobBatch, 
    JobResult, CoordinatorStats, QueueStats
)
from .queue_manager import QueueManager
from .agent_manager import AgentManager
from .conflict_resolver import ConflictResolver
from .rate_limiter import RateLimiter, RateLimitConfig, AdaptiveRateLimiter
from .distributor import JobDistributor, DistributionStrategy, SmartDistributor
from .monitoring import CoordinatorMetrics, HealthChecker, record_job_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# Request/Response Models
# =============================================================================

class CreateJobRequest(BaseModel):
    """Request to create a new extraction job."""
    game: GameType
    source: str
    job_type: str
    priority: int = Field(default=5, ge=1, le=10)
    epoch: int = Field(default=1, ge=1, le=3)
    region: Optional[str] = None
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    dependencies: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CreateJobResponse(BaseModel):
    """Response for job creation."""
    job_id: str
    status: str
    message: str


class RegisterAgentRequest(BaseModel):
    """Request to register a new agent."""
    agent_id: str
    game_specialization: List[GameType]
    source_capabilities: List[str]


class HeartbeatResponse(BaseModel):
    """Response to agent heartbeat."""
    agent_id: str
    status: str
    assigned_job: Optional[ExtractionJob] = None
    message: str


class JobCompleteRequest(BaseModel):
    """Request to report job completion."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    records_extracted: int = 0
    checksum: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RateLimitStatusResponse(BaseModel):
    """Rate limit status for a source."""
    source: str
    requests_per_minute: Dict[str, int]
    requests_per_hour: Dict[str, int]
    burst_allowance: int
    is_rate_limited: bool
    backoff_until: Optional[str] = None
    consecutive_failures: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    checks: List[Dict[str, Any]]
    timestamp: str


class CoordinatorStatusResponse(BaseModel):
    """Overall coordinator status."""
    status: str
    version: str = "1.0.0"
    queues: Dict[str, Any]
    agents: Dict[str, Any]
    metrics: Dict[str, Any]
    timestamp: str


# =============================================================================
# Global State (initialized in lifespan)
# =============================================================================

class CoordinatorState:
    """Holds shared coordinator state."""
    def __init__(self):
        self.queue_manager: Optional[QueueManager] = None
        self.agent_manager: Optional[AgentManager] = None
        self.conflict_resolver: Optional[ConflictResolver] = None
        self.rate_limiter: Optional[RateLimiter] = None
        self.distributor: Optional[JobDistributor] = None
        self.metrics: Optional[CoordinatorMetrics] = None
        self.health_checker: Optional[HealthChecker] = None
        self.db_pool = None
        self.redis_client = None
    
    async def initialize(self):
        """Initialize all components."""
        logger.info("Initializing coordinator state...")
        
        # Initialize core components
        self.queue_manager = QueueManager()
        self.agent_manager = AgentManager(self.db_pool, self.queue_manager)
        self.conflict_resolver = ConflictResolver(self.db_pool, self.redis_client)
        self.rate_limiter = AdaptiveRateLimiter(self.redis_client)
        self.distributor = SmartDistributor(
            self.queue_manager,
            self.agent_manager,
            self.rate_limiter,
            self.conflict_resolver
        )
        self.metrics = CoordinatorMetrics()
        self.health_checker = HealthChecker(
            self.queue_manager,
            self.agent_manager,
            self.metrics
        )
        
        # Register health checks
        self.health_checker.register_check(self.health_checker.check_queue_health)
        self.health_checker.register_check(self.health_checker.check_agent_health)
        self.health_checker.register_check(self.health_checker.check_throughput)
        self.health_checker.register_check(self.health_checker.check_error_rate)
        
        # Start background tasks
        await self.agent_manager.start()
        await self.rate_limiter.start()
        await self.health_checker.start()
        
        logger.info("Coordinator state initialized")
    
    async def shutdown(self):
        """Shutdown all components."""
        logger.info("Shutting down coordinator...")
        
        if self.health_checker:
            await self.health_checker.stop()
        if self.rate_limiter:
            await self.rate_limiter.stop()
        if self.agent_manager:
            await self.agent_manager.stop()
        
        logger.info("Coordinator shutdown complete")


coordinator_state = CoordinatorState()


# =============================================================================
# FastAPI Application
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    await coordinator_state.initialize()
    yield
    await coordinator_state.shutdown()


app = FastAPI(
    title="Esports Data Coordinator",
    description="Central job coordinator for dual-game esports data collection",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Esports Data Coordinator",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


# -----------------------------------------------------------------------------
# Job Management Endpoints
# -----------------------------------------------------------------------------

@app.post("/jobs", response_model=CreateJobResponse)
async def create_job(request: CreateJobRequest):
    """
    Create a new extraction job.
    
    The job will be queued for processing by an available agent.
    """
    job = ExtractionJob(
        game=request.game,
        source=request.source,
        job_type=request.job_type,
        priority=request.priority,
        epoch=request.epoch,
        region=request.region,
        date_start=request.date_start,
        date_end=request.date_end,
        dependencies=request.dependencies,
        metadata=request.metadata
    )
    
    # Check for duplicates
    if coordinator_state.conflict_resolver:
        duplicate = await coordinator_state.conflict_resolver.check_duplicate_job(job)
        if duplicate:
            return CreateJobResponse(
                job_id=duplicate,
                status="duplicate",
                message=f"Equivalent job already exists: {duplicate}"
            )
    
    # Enqueue job
    enqueued = await coordinator_state.queue_manager.enqueue(job)
    
    if enqueued:
        return CreateJobResponse(
            job_id=job.id,
            status="created",
            message="Job created and queued"
        )
    else:
        return CreateJobResponse(
            job_id=job.id,
            status="pending",
            message="Job waiting for dependencies"
        )


@app.post("/jobs/batch")
async def create_batch_jobs(jobs: List[CreateJobRequest]):
    """Create multiple jobs in a batch."""
    created = []
    duplicates = []
    
    for request in jobs:
        job = ExtractionJob(
            game=request.game,
            source=request.source,
            job_type=request.job_type,
            priority=request.priority,
            epoch=request.epoch,
            region=request.region,
            date_start=request.date_start,
            date_end=request.date_end,
            dependencies=request.dependencies,
            metadata=request.metadata
        )
        
        # Check for duplicates
        if coordinator_state.conflict_resolver:
            duplicate = await coordinator_state.conflict_resolver.check_duplicate_job(job)
            if duplicate:
                duplicates.append({"job": job.id, "duplicate_of": duplicate})
                continue
        
        await coordinator_state.queue_manager.enqueue(job)
        created.append(job.id)
    
    return {
        "created": len(created),
        "duplicates": len(duplicates),
        "job_ids": created,
        "duplicate_details": duplicates
    }


@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """Get job details by ID."""
    job = await coordinator_state.queue_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job


@app.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a pending job."""
    cancelled = await coordinator_state.queue_manager.cancel_job(job_id)
    
    if not cancelled:
        raise HTTPException(status_code=400, detail="Job not found or cannot be cancelled")
    
    return {"status": "cancelled", "job_id": job_id}


# -----------------------------------------------------------------------------
# Agent Management Endpoints
# -----------------------------------------------------------------------------

@app.post("/agents/register")
async def register_agent(request: RegisterAgentRequest):
    """Register a new extraction agent."""
    agent = await coordinator_state.agent_manager.register_agent(
        agent_id=request.agent_id,
        game_specialization=request.game_specialization,
        source_capabilities=request.source_capabilities
    )
    
    return {
        "agent_id": agent.id,
        "status": "registered",
        "game_specialization": [g.value for g in agent.game_specialization],
        "source_capabilities": agent.source_capabilities
    }


@app.post("/agents/{agent_id}/heartbeat", response_model=HeartbeatResponse)
async def agent_heartbeat(agent_id: str, background_tasks: BackgroundTasks):
    """
    Agent heartbeat - updates last seen and may return a new job assignment.
    
    Agents should call this endpoint regularly (every 10-30 seconds).
    """
    # Check if agent exists, create if not (for auto-registration)
    agent = await coordinator_state.agent_manager.get_agent(agent_id)
    
    if not agent:
        # Auto-register with default capabilities
        agent = await coordinator_state.agent_manager.register_agent(
            agent_id=agent_id,
            game_specialization=[GameType.COUNTER_STRIKE, GameType.VALORANT],
            source_capabilities=["hltv", "vlr", "liquipedia"]
        )
    
    # Process heartbeat and potentially assign job
    job = await coordinator_state.agent_manager.heartbeat(agent_id)
    
    if job:
        return HeartbeatResponse(
            agent_id=agent_id,
            status=agent.status,
            assigned_job=job,
            message=f"New job assigned: {job.id}"
        )
    
    return HeartbeatResponse(
        agent_id=agent_id,
        status=agent.status,
        assigned_job=None,
        message="No work available"
    )


@app.post("/agents/{agent_id}/jobs/{job_id}/complete")
async def complete_job(agent_id: str, job_id: str, request: JobCompleteRequest):
    """Report job completion."""
    result = JobResult(
        job_id=job_id,
        success=request.success,
        data=request.data,
        error=request.error,
        records_extracted=request.records_extracted,
        checksum=request.checksum,
        metadata=request.metadata
    )
    
    handled = await coordinator_state.distributor.handle_job_completion(
        agent_id, job_id, result
    )
    
    if not handled:
        raise HTTPException(status_code=400, detail="Failed to process completion")
    
    # Record metrics
    await coordinator_state.metrics.record_job_completed(
        result.job_id, 0, {"agent": agent_id}
    )
    
    return {
        "status": "recorded",
        "agent_id": agent_id,
        "job_id": job_id,
        "success": request.success
    }


@app.get("/agents")
async def list_agents(
    status: Optional[str] = None,
    game: Optional[GameType] = None
):
    """List all registered agents."""
    agents = await coordinator_state.agent_manager.list_agents(status=status, game=game)
    return {
        "count": len(agents),
        "agents": agents
    }


@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get agent details."""
    agent = await coordinator_state.agent_manager.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent


@app.delete("/agents/{agent_id}")
async def unregister_agent(agent_id: str):
    """Unregister an agent."""
    success = await coordinator_state.agent_manager.unregister_agent(agent_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {"status": "unregistered", "agent_id": agent_id}


# -----------------------------------------------------------------------------
# Queue Management Endpoints
# -----------------------------------------------------------------------------

@app.get("/queue/stats")
async def get_queue_stats():
    """Get queue statistics."""
    return coordinator_state.queue_manager.get_queue_stats()


@app.post("/queue/rebalance")
async def rebalance_queue():
    """Trigger queue rebalancing."""
    stats = await coordinator_state.distributor.rebalance_load()
    return {"rebalanced": True, "stats": stats}


# -----------------------------------------------------------------------------
# Rate Limiting Endpoints
# -----------------------------------------------------------------------------

@app.get("/rate-limits/{source}", response_model=RateLimitStatusResponse)
async def get_rate_limit_status(source: str):
    """Get rate limit status for a source."""
    status = await coordinator_state.rate_limiter.get_status(source)
    return status


@app.get("/rate-limits")
async def get_all_rate_limits():
    """Get rate limit status for all sources."""
    return await coordinator_state.rate_limiter.get_all_statuses()


@app.post("/rate-limits/{source}/reset")
async def reset_rate_limit(source: str):
    """Reset rate limit for a source."""
    await coordinator_state.rate_limiter.reset_source(source)
    return {"status": "reset", "source": source}


# -----------------------------------------------------------------------------
# Monitoring Endpoints
# -----------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Get comprehensive health status."""
    health = await coordinator_state.health_checker.get_health_summary()
    return health


@app.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe."""
    health = await coordinator_state.health_checker.get_health_summary()
    
    if health["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health)
    
    return {"status": "ready"}


@app.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe."""
    return {"status": "alive"}


@app.get("/metrics")
async def get_metrics():
    """Get coordinator metrics."""
    return await coordinator_state.metrics.get_all_metrics()


@app.get("/metrics/prometheus", response_class=PlainTextResponse)
async def get_prometheus_metrics():
    """Get metrics in Prometheus format."""
    return coordinator_state.metrics.export_prometheus()


@app.get("/status", response_model=CoordinatorStatusResponse)
async def get_status():
    """Get overall coordinator status."""
    queue_stats = coordinator_state.queue_manager.get_queue_stats()
    agent_stats = coordinator_state.agent_manager.get_agent_stats()
    metrics = await coordinator_state.metrics.get_all_metrics()
    
    health = await coordinator_state.health_checker.get_health_summary()
    
    return CoordinatorStatusResponse(
        status=health["status"],
        queues=queue_stats,
        agents=agent_stats,
        metrics=metrics,
        timestamp=datetime.utcnow().isoformat()
    )


# -----------------------------------------------------------------------------
# Administrative Endpoints
# -----------------------------------------------------------------------------

@app.post("/admin/purge")
async def purge_old_jobs(max_age_hours: int = 24):
    """Purge old completed jobs from memory."""
    purged = await coordinator_state.queue_manager.purge_completed(max_age_hours)
    return {"purged": purged}


@app.get("/admin/distributor/stats")
async def get_distributor_stats():
    """Get distributor statistics."""
    return coordinator_state.distributor.get_stats()


@app.get("/admin/distributor/insights")
async def get_distributor_insights():
    """Get distributor performance insights."""
    if hasattr(coordinator_state.distributor, 'get_performance_insights'):
        return coordinator_state.distributor.get_performance_insights()
    return {"error": "Distributor does not support insights"}


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__:":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    uvicorn.run(app, host=host, port=port)
