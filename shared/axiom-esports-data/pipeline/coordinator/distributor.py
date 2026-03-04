"""
Job distribution logic for the esports data pipeline.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass

from .models import (
    ExtractionJob, Agent, GameType, JobStatus, JobBatch, JobResult
)
from .queue_manager import QueueManager
from .agent_manager import AgentManager
from .rate_limiter import RateLimiter
from .conflict_resolver import ConflictResolver

logger = logging.getLogger(__name__)


@dataclass
class DistributionStrategy:
    """Configuration for job distribution strategy."""
    batch_size: int = 10
    fairness_window: int = 100  # Jobs to consider for fairness
    priority_boost_threshold: int = 5  # Queue size to trigger priority boost
    cross_train_agents: bool = True  # Allow agents to handle multiple games


class JobDistributor:
    """
    Orchestrates job distribution across agents.
    
    Responsible for:
    - Balancing load across agents
    - Batching jobs efficiently
    - Handling agent failures
    - Optimizing throughput
    """
    
    def __init__(
        self,
        queue_manager: QueueManager,
        agent_manager: AgentManager,
        rate_limiter: Optional[RateLimiter] = None,
        conflict_resolver: Optional[ConflictResolver] = None,
        strategy: Optional[DistributionStrategy] = None
    ):
        self.queue_manager = queue_manager
        self.agent_manager = agent_manager
        self.rate_limiter = rate_limiter
        self.conflict_resolver = conflict_resolver
        self.strategy = strategy or DistributionStrategy()
        
        self._distribution_callbacks: List[Callable] = []
        self._batch_callbacks: List[Callable] = []
        self._stats: Dict[str, Any] = {
            "jobs_distributed": 0,
            "jobs_batched": 0,
            "distribution_failures": 0,
            "last_distribution": None
        }
    
    async def distribute_single(self, agent_id: str) -> Optional[ExtractionJob]:
        """
        Distribute a single job to an agent.
        
        Args:
            agent_id: ID of agent to assign work to
            
        Returns:
            Assigned job or None if no work available
        """
        agent = await self.agent_manager.get_agent(agent_id)
        if not agent:
            logger.warning(f"Distribute called for unknown agent: {agent_id}")
            return None
        
        if not agent.is_available():
            logger.debug(f"Agent {agent_id} is not available")
            return None
        
        # Get job from queue
        job = await self.queue_manager.dequeue(agent)
        
        if job:
            self._stats["jobs_distributed"] += 1
            self._stats["last_distribution"] = datetime.utcnow().isoformat()
            
            # Trigger callbacks
            for callback in self._distribution_callbacks:
                try:
                    await callback(agent, job)
                except Exception as e:
                    logger.error(f"Distribution callback error: {e}")
            
            logger.info(f"Distributed job {job.id} to agent {agent_id}")
        
        return job
    
    async def distribute_batch(
        self,
        agent_id: str,
        max_size: Optional[int] = None
    ) -> JobBatch:
        """
        Distribute a batch of jobs to an agent.
        
        Args:
            agent_id: ID of agent to assign work to
            max_size: Maximum batch size (defaults to strategy.batch_size)
            
        Returns:
            JobBatch containing assigned jobs
        """
        max_size = max_size or self.strategy.batch_size
        agent = await self.agent_manager.get_agent(agent_id)
        
        if not agent or not agent.is_available():
            return JobBatch(game=GameType.COUNTER_STRIKE)  # Empty batch
        
        # Determine primary game for this batch (first specialization)
        primary_game = agent.game_specialization[0] if agent.game_specialization else GameType.COUNTER_STRIKE
        batch = JobBatch(game=primary_game)
        batch.assigned_agent = agent_id
        
        # Collect jobs up to batch size
        for _ in range(max_size):
            job = await self.queue_manager.dequeue(agent)
            if not job:
                break
            
            batch.add_job(job)
            self._stats["jobs_distributed"] += 1
        
        if batch.size() > 0:
            self._stats["jobs_batched"] += batch.size()
            self._stats["last_distribution"] = datetime.utcnow().isoformat()
            
            # Trigger callbacks
            for callback in self._batch_callbacks:
                try:
                    await callback(agent, batch)
                except Exception as e:
                    logger.error(f"Batch callback error: {e}")
            
            logger.info(f"Distributed batch of {batch.size()} jobs to agent {agent_id}")
        
        return batch
    
    async def distribute_to_all(self) -> Dict[str, Optional[ExtractionJob]]:
        """
        Distribute jobs to all available agents.
        
        Returns:
            Dict mapping agent_id to assigned job (or None)
        """
        assignments: Dict[str, Optional[ExtractionJob]] = {}
        
        # Get all idle agents
        idle_agents = await self.agent_manager.list_agents(status="idle")
        
        if not idle_agents:
            return assignments
        
        # Sort agents by specialization for fairness
        agent_list = list(idle_agents)
        agent_list.sort(key=lambda a: a.total_jobs_completed)
        
        # Try to assign to each agent
        for agent in agent_list:
            job = await self.distribute_single(agent.id)
            assignments[agent.id] = job
        
        return assignments
    
    async def handle_job_completion(
        self,
        agent_id: str,
        job_id: str,
        result: JobResult
    ) -> bool:
        """
        Handle job completion from an agent.
        
        Args:
            agent_id: ID of completing agent
            job_id: ID of completed job
            result: Job result
            
        Returns:
            True if handled successfully
        """
        success = await self.agent_manager.report_job_complete(
            agent_id,
            job_id,
            result.success,
            result
        )
        
        if not success:
            self._stats["distribution_failures"] += 1
            return False
        
        # Try to assign more work immediately
        asyncio.create_task(self._assign_follow_up(agent_id))
        
        return True
    
    async def _assign_follow_up(self, agent_id: str) -> None:
        """Assign follow-up work to an agent after completion."""
        await asyncio.sleep(0.1)  # Brief pause to allow agent to report ready
        
        agent = await self.agent_manager.get_agent(agent_id)
        if agent and agent.is_available():
            job = await self.distribute_single(agent_id)
            if job:
                logger.debug(f"Follow-up job {job.id} assigned to agent {agent_id}")
    
    async def rebalance_load(self) -> Dict[str, int]:
        """
        Rebalance jobs across agents if load is uneven.
        
        Returns:
            Dict with rebalance statistics
        """
        stats = {"moved": 0, "failed": 0}
        
        # Get queue stats
        queue_stats = self.queue_manager.get_queue_stats()
        
        # Check if any game has excessive backlog
        for game_str, game_stats in [("cs", queue_stats["cs"]), ("valorant", queue_stats["valorant"])]:
            if game_stats["pending"] > self.strategy.priority_boost_threshold * 10:
                logger.warning(f"{game_str} queue has {game_stats['pending']} pending jobs, triggering rebalance")
                
                # Try to find agents from other games that could help
                if self.strategy.cross_train_agents:
                    other_game = GameType.VALORANT if game_str == "cs" else GameType.COUNTER_STRIKE
                    cross_trained = await self.agent_manager.list_agents(game=other_game)
                    
                    for agent in cross_trained:
                        if agent.status == "idle":
                            # Temporarily add this game to their specialization
                            game = GameType.COUNTER_STRIKE if game_str == "cs" else GameType.VALORANT
                            if game not in agent.game_specialization:
                                agent.game_specialization.append(game)
                                
                                job = await self.queue_manager.dequeue(agent)
                                if job:
                                    stats["moved"] += 1
                                    logger.info(f"Cross-game assignment: {agent.id} took {game_str} job")
                                else:
                                    # Remove the temporary specialization
                                    agent.game_specialization.remove(game)
        
        return stats
    
    async def optimize_batch_sizes(self) -> None:
        """Dynamically adjust batch sizes based on throughput."""
        # This is a placeholder for dynamic batch size optimization
        # In production, this would analyze historical throughput data
        pass
    
    def on_distribute(self, callback: Callable) -> None:
        """Register a callback for job distribution events."""
        self._distribution_callbacks.append(callback)
    
    def on_batch(self, callback: Callable) -> None:
        """Register a callback for batch distribution events."""
        self._batch_callbacks.append(callback)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get distributor statistics."""
        return dict(self._stats)
    
    async def get_health(self) -> Dict[str, Any]:
        """Get distributor health status."""
        queue_stats = self.queue_manager.get_queue_stats()
        agent_stats = self.agent_manager.get_agent_stats()
        
        total_pending = queue_stats["cs"]["pending"] + queue_stats["valorant"]["pending"]
        idle_agents = agent_stats.get("idle", 0)
        
        # Calculate health score
        health_score = 100
        
        if total_pending > 100 and idle_agents == 0:
            health_score -= 30  # High backlog with no idle agents
        
        if self._stats["distribution_failures"] > 10:
            health_score -= 20  # Recent failures
        
        # Check for stale distributions
        if self._stats["last_distribution"]:
            last_dist = datetime.fromisoformat(self._stats["last_distribution"])
            if datetime.utcnow() - last_dist > timedelta(minutes=5):
                health_score -= 20  # No recent distributions
        
        status = "healthy" if health_score >= 80 else "degraded" if health_score >= 50 else "unhealthy"
        
        return {
            "status": status,
            "score": max(0, health_score),
            "pending_jobs": total_pending,
            "idle_agents": idle_agents,
            "recent_distributions": self._stats["jobs_distributed"],
            "recent_failures": self._stats["distribution_failures"]
        }


