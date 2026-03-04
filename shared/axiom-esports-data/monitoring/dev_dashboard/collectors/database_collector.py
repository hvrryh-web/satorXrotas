"""Database health check collector."""

from typing import List, Optional
import asyncpg

from .base import HealthCheckCollector
from ..models import HealthCheckResult, HealthStatus, CheckType


class DatabaseCollector(HealthCheckCollector):
    """Collects health checks for PostgreSQL database."""
    
    def __init__(self, component: SystemComponent, db_pool: Optional[asyncpg.Pool] = None, 
                 dsn: Optional[str] = None):
        super().__init__(component)
        self.db_pool = db_pool
        self.dsn = dsn
        self._local_pool: Optional[asyncpg.Pool] = None
    
    async def _get_pool(self) -> asyncpg.Pool:
        """Get or create database pool."""
        if self.db_pool:
            return self.db_pool
        if self._local_pool is None and self.dsn:
            self._local_pool = await asyncpg.create_pool(self.dsn, min_size=1, max_size=2)
        return self._local_pool
    
    async def close(self):
        """Close local pool if created."""
        if self._local_pool:
            await self._local_pool.close()
            self._local_pool = None
    
    async def collect(self) -> List[HealthCheckResult]:
        """Collect database health metrics."""
        checks = []
        
        # Connection check
        checks.append(await self._check_connection())
        
        # Disk space
        checks.append(await self._check_disk_space())
        
        # Replication lag (if replica)
        checks.append(await self._check_replication_lag())
        
        # Active connections
        checks.append(await self._check_connections())
        
        # Slow queries
        checks.append(await self._check_slow_queries())
        
        return checks
    
    async def _check_connection(self) -> HealthCheckResult:
        """Check database connectivity and latency."""
        import time
        
        start = time.time()
        try:
            pool = await self._get_pool()
            if pool is None:
                return HealthCheckResult(
                    check_id=f"{self.component.component_id}_connection",
                    name="Database Connection",
                    layer=self.component.layer,
                    check_type=CheckType.CONNECTIVITY,
                    status=HealthStatus.UNKNOWN,
                    message="No database pool or DSN configured"
                )
            
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                elapsed = (time.time() - start) * 1000
                
                return HealthCheckResult(
                    check_id=f"{self.component.component_id}_connection",
                    name="Database Connection",
                    layer=self.component.layer,
                    check_type=CheckType.CONNECTIVITY,
                    status=HealthStatus.HEALTHY,
                    response_time_ms=elapsed,
                    actual_value=elapsed,
                    warning_threshold=100,
                    critical_threshold=500
                )
        except Exception as e:
            return HealthCheckResult(
                check_id=f"{self.component.component_id}_connection",
                name="Database Connection",
                layer=self.component.layer,
                check_type=CheckType.CONNECTIVITY,
                status=HealthStatus.CRITICAL,
                message=str(e)
            )
    
    async def _check_disk_space(self) -> HealthCheckResult:
        """Check database disk usage."""
        try:
            pool = await self._get_pool()
            if pool is None:
                return HealthCheckResult(
                    check_id=f"{self.component.component_id}_disk",
                    name="Database Disk Usage",
                    layer=self.component.layer,
                    check_type=CheckType.CAPACITY,
                    status=HealthStatus.UNKNOWN,
                    message="No database pool or DSN configured"
                )
            
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT 
                        pg_database_size(current_database()) as db_size,
                        pg_size_pretty(pg_database_size(current_database())) as size_pretty
                    """
                )
                
                size_bytes = row['db_size']
                size_gb = size_bytes / (1024 ** 3)
                
                # Determine status based on size
                status = HealthStatus.HEALTHY
                if size_gb > 100:  # 100GB
                    status = HealthStatus.DEGRADED
                if size_gb > 400:  # 400GB (Supabase limit 500GB)
                    status = HealthStatus.CRITICAL
                
                return HealthCheckResult(
                    check_id=f"{self.component.component_id}_disk",
                    name="Database Disk Usage",
                    layer=self.component.layer,
                    check_type=CheckType.CAPACITY,
                    status=status,
                    actual_value=size_gb,
                    warning_threshold=100,
                    critical_threshold=400,
                    details={"size_pretty": row['size_pretty']}
                )
        except Exception as e:
            return HealthCheckResult(
                check_id=f"{self.component.component_id}_disk",
                name="Database Disk Usage",
                layer=self.component.layer,
                check_type=CheckType.CAPACITY,
                status=HealthStatus.UNKNOWN,
                message=str(e)
            )
    
    async def _check_replication_lag(self) -> HealthCheckResult:
        """Check replication lag if applicable."""
        try:
            pool = await self._get_pool()
            if pool is None:
                return HealthCheckResult(
                    check_id=f"{self.component.component_id}_replication",
                    name="Replication Lag",
                    layer=self.component.layer,
                    check_type=CheckType.LATENCY,
                    status=HealthStatus.UNKNOWN,
                    message="No database pool or DSN configured"
                )
            
            async with pool.acquire() as conn:
                lag = await conn.fetchval(
                    "SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp()))"
                )
                
                if lag is None:
                    return HealthCheckResult(
                        check_id=f"{self.component.component_id}_replication",
                        name="Replication Lag",
                        layer=self.component.layer,
                        check_type=CheckType.LATENCY,
                        status=HealthStatus.HEALTHY,
                        message="Not a replica"
                    )
                
                status = HealthStatus.HEALTHY
                if lag > 60:  # 1 minute
                    status = HealthStatus.DEGRADED
                if lag > 300:  # 5 minutes
                    status = HealthStatus.CRITICAL
                
                return HealthCheckResult(
                    check_id=f"{self.component.component_id}_replication",
                    name="Replication Lag",
                    layer=self.component.layer,
                    check_type=CheckType.LATENCY,
                    status=status,
                    actual_value=lag,
                    warning_threshold=60,
                    critical_threshold=300,
                    details={"lag_seconds": lag}
                )
        except Exception as e:
            return HealthCheckResult(
                check_id=f"{self.component.component_id}_replication",
                name="Replication Lag",
                layer=self.component.layer,
                check_type=CheckType.LATENCY,
                status=HealthStatus.UNKNOWN,
                message=str(e)
            )
    
    async def _check_connections(self) -> HealthCheckResult:
        """Check active database connections."""
        try:
            pool = await self._get_pool()
            if pool is None:
                return HealthCheckResult(
                    check_id=f"{self.component.component_id}_connections",
                    name="Active Connections",
                    layer=self.component.layer,
                    check_type=CheckType.CAPACITY,
                    status=HealthStatus.UNKNOWN,
                    message="No database pool or DSN configured"
                )
            
            async with pool.acquire() as conn:
                result = await conn.fetchrow(
                    """
                    SELECT 
                        count(*) as total,
                        count(*) FILTER (WHERE state = 'active') as active,
                        count(*) FILTER (WHERE state = 'idle') as idle
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                    """
                )
                
                total = result['total']
                
                return HealthCheckResult(
                    check_id=f"{self.component.component_id}_connections",
                    name="Active Connections",
                    layer=self.component.layer,
                    check_type=CheckType.CAPACITY,
                    status=HealthStatus.HEALTHY if total < 80 else HealthStatus.DEGRADED,
                    actual_value=total,
                    warning_threshold=80,
                    critical_threshold=95,
                    details={
                        "active": result['active'],
                        "idle": result['idle']
                    }
                )
        except Exception as e:
            return HealthCheckResult(
                check_id=f"{self.component.component_id}_connections",
                name="Active Connections",
                layer=self.component.layer,
                check_type=CheckType.CAPACITY,
                status=HealthStatus.UNKNOWN,
                message=str(e)
            )
    
    async def _check_slow_queries(self) -> HealthCheckResult:
        """Check for slow running queries."""
        try:
            pool = await self._get_pool()
            if pool is None:
                return HealthCheckResult(
                    check_id=f"{self.component.component_id}_slow_queries",
                    name="Slow Queries (>30s)",
                    layer=self.component.layer,
                    check_type=CheckType.ERROR_RATE,
                    status=HealthStatus.UNKNOWN,
                    message="No database pool or DSN configured"
                )
            
            async with pool.acquire() as conn:
                count = await conn.fetchval(
                    """
                    SELECT count(*) 
                    FROM pg_stat_activity
                    WHERE state = 'active'
                      AND now() - query_start > interval '30 seconds'
                    """
                )
                
                status = HealthStatus.HEALTHY
                if count > 5:
                    status = HealthStatus.DEGRADED
                if count > 10:
                    status = HealthStatus.CRITICAL
                
                return HealthCheckResult(
                    check_id=f"{self.component.component_id}_slow_queries",
                    name="Slow Queries (>30s)",
                    layer=self.component.layer,
                    check_type=CheckType.ERROR_RATE,
                    status=status,
                    actual_value=count,
                    warning_threshold=5,
                    critical_threshold=10
                )
        except Exception as e:
            return HealthCheckResult(
                check_id=f"{self.component.component_id}_slow_queries",
                name="Slow Queries (>30s)",
                layer=self.component.layer,
                check_type=CheckType.ERROR_RATE,
                status=HealthStatus.UNKNOWN,
                message=str(e)
            )
