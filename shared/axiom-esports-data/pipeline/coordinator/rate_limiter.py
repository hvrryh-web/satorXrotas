"""
Per-source rate limiting for esports data extraction.
"""

import asyncio
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import time

from .models import GameType, SourceType

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting a specific source."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_allowance: int = 10
    retry_after_seconds: int = 60
    
    # Source-specific defaults
    @classmethod
    def for_source(cls, source: str) -> "RateLimitConfig":
        """Get default config for a source."""
        source = source.lower()
        
        configs = {
            "hltv": cls(
                requests_per_minute=30,
                requests_per_hour=500,
                burst_allowance=5,
                retry_after_seconds=120
            ),
            "vlr": cls(
                requests_per_minute=60,
                requests_per_hour=2000,
                burst_allowance=10,
                retry_after_seconds=60
            ),
            "liquipedia": cls(
                requests_per_minute=30,
                requests_per_hour=300,
                burst_allowance=5,
                retry_after_seconds=120
            ),
            "esl": cls(
                requests_per_minute=100,
                requests_per_hour=3000,
                burst_allowance=20,
                retry_after_seconds=30
            ),
            "blast": cls(
                requests_per_minute=60,
                requests_per_hour=1000,
                burst_allowance=10,
                retry_after_seconds=60
            ),
            "pgl": cls(
                requests_per_minute=60,
                requests_per_hour=1000,
                burst_allowance=10,
                retry_after_seconds=60
            ),
            "faceit": cls(
                requests_per_minute=120,
                requests_per_hour=5000,
                burst_allowance=20,
                retry_after_seconds=30
            ),
            "riot": cls(
                requests_per_minute=100,
                requests_per_hour=3000,
                burst_allowance=15,
                retry_after_seconds=60
            ),
        }
        
        return configs.get(source, cls())


@dataclass
class RateLimitState:
    """Current rate limit state for a source."""
    config: RateLimitConfig = field(default_factory=RateLimitConfig)
    minute_requests: list = field(default_factory=list)
    hour_requests: list = field(default_factory=list)
    last_request_time: float = field(default_factory=time.time)
    consecutive_failures: int = 0
    backoff_until: Optional[datetime] = None
    
    def _cleanup_old_requests(self):
        """Remove expired request timestamps."""
        now = time.time()
        minute_ago = now - 60
        hour_ago = now - 3600
        
        self.minute_requests = [t for t in self.minute_requests if t > minute_ago]
        self.hour_requests = [t for t in self.hour_requests if t > hour_ago]
    
    def get_current_usage(self) -> Tuple[int, int]:
        """Get current request counts (minute, hour)."""
        self._cleanup_old_requests()
        return len(self.minute_requests), len(self.hour_requests)
    
    def is_rate_limited(self) -> bool:
        """Check if currently rate limited."""
        self._cleanup_old_requests()
        
        # Check backoff
        if self.backoff_until and datetime.utcnow() < self.backoff_until:
            return True
        
        minute_count, hour_count = self.get_current_usage()
        
        # Check burst allowance
        if minute_count >= self.config.burst_allowance:
            # If we've used burst, check sustained rate
            if minute_count >= self.config.requests_per_minute:
                return True
        
        if hour_count >= self.config.requests_per_hour:
            return True
        
        return False
    
    def record_request(self):
        """Record a request."""
        now = time.time()
        self.minute_requests.append(now)
        self.hour_requests.append(now)
        self.last_request_time = now
        self.consecutive_failures = 0
    
    def record_failure(self, is_rate_limit: bool = False):
        """Record a failed request."""
        self.consecutive_failures += 1
        
        if is_rate_limit or self.consecutive_failures >= 3:
            # Back off
            backoff_seconds = min(
                self.config.retry_after_seconds * (2 ** (self.consecutive_failures - 1)),
                3600  # Max 1 hour backoff
            )
            self.backoff_until = datetime.utcnow() + timedelta(seconds=backoff_seconds)
            logger.warning(
                f"Rate limit backoff activated until {self.backoff_until} "
                f"({self.consecutive_failures} consecutive failures)"
            )


