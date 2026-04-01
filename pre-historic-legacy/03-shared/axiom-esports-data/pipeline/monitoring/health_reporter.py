"""
Health Reporter — Health check endpoints for monitoring systems.

Provides Kubernetes-style health probes:
    - /health: Overall health status
    - /ready: Readiness probe (can accept traffic)
    - /live: Liveness probe (should be restarted)

Health states:
    - healthy: All systems operational
    - degraded: Some issues but functioning
    - unhealthy: Critical failure, needs attention

Example:
    from pipeline.monitoring import HealthReporter
    
    reporter = HealthReporter(db_connection=conn)
    
    # Full health check
    health = reporter.get_health()
    if health.status == "unhealthy":
        send_alert(health.issues)
    
    # K8s probes
    readiness = reporter.get_readiness()
    liveness = reporter.get_liveness()
"""

import os
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class HealthState(str, Enum):
    """Overall health state."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Health status for a single component."""
    name: str
    status: HealthState
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=datetime.utcnow)
    latency_ms: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "checked_at": self.checked_at.isoformat(),
            "latency_ms": self.latency_ms,
        }


@dataclass
class HealthReport:
    """Complete health report."""
    status: HealthState
    components: list[ComponentHealth]
    issues: list[str] = field(default_factory=list)
    checked_at: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    
    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "components": [c.to_dict() for c in self.components],
            "issues": self.issues,
            "checked_at": self.checked_at.isoformat(),
            "version": self.version,
        }


@dataclass
class HealthStatus:
    """Simple health status for probes."""
    healthy: bool
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        return {
            "healthy": self.healthy,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
        }


