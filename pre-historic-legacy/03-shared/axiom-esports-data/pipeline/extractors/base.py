from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio
import aiohttp
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Result of an extraction job."""
    job_id: str
    success: bool
    records_extracted: int
    records_failed: int
    data: Optional[List[Dict]] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None
    checksum: Optional[str] = None


class BaseExtractor(ABC):
    """
    Abstract base class for game extractors.
    
    All game-specific extractors must implement:
    - discover_matches()
    - extract_match_detail()
    - extract_player_stats()
    - validate_data()
    """
    
    def __init__(
        self,
        game_type: str,
        source: str,
        rate_limiter,
        db_pool,
        coordinator_url: str
    ):
        self.game_type = game_type
        self.source = source
        self.rate_limiter = rate_limiter
        self.db_pool = db_pool
        self.coordinator_url = coordinator_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.agent_id: Optional[str] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers=self._get_headers()
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    @abstractmethod
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for requests."""
        pass
    
    @abstractmethod
    async def discover_matches(
        self,
        date_start: datetime,
        date_end: datetime,
        region: Optional[str] = None
    ) -> AsyncIterator[Dict]:
        """Discover match IDs in date range."""
        pass
    
    @abstractmethod
    async def extract_match_detail(self, match_id: str) -> Dict:
        """Extract detailed match data."""
        pass
    
    @abstractmethod
    async def extract_player_stats(
        self,
        player_id: str,
        date_start: Optional[datetime] = None,
        date_end: Optional[datetime] = None
    ) -> Dict:
        """Extract player statistics."""
        pass
    
    @abstractmethod
    async def validate_data(self, data: Dict) -> bool:
        """Validate extracted data."""
        pass
    
    async def run_job(self, job: Dict) -> ExtractionResult:
        """Execute extraction job."""
        job_id = job['id']
        job_type = job['job_type']
        
        try:
            # Check rate limit
            if not await self.rate_limiter.acquire(self.source):
                return ExtractionResult(
                    job_id=job_id,
                    success=False,
                    records_extracted=0,
                    records_failed=0,
                    error_message="Rate limit exceeded"
                )
            
            # Execute based on job type
            if job_type == 'match_list':
                result = await self._extract_match_list(job)
            elif job_type == 'match_detail':
                result = await self._extract_match_detail(job)
            elif job_type == 'player_stats':
                result = await self._extract_player_stats(job)
            else:
                result = ExtractionResult(
                    job_id=job_id,
                    success=False,
                    records_extracted=0,
                    records_failed=0,
                    error_message=f"Unknown job type: {job_type}"
                )
            
            return result
            
        except Exception as e:
            logger.exception(f"Job {job_id} failed")
            return ExtractionResult(
                job_id=job_id,
                success=False,
                records_extracted=0,
                records_failed=1,
                error_message=str(e)
            )
    
    async def _extract_match_list(self, job: Dict) -> ExtractionResult:
        """Extract list of matches."""
        matches = []
        async for match in self.discover_matches(
            date_start=job.get('date_start'),
            date_end=job.get('date_end'),
            region=job.get('region')
        ):
            matches.append(match)
        
        # Submit discovered matches as new jobs
        await self._submit_discovery_jobs(matches)
        
        return ExtractionResult(
            job_id=job['id'],
            success=True,
            records_extracted=len(matches),
            records_failed=0,
            metadata={'discovered_matches': [m['id'] for m in matches]}
        )
    
    async def _submit_discovery_jobs(self, matches: List[Dict]) -> None:
        """Submit discovered matches as new detail extraction jobs."""
        if not matches:
            return
        
        jobs = [
            {
                'game': self.game_type,
                'source': self.source,
                'job_type': 'match_detail',
                'priority': 4,  # Lower than discovery
                'metadata': {'match_id': m['id']}
            }
            for m in matches
        ]
        
        async with self.session.post(
            f"{self.coordinator_url}/jobs/batch",
            json={'jobs': jobs}
        ) as response:
            if response.status != 200:
                logger.error(f"Failed to submit discovery jobs: {response.status}")