class SmartDistributor(JobDistributor):
    """
    Intelligent job distributor with ML-inspired optimizations.
    
    Learns from historical patterns to optimize:
    - Agent-task matching
    - Batch composition
    - Timing of distributions
    """
    
    def __init__(
        self,
        queue_manager: QueueManager,
        agent_manager: AgentManager,
        rate_limiter: Optional[RateLimiter] = None,
        conflict_resolver: Optional[ConflictResolver] = None,
        strategy: Optional[DistributionStrategy] = None
    ):
        super().__init__(queue_manager, agent_manager, rate_limiter, conflict_resolver, strategy)
        
        # Performance tracking per (agent, source) pair
        self._agent_source_performance: Dict[str, Dict[str, float]] = {}
        
        # Job type affinity
        self._agent_job_type_affinity: Dict[str, Dict[str, float]] = {}
        
        # Time-based patterns
        self._hourly_patterns: Dict[int, Dict[str, int]] = {}
    
    async def distribute_single(self, agent_id: str) -> Optional[ExtractionJob]:
        """Distribute with performance-based optimization."""
        # Get agent performance history
        agent_perf = self._agent_source_performance.get(agent_id, {})
        
        # Try to match agent to their best performing sources first
        if agent_perf:
            best_sources = sorted(agent_perf.items(), key=lambda x: x[1], reverse=True)
            
            # Get agent and try best sources first
            agent = await self.agent_manager.get_agent(agent_id)
            if agent:
                for source, _ in best_sources:
                    if source in agent.source_capabilities:
                        # Look for jobs from this source
                        # This would need queue_manager to support source filtering
                        pass
        
        # Fall back to standard distribution
        job = await super().distribute_single(agent_id)
        
        if job:
            # Record assignment for learning
            key = f"{agent_id}:{job.source}"
            if key not in self._agent_source_performance:
                self._agent_source_performance[key] = {}
        
        return job
    
    async def record_performance(
        self,
        agent_id: str,
        source: str,
        job_type: str,
        success: bool,
        duration_ms: float
    ) -> None:
        """
        Record performance for learning.
        
        Args:
            agent_id: Agent that processed the job
            source: Data source
            job_type: Type of job
            success: Whether job succeeded
            duration_ms: Processing time in milliseconds
        """
        # Update source performance
        if agent_id not in self._agent_source_performance:
            self._agent_source_performance[agent_id] = {}
        
        current = self._agent_source_performance[agent_id].get(source, 0.5)
        
        # Simple exponential moving average of success rate
        success_value = 1.0 if success else 0.0
        new_score = current * 0.8 + success_value * 0.2
        self._agent_source_performance[agent_id][source] = new_score
        
        # Update job type affinity
        if agent_id not in self._agent_job_type_affinity:
            self._agent_job_type_affinity[agent_id] = {}
        
        current_type = self._agent_job_type_affinity[agent_id].get(job_type, 0.5)
        new_type_score = current_type * 0.8 + (1.0 if success else 0.0) * 0.2
        self._agent_job_type_affinity[agent_id][job_type] = new_type_score
        
        # Update hourly patterns
        hour = datetime.utcnow().hour
        if hour not in self._hourly_patterns:
            self._hourly_patterns[hour] = {"success": 0, "failure": 0}
        
        if success:
            self._hourly_patterns[hour]["success"] += 1
        else:
            self._hourly_patterns[hour]["failure"] += 1
    
    def get_performance_insights(self) -> Dict[str, Any]:
        """Get insights from learned patterns."""
        insights = {
            "top_agent_source_pairs": [],
            "best_job_type_matches": [],
            "optimal_hours": []
        }
        
        # Top performing agent-source pairs
        all_pairs = []
        for agent_id, sources in self._agent_source_performance.items():
            for source, score in sources.items():
                all_pairs.append((agent_id, source, score))
        
        all_pairs.sort(key=lambda x: x[2], reverse=True)
        insights["top_agent_source_pairs"] = [
            {"agent": a, "source": s, "score": round(sc, 3)}
            for a, s, sc in all_pairs[:10]
        ]
        
        # Best job type matches
        type_matches = []
        for agent_id, types in self._agent_job_type_affinity.items():
            for job_type, score in types.items():
                type_matches.append((agent_id, job_type, score))
        
        type_matches.sort(key=lambda x: x[2], reverse=True)
        insights["best_job_type_matches"] = [
            {"agent": a, "job_type": jt, "score": round(sc, 3)}
            for a, jt, sc in type_matches[:10]
        ]
        
        # Optimal hours
        hour_success_rates = []
        for hour, counts in self._hourly_patterns.items():
            total = counts["success"] + counts["failure"]
            if total > 0:
                rate = counts["success"] / total
                hour_success_rates.append((hour, rate, total))
        
        hour_success_rates.sort(key=lambda x: x[1], reverse=True)
        insights["optimal_hours"] = [
            {"hour": h, "success_rate": round(sr, 3), "sample_size": n}
            for h, sr, n in hour_success_rates[:5]
        ]
        
        return insights