class HealthReporter:
    """
    Health check provider for load balancers and monitoring systems.
    
    Checks:
        - Database connectivity
        - Registry load status
        - Recent run success rate
        - Disk space
        - Memory usage
    """
    
    def __init__(
        self,
        db_connection: Optional[Any] = None,
        registry: Optional[Any] = None,
        metrics_path: Optional[str] = None,
        min_disk_space_gb: float = 1.0,
        min_memory_percent: float = 90.0,
    ) -> None:
        """
        Initialize health reporter.
        
        Args:
            db_connection: Database connection object
            registry: KnownRecordRegistry instance
            metrics_path: Path to metrics storage
            min_disk_space_gb: Minimum required disk space in GB
            min_memory_percent: Maximum acceptable memory usage %
        """
        self._db = db_connection
        self._registry = registry
        self._metrics_path = metrics_path or "data/metrics"
        self._min_disk_space_gb = min_disk_space_gb
        self._min_memory_percent = min_memory_percent
    
    def get_health(self) -> HealthReport:
        """
        Check all components and return comprehensive health report.
        
        Returns:
            HealthReport with status and component details
        """
        components: list[ComponentHealth] = []
        issues: list[str] = []
        
        # Check database
        db_health = self._check_database()
        components.append(db_health)
        if db_health.status != HealthState.HEALTHY:
            issues.append(f"Database: {db_health.message}")
        
        # Check registry
        registry_health = self._check_registry()
        components.append(registry_health)
        if registry_health.status != HealthState.HEALTHY:
            issues.append(f"Registry: {registry_health.message}")
        
        # Check disk space
        disk_health = self._check_disk_space()
        components.append(disk_health)
        if disk_health.status != HealthState.HEALTHY:
            issues.append(f"Disk: {disk_health.message}")
        
        # Check memory
        memory_health = self._check_memory()
        components.append(memory_health)
        if memory_health.status != HealthState.HEALTHY:
            issues.append(f"Memory: {memory_health.message}")
        
        # Check recent runs
        runs_health = self._check_recent_runs()
        components.append(runs_health)
        if runs_health.status != HealthState.HEALTHY:
            issues.append(f"Recent runs: {runs_health.message}")
        
        # Determine overall status
        if any(c.status == HealthState.UNHEALTHY for c in components):
            status = HealthState.UNHEALTHY
        elif any(c.status == HealthState.DEGRADED for c in components):
            status = HealthState.DEGRADED
        else:
            status = HealthState.HEALTHY
        
        return HealthReport(
            status=status,
            components=components,
            issues=issues,
        )
    
    def get_readiness(self) -> HealthStatus:
        """
        Kubernetes-style readiness probe.
        
        Returns True when the service is ready to accept traffic.
        Requires:
            - Database connectivity
            - Registry loaded
        """
        issues = []
        
        # Check database
        db_health = self._check_database()
        if db_health.status == HealthState.UNHEALTHY:
            issues.append("Database not accessible")
        
        # Check registry
        if self._registry:
            try:
                stats = self._registry.get_stats()
                if stats.total_known == 0:
                    issues.append("Registry not populated")
            except Exception as e:
                issues.append(f"Registry error: {e}")
        
        if issues:
            return HealthStatus(
                healthy=False,
                message="; ".join(issues),
            )
        
        return HealthStatus(healthy=True, message="Ready to accept traffic")
    
    def get_liveness(self) -> HealthStatus:
        """
        Kubernetes-style liveness probe.
        
        Returns True when the service is running and should not be restarted.
        Fails only on critical internal errors.
        """
        # Liveness should be permissive - only fail on critical errors
        # that indicate the process is stuck or corrupted
        
        try:
            # Check if we can access basic resources
            if not os.access(".", os.R_OK):
                return HealthStatus(healthy=False, message="Cannot access working directory")
            
            # Check for critical memory pressure
            memory = self._get_memory_info()
            if memory and memory.get("percent", 0) > 98:
                return HealthStatus(healthy=False, message="Critical memory pressure")
            
            return HealthStatus(healthy=True, message="Service is alive")
            
        except Exception as e:
            logger.error(f"Liveness check failed: {e}")
            return HealthStatus(healthy=False, message=f"Check error: {e}")
    
    def _check_database(self) -> ComponentHealth:
        """Check database connectivity."""
        import time
        start = time.time()
        
        if not self._db:
            return ComponentHealth(
                name="database",
                status=HealthState.DEGRADED,
                message="No database connection configured",
            )
        
        try:
            # Try a simple query
            if hasattr(self._db, 'execute'):
                self._db.execute("SELECT 1")
            elif hasattr(self._db, 'cursor'):
                cur = self._db.cursor()
                cur.execute("SELECT 1")
                cur.fetchone()
            
            latency = (time.time() - start) * 1000
            
            return ComponentHealth(
                name="database",
                status=HealthState.HEALTHY,
                message="Connected",
                latency_ms=latency,
            )
            
        except Exception as e:
            latency = (time.time() - start) * 1000
            return ComponentHealth(
                name="database",
                status=HealthState.UNHEALTHY,
                message=f"Connection failed: {e}",
                latency_ms=latency,
            )
    
    def _check_registry(self) -> ComponentHealth:
        """Check registry load status."""
        if not self._registry:
            return ComponentHealth(
                name="registry",
                status=HealthState.DEGRADED,
                message="No registry configured",
            )
        
        try:
            stats = self._registry.get_stats()
            
            if stats.total_known == 0:
                return ComponentHealth(
                    name="registry",
                    status=HealthState.DEGRADED,
                    message="Registry empty - may need initial load",
                    details=stats.as_dict(),
                )
            
            return ComponentHealth(
                name="registry",
                status=HealthState.HEALTHY,
                message=f"Loaded {stats.total_known} records",
                details=stats.as_dict(),
            )
            
        except Exception as e:
            return ComponentHealth(
                name="registry",
                status=HealthState.UNHEALTHY,
                message=f"Registry error: {e}",
            )
    
    def _check_disk_space(self) -> ComponentHealth:
        """Check available disk space."""
        try:
            path = self._metrics_path or "."
            usage = shutil.disk_usage(path)
            
            free_gb = usage.free / (1024**3)
            total_gb = usage.total / (1024**3)
            used_percent = (usage.used / usage.total) * 100
            
            details = {
                "free_gb": round(free_gb, 2),
                "total_gb": round(total_gb, 2),
                "used_percent": round(used_percent, 2),
            }
            
            if free_gb < self._min_disk_space_gb:
                return ComponentHealth(
                    name="disk",
                    status=HealthState.UNHEALTHY,
                    message=f"Low disk space: {free_gb:.1f}GB free",
                    details=details,
                )
            elif free_gb < self._min_disk_space_gb * 2:
                return ComponentHealth(
                    name="disk",
                    status=HealthState.DEGRADED,
                    message=f"Disk space warning: {free_gb:.1f}GB free",
                    details=details,
                )
            
            return ComponentHealth(
                name="disk",
                status=HealthState.HEALTHY,
                message=f"{free_gb:.1f}GB free",
                details=details,
            )
            
        except Exception as e:
            return ComponentHealth(
                name="disk",
                status=HealthState.DEGRADED,
                message=f"Cannot check disk: {e}",
            )
    
    def _check_memory(self) -> ComponentHealth:
        """Check memory usage."""
        memory = self._get_memory_info()
        
        if not memory:
            return ComponentHealth(
                name="memory",
                status=HealthState.DEGRADED,
                message="Cannot retrieve memory info",
            )
        
        percent = memory.get("percent", 0)
        details = {
            "used_mb": memory.get("used_mb"),
            "total_mb": memory.get("total_mb"),
            "percent": percent,
        }
        
        if percent > self._min_memory_percent:
            return ComponentHealth(
                name="memory",
                status=HealthState.UNHEALTHY,
                message=f"High memory usage: {percent:.1f}%",
                details=details,
            )
        elif percent > self._min_memory_percent * 0.8:
            return ComponentHealth(
                name="memory",
                status=HealthState.DEGRADED,
                message=f"Elevated memory usage: {percent:.1f}%",
                details=details,
            )
        
        return ComponentHealth(
            name="memory",
            status=HealthState.HEALTHY,
            message=f"{percent:.1f}% used",
            details=details,
        )
    
    def _check_recent_runs(self) -> ComponentHealth:
        """Check success rate of recent pipeline runs."""
        # This would typically query a database or metrics store
        # For now, check if metrics files exist and are recent
        
        try:
            import time
            metrics_file = os.path.join(self._metrics_path, "pipeline_runs.jsonl")
            
            if not os.path.exists(metrics_file):
                return ComponentHealth(
                    name="recent_runs",
                    status=HealthState.DEGRADED,
                    message="No run history found",
                )
            
            # Check if file has recent entries
            mtime = os.path.getmtime(metrics_file)
            age_hours = (time.time() - mtime) / 3600
            
            if age_hours > 24:
                return ComponentHealth(
                    name="recent_runs",
                    status=HealthState.DEGRADED,
                    message=f"No runs in {age_hours:.0f} hours",
                    details={"last_run_hours_ago": round(age_hours, 1)},
                )
            
            # Count recent successful runs
            # In production, query the database
            return ComponentHealth(
                name="recent_runs",
                status=HealthState.HEALTHY,
                message=f"Recent activity ({age_hours:.1f}h ago)",
                details={"last_run_hours_ago": round(age_hours, 1)},
            )
            
        except Exception as e:
            return ComponentHealth(
                name="recent_runs",
                status=HealthState.DEGRADED,
                message=f"Cannot check runs: {e}",
            )
    
    def _get_memory_info(self) -> Optional[dict]:
        """Get memory usage information."""
        try:
            import psutil
            mem = psutil.virtual_memory()
            return {
                "used_mb": mem.used // (1024 * 1024),
                "total_mb": mem.total // (1024 * 1024),
                "percent": mem.percent,
            }
        except ImportError:
            # Fallback for systems without psutil
            try:
                with open('/proc/meminfo', 'r') as f:
                    lines = f.readlines()
                
                mem_total = 0
                mem_available = 0
                
                for line in lines:
                    if line.startswith('MemTotal:'):
                        mem_total = int(line.split()[1]) // 1024
                    elif line.startswith('MemAvailable:'):
                        mem_available = int(line.split()[1]) // 1024
                
                if mem_total > 0:
                    used_mb = mem_total - mem_available
                    return {
                        "used_mb": used_mb,
                        "total_mb": mem_total,
                        "percent": (used_mb / mem_total) * 100,
                    }
            except Exception:
                pass
            
            return None
        except Exception:
            return None
