"""Base class for health check collectors."""

from abc import ABC, abstractmethod
from typing import List, Optional
import asyncio
import aiohttp
import logging

from ..models import HealthCheckResult, SystemComponent, HealthStatus, CheckType

logger = logging.getLogger(__name__)


class HealthCheckCollector(ABC):
    """Abstract base class for health check collectors."""
    
    def __init__(self, component: SystemComponent):
        self.component = component
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.component.timeout_seconds)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def collect(self) -> List[HealthCheckResult]:
        """Collect health checks for this component."""
        pass
    
    async def check_http_endpoint(
        self,
        url: str,
        check_id: str,
        check_name: str,
        expected_status: int = 200
    ) -> HealthCheckResult:
        """Generic HTTP endpoint health check."""
        import time
        
        start = time.time()
        try:
            async with self.session.get(url) as response:
                elapsed = (time.time() - start) * 1000
                
                if response.status == expected_status:
                    return HealthCheckResult(
                        check_id=check_id,
                        name=check_name,
                        layer=self.component.layer,
                        check_type=CheckType.CONNECTIVITY,
                        status=HealthStatus.HEALTHY,
                        response_time_ms=elapsed,
                        message=f"HTTP {response.status}",
                        actual_value=elapsed
                    )
                else:
                    return HealthCheckResult(
                        check_id=check_id,
                        name=check_name,
                        layer=self.component.layer,
                        check_type=CheckType.CONNECTIVITY,
                        status=HealthStatus.CRITICAL,
                        response_time_ms=elapsed,
                        message=f"Unexpected status: {response.status}",
                        actual_value=response.status
                    )
        except asyncio.TimeoutError:
            return HealthCheckResult(
                check_id=check_id,
                name=check_name,
                layer=self.component.layer,
                check_type=CheckType.CONNECTIVITY,
                status=HealthStatus.CRITICAL,
                message="Connection timeout",
                consecutive_failures=1
            )
        except Exception as e:
            return HealthCheckResult(
                check_id=check_id,
                name=check_name,
                layer=self.component.layer,
                check_type=CheckType.CONNECTIVITY,
                status=HealthStatus.CRITICAL,
                message=str(e),
                consecutive_failures=1
            )