class RateLimiter:
    """
    Per-source rate limiting manager.
    
    Tracks request rates per source and enforces limits to prevent
    overwhelming data sources or getting blocked.
    """
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self._states: Dict[str, RateLimitState] = defaultdict(
            lambda: RateLimitState(config=RateLimitConfig())
        )
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
    
    async def start(self) -> None:
        """Start background cleanup task."""
        if self._cleanup_task is None:
            self._shutdown_event.clear()
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            logger.info("Rate limiter started")
    
    async def stop(self) -> None:
        """Stop background cleanup task."""
        self._shutdown_event.set()
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Rate limiter stopped")
    
    def _get_source_key(self, source: str) -> str:
        """Normalize source name for lookup."""
        return source.lower().strip()
    
    async def acquire_permit(
        self,
        source: str,
        timeout: Optional[float] = None
    ) -> bool:
        """
        Acquire a rate limit permit for a source.
        
        Args:
            source: Data source name
            timeout: Maximum time to wait for permit (None = no wait)
            
        Returns:
            True if permit acquired
        """
        source_key = self._get_source_key(source)
        start_time = time.time()
        
        while True:
            async with self._lock:
                state = self._states[source_key]
                
                # Ensure config is set for this source
                if state.config == RateLimitConfig():
                    state.config = RateLimitConfig.for_source(source_key)
                
                if not state.is_rate_limited():
                    state.record_request()
                    return True
                
                # Rate limited
                if timeout is None:
                    return False
            
            # Wait before retrying
            await asyncio.sleep(1)
            
            if timeout and (time.time() - start_time) >= timeout:
                return False
    
    async def release_permit(self, source: str, success: bool = True, is_rate_limit: bool = False) -> None:
        """
        Release a permit and record result.
        
        Args:
            source: Data source name
            success: Whether request succeeded
            is_rate_limit: Whether failure was due to rate limiting
        """
        if not success:
            source_key = self._get_source_key(source)
            async with self._lock:
                state = self._states[source_key]
                state.record_failure(is_rate_limit)
    
    async def get_status(self, source: str) -> Dict:
        """
        Get rate limit status for a source.
        
        Args:
            source: Data source name
            
        Returns:
            Status dictionary
        """
        source_key = self._get_source_key(source)
        
        async with self._lock:
            state = self._states[source_key]
            
            # Ensure config is set
            if state.config == RateLimitConfig():
                state.config = RateLimitConfig.for_source(source_key)
            
            minute_count, hour_count = state.get_current_usage()
            config = state.config
            
            return {
                "source": source,
                "requests_per_minute": {
                    "current": minute_count,
                    "limit": config.requests_per_minute,
                    "remaining": max(0, config.requests_per_minute - minute_count)
                },
                "requests_per_hour": {
                    "current": hour_count,
                    "limit": config.requests_per_hour,
                    "remaining": max(0, config.requests_per_hour - hour_count)
                },
                "burst_allowance": config.burst_allowance,
                "is_rate_limited": state.is_rate_limited(),
                "backoff_until": state.backoff_until.isoformat() if state.backoff_until else None,
                "consecutive_failures": state.consecutive_failures
            }
    
    async def get_all_statuses(self) -> Dict[str, Dict]:
        """Get rate limit status for all known sources."""
        sources = set(self._states.keys())
        # Add default sources
        sources.update(["hltv", "vlr", "liquipedia", "esl", "blast", "pgl", "faceit", "riot"])
        
        result = {}
        for source in sources:
            result[source] = await self.get_status(source)
        
        return result
    
    async def reset_source(self, source: str) -> None:
        """Reset rate limit state for a source."""
        source_key = self._get_source_key(source)
        async with self._lock:
            if source_key in self._states:
                del self._states[source_key]
                logger.info(f"Reset rate limits for {source}")
    
    async def update_config(self, source: str, config: RateLimitConfig) -> None:
        """Update rate limit config for a source."""
        source_key = self._get_source_key(source)
        async with self._lock:
            self._states[source_key].config = config
    
    async def _periodic_cleanup(self):
        """Periodically clean up old request entries."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=300  # Clean up every 5 minutes
                )
            except asyncio.TimeoutError:
                pass
            
            if self._shutdown_event.is_set():
                break
            
            await self._cleanup()
    
    async def _cleanup(self):
        """Clean up old entries from all states."""
        async with self._lock:
            for source_key, state in self._states.items():
                old_minute = len(state.minute_requests)
                old_hour = len(state.hour_requests)
                state._cleanup_old_requests()
                
                if len(state.minute_requests) != old_minute or len(state.hour_requests) != old_hour:
                    logger.debug(
                        f"Cleaned up {source_key}: "
                        f"minute {old_minute}->{len(state.minute_requests)}, "
                        f"hour {old_hour}->{len(state.hour_requests)}"
                    )
    
    def get_wait_time(self, source: str) -> float:
        """
        Get estimated wait time until next permit is available.
        
        Args:
            source: Data source name
            
        Returns:
            Estimated seconds to wait (0 if permit available now)
        """
        source_key = self._get_source_key(source)
        state = self._states[source_key]
        
        if not state.is_rate_limited():
            return 0.0
        
        if state.backoff_until:
            wait = (state.backoff_until - datetime.utcnow()).total_seconds()
            if wait > 0:
                return wait
        
        # Calculate based on request history
        state._cleanup_old_requests()
        minute_count, _ = state.get_current_usage()
        
        if minute_count >= state.config.requests_per_minute:
            # Need to wait for oldest request to expire
            if state.minute_requests:
                oldest = min(state.minute_requests)
                return max(0.0, 60 - (time.time() - oldest))
        
        return 1.0  # Default small wait


class AdaptiveRateLimiter(RateLimiter):
    """
    Rate limiter that adapts to observed response patterns.
    
    Automatically adjusts rate limits based on observed rate limit
    responses from the source.
    """
    
    def __init__(self, redis_client=None):
        super().__init__(redis_client)
        self._success_rates: Dict[str, list] = defaultdict(list)
    
    async def record_result(
        self,
        source: str,
        success: bool,
        response_time_ms: Optional[float] = None,
        is_rate_limited: bool = False
    ) -> None:
        """
        Record request result for adaptive tuning.
        
        Args:
            source: Data source name
            success: Whether request succeeded
            response_time_ms: Response time in milliseconds
            is_rate_limited: Whether response indicated rate limiting
        """
        source_key = self._get_source_key(source)
        
        async with self._lock:
            state = self._states[source_key]
            
            if not success:
                state.record_failure(is_rate_limited)
                
                # Adaptive: reduce limits if we're getting rate limited
                if is_rate_limited:
                    old_rpm = state.config.requests_per_minute
                    state.config.requests_per_minute = max(
                        10,  # Minimum
                        int(old_rpm * 0.8)  # Reduce by 20%
                    )
                    logger.warning(
                        f"Adaptive rate limit: reduced {source} RPM "
                        f"from {old_rpm} to {state.config.requests_per_minute}"
                    )
            else:
                state.consecutive_failures = 0
                
                # Track success for potential limit increases
                self._success_rates[source_key].append(time.time())
                
                # Clean old success records
                cutoff = time.time() - 300  # 5 minutes
                self._success_rates[source_key] = [
                    t for t in self._success_rates[source_key]
                    if t > cutoff
                ]
                
                # Consider increasing limits if sustained success
                if len(self._success_rates[source_key]) >= 50:
                    default_config = RateLimitConfig.for_source(source_key)
                    if state.config.requests_per_minute < default_config.requests_per_minute:
                        old_rpm = state.config.requests_per_minute
                        state.config.requests_per_minute = min(
                            default_config.requests_per_minute,
                            int(old_rpm * 1.1)  # Increase by 10%
                        )
                        logger.info(
                            f"Adaptive rate limit: increased {source} RPM "
                            f"from {old_rpm} to {state.config.requests_per_minute}"
                        )
                        self._success_rates[source_key] = []
