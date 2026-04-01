"""
Metrics and health checks for the coordinator.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json

from .models import ExtractionJob, Agent, GameType, JobStatus, CoordinatorStats
from .queue_manager import QueueManager
from .agent_manager import AgentManager

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """A single metric data point."""
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class MetricSeries:
    """A series of metric points with retention."""
    name: str
    description: str
    max_points: int = 1000
    points: deque = field(default_factory=lambda: deque(maxlen=1000))
    
    def add(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Add a point to the series."""
        self.points.append(MetricPoint(value, labels=labels or {}))
    
    def get_latest(self) -> Optional[MetricPoint]:
        """Get the most recent point."""
        return self.points[-1] if self.points else None
    
    def get_average(self, window_seconds: int = 300) -> float:
        """Get average over a time window."""
        cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
        values = [p.value for p in self.points if p.timestamp > cutoff]
        return sum(values) / len(values) if values else 0.0


class CoordinatorMetrics:
    """
    Collects and stores metrics for the coordinator.
    
    Tracks:
    - Job throughput
    - Queue depths
    - Agent performance
    - Error rates
    - Latency percentiles
    """
    
    def __init__(self, max_series_points: int = 1000):
        self.max_series_points = max_series_points
        self._series: Dict[str, MetricSeries] = {}
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._lock = asyncio.Lock()
        
        # Initialize standard series
        self._init_series()
    
    def _init_series(self):
        """Initialize standard metric series."""
        self._series["jobs_completed"] = MetricSeries(
            "jobs_completed", "Total jobs completed", self.max_series_points
        )
        self._series["jobs_failed"] = MetricSeries(
            "jobs_failed", "Total jobs failed", self.max_series_points
        )
        self._series["queue_depth_cs"] = MetricSeries(
            "queue_depth_cs", "CS queue depth", self.max_series_points
        )
        self._series["queue_depth_valorant"] = MetricSeries(
            "queue_depth_valorant", "Valorant queue depth", self.max_series_points
        )
        self._series["job_latency"] = MetricSeries(
            "job_latency", "Job processing latency (seconds)", self.max_series_points
        )
        self._series["agent_utilization"] = MetricSeries(
            "agent_utilization", "Percentage of busy agents", self.max_series_points
        )
    
    async def record_job_completed(
        self,
        job: ExtractionJob,
        duration_seconds: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """Record a completed job."""
        async with self._lock:
            self._counters["jobs_completed_total"] += 1
            self._series["jobs_completed"].add(1, labels)
            
            # Track by game
            game_key = f"jobs_completed_{job.game}"
            self._counters[game_key] += 1
            
            # Track latency
            self._series["job_latency"].add(duration_seconds, labels)
            self._histograms["job_latency"].append(duration_seconds)
            
            # Keep histogram bounded
            if len(self._histograms["job_latency"]) > 10000:
                self._histograms["job_latency"] = self._histograms["job_latency"][-5000:]
    
    async def record_job_failed(
        self,
        job: ExtractionJob,
        error: str,
        labels: Optional[Dict[str, str]] = None
    ):
        """Record a failed job."""
        async with self._lock:
            self._counters["jobs_failed_total"] += 1
            self._series["jobs_failed"].add(1, labels)
            
            # Track by game and error type
            game_key = f"jobs_failed_{job.game}"
            self._counters[game_key] += 1
            
            # Categorize error
            error_type = self._categorize_error(error)
            error_key = f"errors_{error_type}"
            self._counters[error_key] += 1
    
    def _categorize_error(self, error: str) -> str:
        """Categorize an error message."""
        error_lower = error.lower()
        
        if any(x in error_lower for x in ["timeout", "timed out"]):
            return "timeout"
        elif any(x in error_lower for x in ["rate limit", "429", "too many"]):
            return "rate_limit"
        elif any(x in error_lower for x in ["connection", "network", "dns"]):
            return "network"
        elif any(x in error_lower for x in ["parse", "json", "xml"]):
            return "parse"
        elif any(x in error_lower for x in ["not found", "404", "missing"]):
            return "not_found"
        else:
            return "unknown"
    
    async def update_queue_depth(self, game: GameType, depth: int):
        """Update queue depth gauge."""
        async with self._lock:
            series_name = f"queue_depth_{game.value}"
            if series_name in self._series:
                self._series[series_name].add(depth)
            self._gauges[f"queue_depth_{game}"] = float(depth)
    
    async def update_agent_utilization(self, busy: int, total: int):
        """Update agent utilization percentage."""
        async with self._lock:
            if total > 0:
                utilization = (busy / total) * 100
                self._series["agent_utilization"].add(utilization)
                self._gauges["agent_utilization_percent"] = utilization
                self._gauges["agents_busy"] = float(busy)
                self._gauges["agents_total"] = float(total)
    
    async def increment_counter(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        async with self._lock:
            self._counters[name] += value
    
    async def set_gauge(self, name: str, value: float):
        """Set a gauge metric."""
        async with self._lock:
            self._gauges[name] = value
    
    def get_counter(self, name: str) -> int:
        """Get counter value."""
        return self._counters.get(name, 0)
    
    def get_gauge(self, name: str) -> float:
        """Get gauge value."""
        return self._gauges.get(name, 0.0)
    
    def get_latency_percentiles(self) -> Dict[str, float]:
        """Calculate latency percentiles."""
        latencies = sorted(self._histograms["job_latency"])
        if not latencies:
            return {"p50": 0, "p95": 0, "p99": 0}
        
        n = len(latencies)
        return {
            "p50": latencies[int(n * 0.50)],
            "p95": latencies[int(n * 0.95)],
            "p99": latencies[int(n * 0.99)] if n >= 100 else latencies[-1]
        }
    
    def get_series(self, name: str) -> Optional[MetricSeries]:
        """Get a metric series by name."""
        return self._series.get(name)
    
    async def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metrics."""
        async with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "latency_percentiles": self.get_latency_percentiles(),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        
        # Counters
        for name, value in self._counters.items():
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")
        
        # Gauges
        for name, value in self._gauges.items():
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")
        
        return "\n".join(lines)


class HealthChecker:
    """
    Health check system for coordinator components.
    
    Monitors:
    - Queue depths
    - Agent heartbeats
    - Processing throughput
    - Error rates
    """
    
    def __init__(
        self,
        queue_manager: Optional[QueueManager] = None,
        agent_manager: Optional[AgentManager] = None,
        metrics: Optional[CoordinatorMetrics] = None,
        check_interval_seconds: int = 30
    ):
        self.queue_manager = queue_manager
        self.agent_manager = agent_manager
        self.metrics = metrics
        self.check_interval = check_interval_seconds
        
        self._checks: List[Callable] = []
        self._alerts: List[Dict] = []
        self._alert_handlers: List[Callable] = []
        self._monitor_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        # Thresholds
        self.max_queue_depth = 1000
        self.max_error_rate = 0.1  # 10%
        self.min_throughput = 1  # jobs per minute
    
    async def start(self):
        """Start health monitoring."""
        if self._monitor_task is None:
            self._shutdown_event.clear()
            self._monitor_task = asyncio.create_task(self._monitor_loop())
            logger.info("Health checker started")
    
    async def stop(self):
        """Stop health monitoring."""
        self._shutdown_event.set()
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
            logger.info("Health checker stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=self.check_interval
                )
            except asyncio.TimeoutError:
                pass
            
            if self._shutdown_event.is_set():
                break
            
            await self._run_checks()
    
    async def _run_checks(self):
        """Run all health checks."""
        results = []
        
        for check in self._checks:
            try:
                result = await check()
                results.append(result)
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                results.append({
                    "name": check.__name__,
                    "status": "error",
                    "message": str(e)
                })
        
        # Check for alerts
        await self._check_alerts(results)
    
    async def _check_alerts(self, results: List[Dict]):
        """Check for alert conditions."""
        alerts = []
        
        for result in results:
            if result.get("status") != "healthy":
                alert = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "check": result.get("name"),
                    "severity": result.get("severity", "warning"),
                    "message": result.get("message"),
                    "details": result.get("details", {})
                }
                alerts.append(alert)
                
                # Trigger handlers
                for handler in self._alert_handlers:
                    try:
                        await handler(alert)
                    except Exception as e:
                        logger.error(f"Alert handler error: {e}")
        
        self._alerts.extend(alerts)
        
        # Keep only recent alerts
        cutoff = datetime.utcnow() - timedelta(hours=24)
        self._alerts = [
            a for a in self._alerts
            if datetime.fromisoformat(a["timestamp"]) > cutoff
        ]
    
    def register_check(self, check: Callable):
        """Register a custom health check."""
        self._checks.append(check)
    
    def on_alert(self, handler: Callable):
        """Register an alert handler."""
        self._alert_handlers.append(handler)
    
    async def check_queue_health(self) -> Dict:
        """Check queue health."""
        if not self.queue_manager:
            return {"name": "queue", "status": "unknown", "message": "No queue manager"}
        
        stats = self.queue_manager.get_queue_stats()
        
        cs_pending = stats["cs"]["pending"]
        val_pending = stats["valorant"]["pending"]
        total_pending = cs_pending + val_pending
        
        if total_pending > self.max_queue_depth:
            return {
                "name": "queue",
                "status": "unhealthy",
                "severity": "critical",
                "message": f"Queue depth critical: {total_pending} pending jobs",
                "details": stats
            }
        elif total_pending > self.max_queue_depth * 0.7:
            return {
                "name": "queue",
                "status": "degraded",
                "severity": "warning",
                "message": f"Queue depth high: {total_pending} pending jobs",
                "details": stats
            }
        
        return {
            "name": "queue",
            "status": "healthy",
            "message": f"Queue depth normal: {total_pending} pending jobs",
            "details": stats
        }
    
    async def check_agent_health(self) -> Dict:
        """Check agent health."""
        if not self.agent_manager:
            return {"name": "agents", "status": "unknown", "message": "No agent manager"}
        
        stats = self.agent_manager.get_agent_stats()
        total = stats.get("total", 0)
        idle = stats.get("idle", 0)
        offline = stats.get("offline", 0)
        
        if total == 0:
            return {
                "name": "agents",
                "status": "unhealthy",
                "severity": "critical",
                "message": "No agents registered",
                "details": stats
            }
        
        if offline == total:
            return {
                "name": "agents",
                "status": "unhealthy",
                "severity": "critical",
                "message": "All agents offline",
                "details": stats
            }
        
        if idle == 0 and stats.get("busy", 0) > 0:
            return {
                "name": "agents",
                "status": "degraded",
                "severity": "warning",
                "message": "No idle agents available",
                "details": stats
            }
        
        return {
            "name": "agents",
            "status": "healthy",
            "message": f"{idle}/{total} agents idle, {offline} offline",
            "details": stats
        }
    
    async def check_throughput(self) -> Dict:
        """Check processing throughput."""
        if not self.metrics:
            return {"name": "throughput", "status": "unknown", "message": "No metrics"}
        
        # Calculate recent throughput
        series = self.metrics.get_series("jobs_completed")
        if not series:
            return {"name": "throughput", "status": "unknown", "message": "No throughput data"}
        
        recent = series.get_average(300)  # 5 minute window
        
        if recent < self.min_throughput:
            return {
                "name": "throughput",
                "status": "degraded",
                "severity": "warning",
                "message": f"Low throughput: {recent:.2f} jobs/min",
                "details": {"recent_jobs_per_minute": recent}
            }
        
        return {
            "name": "throughput",
            "status": "healthy",
            "message": f"Throughput normal: {recent:.2f} jobs/min",
            "details": {"recent_jobs_per_minute": recent}
        }
    
    async def check_error_rate(self) -> Dict:
        """Check error rate."""
        if not self.metrics:
            return {"name": "error_rate", "status": "unknown", "message": "No metrics"}
        
        completed = self.metrics.get_counter("jobs_completed_total")
        failed = self.metrics.get_counter("jobs_failed_total")
        
        total = completed + failed
        if total == 0:
            return {
                "name": "error_rate",
                "status": "healthy",
                "message": "No jobs processed yet"
            }
        
        error_rate = failed / total
        
        if error_rate > self.max_error_rate:
            return {
                "name": "error_rate",
                "status": "unhealthy",
                "severity": "critical",
                "message": f"High error rate: {error_rate:.1%} ({failed}/{total})",
                "details": {"error_rate": error_rate, "failed": failed, "completed": completed}
            }
        
        return {
            "name": "error_rate",
            "status": "healthy",
            "message": f"Error rate normal: {error_rate:.1%}",
            "details": {"error_rate": error_rate, "failed": failed, "completed": completed}
        }
    
    async def get_health_summary(self) -> Dict[str, Any]:
        """Get complete health summary."""
        checks = [
            await self.check_queue_health(),
            await self.check_agent_health(),
            await self.check_throughput(),
            await self.check_error_rate()
        ]
        
        statuses = [c.get("status") for c in checks]
        
        if any(s == "unhealthy" for s in statuses):
            overall = "unhealthy"
        elif any(s == "degraded" for s in statuses):
            overall = "degraded"
        elif all(s == "healthy" for s in statuses):
            overall = "healthy"
        else:
            overall = "unknown"
        
        return {
            "status": overall,
            "checks": checks,
            "alerts": self._alerts[-10:],  # Last 10 alerts
            "timestamp": datetime.utcnow().isoformat()
        }


# Convenience functions for common monitoring scenarios
async def record_job_metrics(
    metrics: CoordinatorMetrics,
    job: ExtractionJob,
    start_time: datetime,
    success: bool,
    error: Optional[str] = None
):
    """Record metrics for a job completion."""
    duration = (datetime.utcnow() - start_time).total_seconds()
    
    labels = {
        "game": job.game.value if isinstance(job.game, GameType) else str(job.game),
        "source": job.source,
        "job_type": job.job_type
    }
    
    if success:
        await metrics.record_job_completed(job, duration, labels)
    else:
        await metrics.record_job_failed(job, error or "Unknown", labels)
