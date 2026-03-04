"""API Services health check collector."""

from typing import List, Optional
import json

from .base import HealthCheckCollector
from ..models import HealthCheckResult, HealthStatus, CheckType, SystemComponent


class APICollector(HealthCheckCollector):
    """Collects health checks for FastAPI and other API services."""
    
    def __init__(self, component: SystemComponent, base_url: Optional[str] = None):
        super().__init__(component)
        self.base_url = base_url or component.health_endpoint
        # Ensure base_url doesn't end with trailing slash for consistency
        self.base_url = self.base_url.rstrip('/') if self.base_url else None
    
    async def collect(self) -> List[HealthCheckResult]:
        """Collect API health metrics."""
        checks = []
        
        if not self.base_url:
            return [HealthCheckResult(
                check_id=f"{self.component.component_id}_no_endpoint",
                name="API Endpoint",
                layer=self.component.layer,
                check_type=CheckType.CONNECTIVITY,
                status=HealthStatus.UNKNOWN,
                message="No base URL configured for API checks"
            )]
        
        # Basic health endpoint check
        checks.append(await self._check_health_endpoint())
        
        # API latency check
        checks.append(await self._check_api_latency())
        
        # Deep health check (if available)
        checks.append(await self._check_deep_health())
        
        # Metrics endpoint (if available)
        if self.component.metrics_endpoint:
            checks.append(await self._check_metrics_endpoint())
        
        return checks
    
    async def _check_health_endpoint(self) -> HealthCheckResult:
        """Check basic /health endpoint."""
        url = f"{self.base_url}/health"
        
        result = await self.check_http_endpoint(
            url=url,
            check_id=f"{self.component.component_id}_health",
            check_name="Health Endpoint",
            expected_status=200
        )
        
        # Try to parse response for additional details
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    try:
                        data = await response.json()
                        result.details = {
                            "version": data.get("version"),
                            "environment": data.get("environment"),
                            "timestamp": data.get("timestamp")
                        }
                    except:
                        text = await response.text()
                        result.details = {"response": text[:200]}
        except:
            pass
        
        return result
    
    async def _check_api_latency(self) -> HealthCheckResult:
        """Check API response time for a simple endpoint."""
        import time
        
        # Try common simple endpoints
        test_endpoints = ["/health", "/api/health", "/ping", "/api/ping"]
        
        for endpoint in test_endpoints:
            url = f"{self.base_url}{endpoint}"
            try:
                start = time.time()
                async with self.session.get(url) as response:
                    elapsed = (time.time() - start) * 1000
                    
                    status = HealthStatus.HEALTHY
                    if elapsed > 500:  # 500ms
                        status = HealthStatus.DEGRADED
                    if elapsed > 2000:  # 2 seconds
                        status = HealthStatus.CRITICAL
                    
                    return HealthCheckResult(
                        check_id=f"{self.component.component_id}_latency",
                        name="API Latency",
                        layer=self.component.layer,
                        check_type=CheckType.LATENCY,
                        status=status,
                        response_time_ms=elapsed,
                        actual_value=elapsed,
                        warning_threshold=500,
                        critical_threshold=2000,
                        details={"test_endpoint": endpoint}
                    )
            except:
                continue
        
        return HealthCheckResult(
            check_id=f"{self.component.component_id}_latency",
            name="API Latency",
            layer=self.component.layer,
            check_type=CheckType.LATENCY,
            status=HealthStatus.CRITICAL,
            message="Could not connect to any test endpoint"
        )
    
    async def _check_deep_health(self) -> HealthCheckResult:
        """Check deep health endpoint with dependency status."""
        import time
        
        # Common deep health endpoints
        deep_endpoints = ["/health/deep", "/health/ready", "/api/health/deep"]
        
        for endpoint in deep_endpoints:
            url = f"{self.base_url}{endpoint}"
            try:
                start = time.time()
                async with self.session.get(url) as response:
                    elapsed = (time.time() - start) * 1000
                    
                    if response.status == 200:
                        try:
                            data = await response.json()
                            # Check for overall status in response
                            health_status = data.get("status", "healthy").lower()
                            
                            status_map = {
                                "healthy": HealthStatus.HEALTHY,
                                "ok": HealthStatus.HEALTHY,
                                "degraded": HealthStatus.DEGRADED,
                                "unhealthy": HealthStatus.CRITICAL,
                                "error": HealthStatus.CRITICAL
                            }
                            
                            status = status_map.get(health_status, HealthStatus.HEALTHY)
                            
                            # Extract dependencies info
                            deps = data.get("dependencies", {})
                            failed_deps = [k for k, v in deps.items() if not v]
                            
                            return HealthCheckResult(
                                check_id=f"{self.component.component_id}_deep_health",
                                name="Deep Health Check",
                                layer=self.component.layer,
                                check_type=CheckType.DEPENDENCY,
                                status=status,
                                response_time_ms=elapsed,
                                message=f"Failed dependencies: {failed_deps}" if failed_deps else "All dependencies healthy",
                                details={
                                    "dependencies": deps,
                                    "failed_dependencies": failed_deps
                                }
                            )
                        except:
                            return HealthCheckResult(
                                check_id=f"{self.component.component_id}_deep_health",
                                name="Deep Health Check",
                                layer=self.component.layer,
                                check_type=CheckType.DEPENDENCY,
                                status=HealthStatus.HEALTHY,
                                response_time_ms=elapsed,
                                message="Deep health endpoint responding"
                            )
            except:
                continue
        
        # No deep health endpoint found - not critical
        return HealthCheckResult(
            check_id=f"{self.component.component_id}_deep_health",
            name="Deep Health Check",
            layer=self.component.layer,
            check_type=CheckType.DEPENDENCY,
            status=HealthStatus.HEALTHY,
            message="Deep health endpoint not configured"
        )
    
    async def _check_metrics_endpoint(self) -> HealthCheckResult:
        """Check if metrics endpoint is available."""
        url = self.component.metrics_endpoint
        if not url.startswith('http'):
            url = f"{self.base_url}{url}"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return HealthCheckResult(
                        check_id=f"{self.component.component_id}_metrics",
                        name="Metrics Endpoint",
                        layer=self.component.layer,
                        check_type=CheckType.CUSTOM,
                        status=HealthStatus.HEALTHY,
                        message="Metrics endpoint responding"
                    )
                else:
                    return HealthCheckResult(
                        check_id=f"{self.component.component_id}_metrics",
                        name="Metrics Endpoint",
                        layer=self.component.layer,
                        check_type=CheckType.CUSTOM,
                        status=HealthStatus.DEGRADED,
                        message=f"Metrics endpoint returned status {response.status}"
                    )
        except Exception as e:
            return HealthCheckResult(
                check_id=f"{self.component.component_id}_metrics",
                name="Metrics Endpoint",
                layer=self.component.layer,
                check_type=CheckType.CUSTOM,
                status=HealthStatus.DEGRADED,
                message=f"Metrics endpoint error: {str(e)}"
            )
