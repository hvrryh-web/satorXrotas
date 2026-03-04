"""Data Pipeline health check collector."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from .base import HealthCheckCollector
from ..models import HealthCheckResult, HealthStatus, CheckType, SystemComponent


class PipelineCollector(HealthCheckCollector):
    """Collects health checks for data pipeline components."""
    
    def __init__(self, component: SystemComponent, 
                 api_base_url: Optional[str] = None,
                 db_pool = None):
        super().__init__(component)
        self.api_base_url = api_base_url
        self.db_pool = db_pool
    
    async def collect(self) -> List[HealthCheckResult]:
        """Collect pipeline health metrics."""
        checks = []
        
        # Job queue status
        checks.append(await self._check_job_queue())
        
        # Recent job success rate
        checks.append(await self._check_job_success_rate())
        
        # Data freshness
        checks.append(await self._check_data_freshness())
        
        # Extractor specific checks
        if "extractor" in self.component.component_id:
            checks.append(await self._check_extractor_status())
        
        return checks
    
    async def _check_job_queue(self) -> HealthCheckResult:
        """Check job queue status."""
        # If we have API access, query the coordinator
        if self.api_base_url and self.session:
            try:
                url = f"{self.api_base_url}/jobs/queue/status"
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        queued = data.get("queued", 0)
                        running = data.get("running", 0)
                        failed = data.get("failed_recent", 0)
                        
                        status = HealthStatus.HEALTHY
                        if failed > 10 or queued > 1000:
                            status = HealthStatus.DEGRADED
                        if failed > 50 or queued > 5000:
                            status = HealthStatus.CRITICAL
                        
                        return HealthCheckResult(
                            check_id=f"{self.component.component_id}_queue",
                            name="Job Queue Status",
                            layer=self.component.layer,
                            check_type=CheckType.CAPACITY,
                            status=status,
                            actual_value=queued,
                            warning_threshold=1000,
                            critical_threshold=5000,
                            details={
                                "queued": queued,
                                "running": running,
                                "failed_recent": failed
                            }
                        )
            except:
                pass
        
        # Fallback to basic connectivity check
        if self.component.health_endpoint:
            return await self.check_http_endpoint(
                url=self.component.health_endpoint,
                check_id=f"{self.component.component_id}_queue",
                check_name="Job Queue Status"
            )
        
        return HealthCheckResult(
            check_id=f"{self.component.component_id}_queue",
            name="Job Queue Status",
            layer=self.component.layer,
            check_type=CheckType.CAPACITY,
            status=HealthStatus.UNKNOWN,
            message="No health endpoint or API configured"
        )
    
    async def _check_job_success_rate(self) -> HealthCheckResult:
        """Check recent job success rate."""
        # This would typically query the database for job history
        if self.db_pool:
            try:
                async with self.db_pool.acquire() as conn:
                    result = await conn.fetchrow(
                        """
                        SELECT 
                            count(*) FILTER (WHERE status = 'completed') as completed,
                            count(*) FILTER (WHERE status = 'failed') as failed,
                            count(*) as total
                        FROM pipeline_jobs
                        WHERE started_at > now() - interval '1 hour'
                        """
                    )
                    
                    total = result['total'] or 1  # Avoid division by zero
                    failed = result['failed'] or 0
                    success_rate = ((total - failed) / total) * 100
                    
                    status = HealthStatus.HEALTHY
                    if success_rate < 95:
                        status = HealthStatus.DEGRADED
                    if success_rate < 80:
                        status = HealthStatus.CRITICAL
                    
                    return HealthCheckResult(
                        check_id=f"{self.component.component_id}_success_rate",
                        name="Job Success Rate (1h)",
                        layer=self.component.layer,
                        check_type=CheckType.ERROR_RATE,
                        status=status,
                        actual_value=success_rate,
                        warning_threshold=95,
                        critical_threshold=80,
                        details={
                            "total_jobs": total,
                            "failed_jobs": failed,
                            "success_rate": f"{success_rate:.1f}%"
                        }
                    )
            except Exception as e:
                return HealthCheckResult(
                    check_id=f"{self.component.component_id}_success_rate",
                    name="Job Success Rate (1h)",
                    layer=self.component.layer,
                    check_type=CheckType.ERROR_RATE,
                    status=HealthStatus.UNKNOWN,
                    message=f"Database query failed: {str(e)}"
                )
        
        return HealthCheckResult(
            check_id=f"{self.component.component_id}_success_rate",
            name="Job Success Rate (1h)",
            layer=self.component.layer,
            check_type=CheckType.ERROR_RATE,
            status=HealthStatus.UNKNOWN,
            message="No database connection configured"
        )
    
    async def _check_data_freshness(self) -> HealthCheckResult:
        """Check if pipeline data is fresh."""
        if self.db_pool:
            try:
                async with self.db_pool.acquire() as conn:
                    # Get last successful run for this component
                    result = await conn.fetchrow(
                        """
                        SELECT max(completed_at) as last_run
                        FROM pipeline_jobs
                        WHERE component_id = $1
                          AND status = 'completed'
                        """,
                        self.component.component_id
                    )
                    
                    last_run = result['last_run']
                    if last_run:
                        age_minutes = (datetime.utcnow() - last_run).total_seconds() / 60
                        
                        # Determine status based on expected interval
                        interval = self.component.check_interval_seconds / 60  # Convert to minutes
                        
                        status = HealthStatus.HEALTHY
                        if age_minutes > interval * 2:
                            status = HealthStatus.DEGRADED
                        if age_minutes > interval * 5:
                            status = HealthStatus.CRITICAL
                        
                        return HealthCheckResult(
                            check_id=f"{self.component.component_id}_freshness",
                            name="Data Freshness",
                            layer=self.component.layer,
                            check_type=CheckType.DATA_FRESHNESS,
                            status=status,
                            actual_value=age_minutes,
                            warning_threshold=interval * 2,
                            critical_threshold=interval * 5,
                            details={
                                "last_run": last_run.isoformat() if last_run else None,
                                "age_minutes": round(age_minutes, 1)
                            }
                        )
                    else:
                        return HealthCheckResult(
                            check_id=f"{self.component.component_id}_freshness",
                            name="Data Freshness",
                            layer=self.component.layer,
                            check_type=CheckType.DATA_FRESHNESS,
                            status=HealthStatus.CRITICAL,
                            message="No successful runs found"
                        )
            except Exception as e:
                return HealthCheckResult(
                    check_id=f"{self.component.component_id}_freshness",
                    name="Data Freshness",
                    layer=self.component.layer,
                    check_type=CheckType.DATA_FRESHNESS,
                    status=HealthStatus.UNKNOWN,
                    message=f"Database query failed: {str(e)}"
                )
        
        return HealthCheckResult(
            check_id=f"{self.component.component_id}_freshness",
            name="Data Freshness",
            layer=self.component.layer,
            check_type=CheckType.DATA_FRESHNESS,
            status=HealthStatus.UNKNOWN,
            message="No database connection configured"
        )
    
    async def _check_extractor_status(self) -> HealthCheckResult:
        """Check extractor-specific status."""
        game = self.component.component_id.replace("_extractor", "")
        
        if self.db_pool:
            try:
                async with self.db_pool.acquire() as conn:
                    # Check for recent matches processed
                    result = await conn.fetchrow(
                        f"""
                        SELECT 
                            count(*) as matches_count,
                            max(created_at) as last_match
                        FROM {game}_matches
                        WHERE created_at > now() - interval '24 hours'
                        """
                    )
                    
                    matches_count = result['matches_count'] or 0
                    last_match = result['last_match']
                    
                    status = HealthStatus.HEALTHY
                    if matches_count == 0:
                        status = HealthStatus.DEGRADED
                    
                    return HealthCheckResult(
                        check_id=f"{self.component.component_id}_extractor",
                        name=f"{game.title()} Extractor Status",
                        layer=self.component.layer,
                        check_type=CheckType.CUSTOM,
                        status=status,
                        actual_value=matches_count,
                        details={
                            "matches_24h": matches_count,
                            "last_match": last_match.isoformat() if last_match else None
                        }
                    )
            except Exception as e:
                return HealthCheckResult(
                    check_id=f"{self.component.component_id}_extractor",
                    name=f"{game.title()} Extractor Status",
                    layer=self.component.layer,
                    check_type=CheckType.CUSTOM,
                    status=HealthStatus.UNKNOWN,
                    message=f"Database query failed: {str(e)}"
                )
        
        return HealthCheckResult(
            check_id=f"{self.component.component_id}_extractor",
            name="Extractor Status",
            layer=self.component.layer,
            check_type=CheckType.CUSTOM,
            status=HealthStatus.UNKNOWN,
            message="No database connection configured"
        )
