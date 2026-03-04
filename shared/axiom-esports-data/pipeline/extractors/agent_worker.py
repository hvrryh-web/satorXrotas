import asyncio
import aiohttp
from typing import Optional, Dict, Type
import logging

from .base import BaseExtractor, ExtractionResult

logger = logging.getLogger(__name__)


class ExtractionAgentWorker:
    """
    Worker process that:
    1. Registers with coordinator
    2. Heartbeats periodically
    3. Receives and processes jobs
    4. Reports results
    """
    
    def __init__(
        self,
        agent_id: str,
        game_specialization: list,
        source_capabilities: list,
        coordinator_url: str,
        db_pool
    ):
        self.agent_id = agent_id
        self.game_specialization = game_specialization
        self.source_capabilities = source_capabilities
        self.coordinator_url = coordinator_url
        self.db_pool = db_pool
        self.session: Optional[aiohttp.ClientSession] = None
        self.running = False
        self.current_job = None
        self.extractors: Dict[str, BaseExtractor] = {}
    
    async def start(self):
        """Start the worker."""
        self.running = True
        self.session = aiohttp.ClientSession()
        
        # Register with coordinator
        await self._register()
        
        # Start heartbeat loop
        await self._run_heartbeat_loop()
    
    async def stop(self):
        """Stop the worker gracefully."""
        self.running = False
        if self.session:
            await self.session.close()
    
    async def _register(self):
        """Register agent with coordinator."""
        async with self.session.post(
            f"{self.coordinator_url}/agents/register",
            json={
                'id': self.agent_id,
                'game_specialization': self.game_specialization,
                'source_capabilities': self.source_capabilities
            }
        ) as response:
            if response.status != 200:
                raise Exception(f"Failed to register: {response.status}")
            logger.info(f"Agent {self.agent_id} registered")
    
    async def _run_heartbeat_loop(self):
        """Main loop - heartbeat and job processing."""
        while self.running:
            try:
                # Send heartbeat, may receive job
                job = await self._heartbeat()
                
                if job:
                    await self._process_job(job)
                else:
                    # No job, wait before next heartbeat
                    await asyncio.sleep(10)
                    
            except Exception as e:
                logger.exception("Heartbeat loop error")
                await asyncio.sleep(30)  # Wait longer on error
    
    async def _heartbeat(self) -> Optional[dict]:
        """Send heartbeat to coordinator."""
        async with self.session.post(
            f"{self.coordinator_url}/agents/{self.agent_id}/heartbeat"
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('job')
            return None
    
    async def _process_job(self, job: dict):
        """Process assigned job."""
        job_id = job['id']
        game = job['game']
        source = job['source']
        
        logger.info(f"Processing job {job_id}: {game}/{source}/{job['job_type']}")
        
        try:
            # Get or create extractor
            extractor = await self._get_extractor(game, source)
            
            # Run extraction
            async with extractor:
                result = await extractor.run_job(job)
            
            # Report result
            await self._report_completion(job_id, result)
            
        except Exception as e:
            logger.exception(f"Job {job_id} failed")
            await self._report_completion(
                job_id,
                ExtractionResult(
                    job_id=job_id,
                    success=False,
                    records_extracted=0,
                    records_failed=1,
                    error_message=str(e)
                )
            )
    
    async def _get_extractor(self, game: str, source: str) -> BaseExtractor:
        """Get or create extractor for game/source."""
        key = f"{game}:{source}"
        
        if key not in self.extractors:
            # Lazy import to avoid circular dependencies
            rate_limiter = await self._create_rate_limiter()
            
            if game == 'cs' and source == 'hltv':
                from .cs.extractor import CSExtractor
                self.extractors[key] = CSExtractor(
                    rate_limiter=rate_limiter,
                    db_pool=self.db_pool,
                    coordinator_url=self.coordinator_url
                )
            elif game == 'valorant' and source == 'vlr':
                from .valorant.extractor import ValorantExtractor
                self.extractors[key] = ValorantExtractor(
                    rate_limiter=rate_limiter,
                    db_pool=self.db_pool,
                    coordinator_url=self.coordinator_url
                )
            else:
                raise ValueError(f"No extractor for {game}/{source}")
        
        return self.extractors[key]
    
    async def _create_rate_limiter(self):
        """Create a rate limiter instance."""
        # Import here to avoid circular imports
        try:
            from ..coordinator.rate_limiter import RateLimiter
            return RateLimiter(self.db_pool)
        except ImportError:
            # Fallback simple rate limiter
            logger.warning("Using fallback rate limiter")
            return _SimpleRateLimiter()
    
    async def _report_completion(self, job_id: str, result: ExtractionResult):
        """Report job completion to coordinator."""
        async with self.session.post(
            f"{self.coordinator_url}/agents/{self.agent_id}/jobs/{job_id}/complete",
            json={
                'success': result.success,
                'records_extracted': result.records_extracted,
                'records_failed': result.records_failed,
                'error_message': result.error_message,
                'metadata': result.metadata
            }
        ) as response:
            if response.status != 200:
                logger.error(f"Failed to report completion: {response.status}")


class _SimpleRateLimiter:
    """Simple in-memory rate limiter fallback."""
    
    def __init__(self):
        self._last_request: Dict[str, float] = {}
        self._min_interval = 2.0  # seconds
    
    async def acquire(self, source: str) -> bool:
        """Acquire rate limit token."""
        import time
        now = time.time()
        last = self._last_request.get(source, 0)
        
        if now - last < self._min_interval:
            await asyncio.sleep(self._min_interval - (now - last))
        
        self._last_request[source] = time.time()
        return True


async def create_and_start_worker(
    agent_id: str,
    game_specialization: list,
    source_capabilities: list,
    coordinator_url: str,
    db_pool
) -> ExtractionAgentWorker:
    """
    Create and start an extraction agent worker.
    
    Args:
        agent_id: Unique identifier for this worker
        game_specialization: List of games this worker can handle
        source_capabilities: List of sources this worker can extract from
        coordinator_url: URL of the job coordinator
        db_pool: Database connection pool
    
    Returns:
        Running worker instance
    
    Example:
        >>> worker = await create_and_start_worker(
        ...     agent_id="cs-worker-1",
        ...     game_specialization=["cs"],
        ...     source_capabilities=["hltv"],
        ...     coordinator_url="http://localhost:8080",
        ...     db_pool=pool
        ... )
    """
    worker = ExtractionAgentWorker(
        agent_id=agent_id,
        game_specialization=game_specialization,
        source_capabilities=source_capabilities,
        coordinator_url=coordinator_url,
        db_pool=db_pool
    )
    
    # Start in background task
    asyncio.create_task(worker.start())
    
    return worker


__all__ = [
    'ExtractionAgentWorker',
    'create_and_start_worker',
]
