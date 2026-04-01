"""
Central Job Coordinator for dual-game esports data collection.

This package provides production-ready coordination for extraction jobs
across Counter-Strike and Valorant data sources.
"""

from .models import (
    GameType,
    JobStatus,
    ExtractionJob,
    Agent,
    JobBatch,
)

from .queue_manager import QueueManager
from .agent_manager import AgentManager
from .conflict_resolver import ConflictResolver
from .rate_limiter import RateLimiter, RateLimitConfig
from .distributor import JobDistributor
from .monitoring import CoordinatorMetrics, HealthChecker

__version__ = "1.0.0"
__all__ = [
    # Enums
    "GameType",
    "JobStatus",
    # Models
    "ExtractionJob",
    "Agent",
    "JobBatch",
    # Managers
    "QueueManager",
    "AgentManager",
    "ConflictResolver",
    "RateLimiter",
    "RateLimitConfig",
    "JobDistributor",
    # Monitoring
    "CoordinatorMetrics",
    "HealthChecker",
]
