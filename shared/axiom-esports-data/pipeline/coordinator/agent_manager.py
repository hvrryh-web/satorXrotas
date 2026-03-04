"""
Agent lifecycle and assignment management.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set

from .models import Agent, ExtractionJob, GameType, JobStatus, JobResult

logger = logging.getLogger(__name__)


class AgentManager:
    """
    Manages extraction agents:
    - Registration and heartbeat
    - Job assignment
    - Health monitoring
    - Load balancing
    - Agent statistics tracking
    """
    
    HEARTBEAT_TIMEOUT = timedelta(minutes=2)
    HEARTBEAT_INTERVAL = timedelta(seconds=30)
    
    def __init__(self, db_pool=None, queue_manager=None):
        self.db_pool = db_pool
        self.queue_manager = queue_manager
        self.agents: Dict[str, Agent] = {}
        self._lock = asyncio.Lock()
        self._monitor_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        # Track job assignments for recovery
        self._job_assignments: Dict[str, str] = {}  # job_id -> agent_id
    
    async def start(self) -> None:
        """Start agent monitoring."""
        if self._monitor_task is None:
            self._shutdown_event.clear()
            self._monitor_task = asyncio.create_task(self._monitor_agents())
            logger.info("Agent manager started")
    
    async def stop(self) -> None:
        """Stop agent monitoring."""
        self._shutdown_event.set()
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
            logger.info("Agent manager stopped")
    
    async def register_agent(
        self,
        agent_id: str,
        game_specialization: List[GameType],
        source_capabilities: List[str]
    ) -> Agent:
        """
        Register new extraction agent.
        
        Args:
            agent_id: Unique agent identifier
            game_specialization: List of games this agent can handle
            source_capabilities: List of sources this agent can extract from
            
        Returns:
            The registered agent
        """
        agent = Agent(
            id=agent_id,
            game_specialization=game_specialization,
            source_capabilities=[s.lower() for s in source_capabilities],
            status="idle"
        )
        
        async with self._lock:
            # Check if agent already exists
            if agent_id in self.agents:
                logger.warning(f"Agent {agent_id} re-registering")
                old_agent = self.agents[agent_id]
                # Preserve stats if re-registering
                agent.total_jobs_completed = old_agent.total_jobs_completed
                agent.total_jobs_failed = old_agent.total_jobs_failed
            
            self.agents[agent_id] = agent
        
        await self._persist_agent(agent)
        logger.info(
            f"Agent registered: {agent_id} "
            f"(games: {[g.value for g in game_specialization]}, "
            f"sources: {source_capabilities})"
        )
        return agent
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent.
        
        Args:
            agent_id: ID of agent to unregister
            
        Returns:
            True if agent was unregistered
        """
        async with self._lock:
            if agent_id not in self.agents:
                return False
            
            agent = self.agents[agent_id]
            
            # Reassign any in-progress job
            if agent.current_job_id:
                await self._reassign_job(agent.current_job_id)
                if agent.current_job_id in self._job_assignments:
                    del self._job_assignments[agent.current_job_id]
            
            del self.agents[agent_id]
            logger.info(f"Agent {agent_id} unregistered")
            return True
    
    async def heartbeat(self, agent_id: str) -> Optional[ExtractionJob]:
        """
        Update agent heartbeat and potentially assign new job.
        
        Args:
            agent_id: ID of agent sending heartbeat
            
        Returns:
            New job assignment if available
        """
        async with self._lock:
            if agent_id not in self.agents:
                logger.warning(f"Heartbeat from unknown agent: {agent_id}")
                return None
            
            agent = self.agents[agent_id]
            agent.last_heartbeat = datetime.utcnow()
            
            # If agent was offline, mark as idle
            if agent.status == "offline":
                agent.status = "idle"
                agent.current_job_id = None
                logger.info(f"Agent {agent_id} came back online")
            
            # If agent is idle and we have a queue manager, try to assign job
            if agent.status == "idle" and self.queue_manager:
                # Release lock before calling queue_manager to avoid deadlock
                pass  # We'll do this outside the lock
        
        # Try to get job outside the lock
        if agent.status == "idle" and self.queue_manager:
            job = await self.queue_manager.dequeue(agent)
            if job:
                async with self._lock:
                    agent.status = "busy"
                    agent.current_job_id = job.id
                    self._job_assignments[job.id] = agent_id
                
                logger.info(f"Assigned job {job.id} to agent {agent_id}")
                return job
        
        return None
    
    async def report_job_complete(
        self,
        agent_id: str,
        job_id: str,
        success: bool,
        result: Optional[JobResult] = None
    ) -> bool:
        """
        Agent reports job completion.
        
        Args:
            agent_id: ID of agent completing the job
            job_id: ID of completed job
            success: Whether job succeeded
            result: Optional job result details
            
        Returns:
            True if report was processed
        """
        async with self._lock:
            agent = self.agents.get(agent_id)
            if not agent:
                logger.warning(f"Job completion report from unknown agent: {agent_id}")
                return False
            
            # Verify agent owns this job
            if agent.current_job_id != job_id:
                logger.warning(
                    f"Agent {agent_id} reported completion for job {job_id} "
                    f"but owns {agent.current_job_id}"
                )
                return False
            
            # Update agent stats
            agent.status = "idle"
            agent.current_job_id = None
            
            if success:
                agent.total_jobs_completed += 1
                logger.info(f"Agent {agent_id} completed job {job_id}")
            else:
                agent.total_jobs_failed += 1
                error = result.error if result else "Unknown error"
                logger.warning(f"Agent {agent_id} failed job {job_id}: {error}")
            
            # Remove from assignments
            if job_id in self._job_assignments:
                del self._job_assignments[job_id]
        
        # Update queue manager outside lock
        if self.queue_manager:
            if success:
                await self.queue_manager.mark_completed(job_id)
            else:
                await self.queue_manager.mark_failed(
                    job_id, 
                    result.error if result else "Unknown error"
                )
        
        # Persist result if db_pool available
        if result:
            await self._persist_job_result(job_id, result)
        
        return True
    
    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID."""
        return self.agents.get(agent_id)
    
    async def list_agents(
        self,
        status: Optional[str] = None,
        game: Optional[GameType] = None
    ) -> List[Agent]:
        """
        List agents with optional filtering.
        
        Args:
            status: Filter by status (idle, busy, offline)
            game: Filter by game specialization
            
        Returns:
            List of matching agents
        """
        agents = list(self.agents.values())
        
        if status:
            agents = [a for a in agents if a.status == status]
        
        if game:
            agents = [a for a in agents if game in a.game_specialization]
        
        return agents
    
    async def _monitor_agents(self):
        """Background task to monitor agent health."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=self.HEARTBEAT_INTERVAL.total_seconds()
                )
            except asyncio.TimeoutError:
                # Time to check agents
                pass
            
            if self._shutdown_event.is_set():
                break
            
            await self._check_agent_health()
    
    async def _check_agent_health(self):
        """Check for stale agents and handle timeouts."""
        async with self._lock:
            now = datetime.utcnow()
            stale_agents: List[str] = []
            
            for agent_id, agent in self.agents.items():
                if agent.status == "offline":
                    continue  # Already marked offline
                
                time_since_heartbeat = now - agent.last_heartbeat
                if time_since_heartbeat > self.HEARTBEAT_TIMEOUT:
                    stale_agents.append(agent_id)
            
            for agent_id in stale_agents:
                agent = self.agents[agent_id]
                logger.warning(
                    f"Agent {agent_id} timed out "
                    f"(last heartbeat: {agent.last_heartbeat.isoformat()})"
                )
                
                # Reassign any in-progress job
                if agent.current_job_id:
                    asyncio.create_task(self._reassign_job(agent.current_job_id))
                
                agent.status = "offline"
    
    async def _reassign_job(self, job_id: str) -> bool:
        """
        Reassign job from failed/timed out agent.
        
        Args:
            job_id: ID of job to reassign
            
        Returns:
            True if job was reassigned or marked failed
        """
        if not self.queue_manager:
            return False
        
        job = await self.queue_manager.get_job(job_id)
        if not job:
            return False
        
        if job.can_retry():
            success = await self.queue_manager.requeue_job(job_id)
            if success:
                logger.info(f"Reassigned job {job_id} (retry {job.retry_count}/{job.max_retries})")
                # Remove old assignment
                if job_id in self._job_assignments:
                    del self._job_assignments[job_id]
            return success
        else:
            # Max retries exceeded
            await self.queue_manager.mark_failed(job_id, "Max retries exceeded")
            logger.error(f"Job {job_id} failed permanently after {job.max_retries} retries")
            return True
    
    async def _persist_agent(self, agent: Agent) -> None:
        """Persist agent to database if db_pool is available."""
        if not self.db_pool:
            return
        
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO agents (id, game_specialization, source_capabilities, status, 
                                      last_heartbeat, total_jobs_completed, total_jobs_failed)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (id) DO UPDATE SET
                        game_specialization = $2,
                        source_capabilities = $3,
                        status = $4,
                        last_heartbeat = $5,
                        total_jobs_completed = $6,
                        total_jobs_failed = $7,
                        updated_at = now()
                    """,
                    agent.id,
                    [g.value for g in agent.game_specialization],
                    agent.source_capabilities,
                    agent.status,
                    agent.last_heartbeat,
                    agent.total_jobs_completed,
                    agent.total_jobs_failed
                )
        except Exception as e:
            logger.error(f"Failed to persist agent {agent.id}: {e}")
    
    async def _persist_job_result(self, job_id: str, result: JobResult) -> None:
        """Persist job result to database if db_pool is available."""
        if not self.db_pool:
            return
        
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO job_results (job_id, success, error, records_extracted, 
                                           checksum, metadata, completed_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (job_id) DO UPDATE SET
                        success = $2,
                        error = $3,
                        records_extracted = $4,
                        checksum = $5,
                        metadata = $6,
                        completed_at = $7
                    """,
                    job_id,
                    result.success,
                    result.error,
                    result.records_extracted,
                    result.checksum,
                    result.metadata,
                    result.completed_at
                )
        except Exception as e:
            logger.error(f"Failed to persist job result for {job_id}: {e}")
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get statistics for all agents."""
        total = len(self.agents)
        idle = sum(1 for a in self.agents.values() if a.status == "idle")
        busy = sum(1 for a in self.agents.values() if a.status == "busy")
        offline = sum(1 for a in self.agents.values() if a.status == "offline")
        
        by_game: Dict[str, int] = {}
        for agent in self.agents.values():
            for game in agent.game_specialization:
                game_val = game.value if isinstance(game, GameType) else str(game)
                by_game[game_val] = by_game.get(game_val, 0) + 1
        
        by_source: Dict[str, int] = {}
        for agent in self.agents.values():
            for source in agent.source_capabilities:
                by_source[source] = by_source.get(source, 0) + 1
        
        total_completed = sum(a.total_jobs_completed for a in self.agents.values())
        total_failed = sum(a.total_jobs_failed for a in self.agents.values())
        
        return {
            "total": total,
            "idle": idle,
            "busy": busy,
            "offline": offline,
            "by_game": by_game,
            "by_source": by_source,
            "total_jobs_completed": total_completed,
            "total_jobs_failed": total_failed,
            "success_rate": (
                total_completed / (total_completed + total_failed) * 100
                if (total_completed + total_failed) > 0 else 0
            )
        }
    
    async def get_job_assignment(self, job_id: str) -> Optional[str]:
        """Get the agent ID assigned to a job."""
        return self._job_assignments.get(job_id)
