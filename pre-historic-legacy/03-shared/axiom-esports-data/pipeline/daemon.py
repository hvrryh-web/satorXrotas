"""
Pipeline Daemon
===============

Background service that:
- Runs scheduled jobs
- Handles webhooks
- Maintains run history
- Exposes health endpoint
"""

import asyncio
import json
import logging
import signal
import sys
import time
from datetime import datetime
from typing import Optional
from uuid import uuid4

from pipeline.config import PipelineConfig
from pipeline.models import HealthStatus, TriggerType
from pipeline.runner import PipelineRunner
from pipeline.scheduler import PipelineScheduler
from pipeline.state_store import StateStore

try:
    from aiohttp import web
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    web = None

logger = logging.getLogger(__name__)


class PipelineDaemon:
    """
    Background service that:
    - Runs scheduled jobs
    - Handles webhooks
    - Maintains run history
    - Exposes health endpoint
    """
    
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8080,
        database_url: Optional[str] = None,
    ):
        self.host = host
        self.port = port
        self.database_url = database_url
        
        self.state_store: Optional[StateStore] = None
        self.runner: Optional[PipelineRunner] = None
        self.scheduler: Optional[PipelineScheduler] = None
        self.web_app: Optional[web.Application] = None
        self.web_runner: Optional[web.AppRunner] = None
        
        self._shutdown_event = asyncio.Event()
        self._started_at: Optional[datetime] = None
        self._tasks: list[asyncio.Task] = []
        self._daemon_id = str(uuid4())[:8]
    
    async def start(self) -> None:
        """Start the daemon."""
        self._started_at = datetime.utcnow()
        
        # Setup logging
        self._setup_logging()
        
        logger.info(f"Starting PipelineDaemon [{self._daemon_id}]...")
        
        # Initialize state store
        self.state_store = StateStore(database_url=self.database_url)
        await self.state_store.connect()
        
        # Initialize schema
        try:
            await self.state_store.initialize_schema()
        except Exception as e:
            logger.warning(f"Schema initialization may have failed: {e}")
        
        # Initialize runner
        self.runner = PipelineRunner(state_store=self.state_store)
        
        # Initialize scheduler
        self.scheduler = PipelineScheduler(
            state_store=self.state_store,
            runner=self.runner,
        )
        await self.scheduler.load_jobs()
        
        # Start web server if aiohttp available
        if AIOHTTP_AVAILABLE:
            await self._start_web_server()
        else:
            logger.warning("aiohttp not installed, web server will not start")
        
        # Start scheduler loop
        scheduler_task = asyncio.create_task(self.scheduler.run_scheduler_loop())
        self._tasks.append(scheduler_task)
        
        # Start metrics collection
        metrics_task = asyncio.create_task(self._metrics_loop())
        self._tasks.append(metrics_task)
        
        logger.info(f"PipelineDaemon [{self._daemon_id}] started on {self.host}:{self.port}")
        
        # Wait for shutdown signal
        try:
            await self._shutdown_event.wait()
        except asyncio.CancelledError:
            pass
        
        await self.stop()
    
    async def stop(self) -> None:
        """Graceful shutdown."""
        logger.info(f"Stopping PipelineDaemon [{self._daemon_id}]...")
        
        self._shutdown_event.set()
        
        # Stop scheduler
        if self.scheduler:
            self.scheduler.stop()
        
        # Cancel all tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()
        
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        # Stop runner
        if self.runner:
            await self.runner.shutdown()
        
        # Stop web server
        if self.web_runner:
            await self.web_runner.cleanup()
        
        # Disconnect from database
        if self.state_store:
            await self.state_store.disconnect()
        
        logger.info(f"PipelineDaemon [{self._daemon_id}] stopped")
    
    async def _start_web_server(self) -> None:
        """Start the web server for health checks and webhooks."""
        self.web_app = web.Application()
        
        # Routes
        self.web_app.router.add_get("/health", self._handle_health)
        self.web_app.router.add_get("/status", self._handle_status)
        self.web_app.router.add_post("/webhook/{secret}", self._handle_webhook)
        self.web_app.router.add_post("/trigger/manual", self._handle_manual_trigger)
        self.web_app.router.add_get("/runs", self._handle_list_runs)
        self.web_app.router.add_get("/runs/{run_id}", self._handle_get_run)
        self.web_app.router.add_get("/runs/{run_id}/logs", self._handle_get_run_logs)
        self.web_app.router.add_post("/runs/{run_id}/cancel", self._handle_cancel_run)
        self.web_app.router.add_get("/jobs", self._handle_list_jobs)
        self.web_app.router.add_post("/jobs/{job_id}/pause", self._handle_pause_job)
        self.web_app.router.add_post("/jobs/{job_id}/resume", self._handle_resume_job)
        
        self.web_runner = web.AppRunner(self.web_app)
        await self.web_runner.setup()
        
        site = web.TCPSite(self.web_runner, self.host, self.port)
        await site.start()
        
        logger.info(f"Web server started on http://{self.host}:{self.port}")
    
    # Web handlers
    async def _handle_health(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        health = await self.health_check()
        status = 200 if health.status == "healthy" else 503
        return web.json_response(health.to_dict(), status=status)
    
    async def _handle_status(self, request: web.Request) -> web.Response:
        """Detailed status endpoint."""
        health = await self.health_check()
        
        # Get recent runs
        runs = []
        if self.runner:
            runs = await self.runner.list_runs(limit=5)
        
        # Get scheduled jobs
        jobs = []
        if self.scheduler:
            jobs = await self.scheduler.list_scheduled_jobs()
        
        status = {
            "daemon_id": self._daemon_id,
            "health": health.to_dict(),
            "recent_runs": [r.to_dict() for r in runs],
            "scheduled_jobs": [j.to_dict() for j in jobs],
        }
        
        return web.json_response(status)
    
    async def _handle_webhook(self, request: web.Request) -> web.Response:
        """Webhook trigger endpoint."""
        secret = request.match_info["secret"]
        
        try:
            payload = await request.json()
        except json.JSONDecodeError:
            payload = {}
        
        # Get signature from header
        signature = request.headers.get("X-Webhook-Signature")
        
        if not self.scheduler:
            return web.json_response({"error": "Scheduler not available"}, status=503)
        
        try:
            run_id = await self.scheduler.trigger_webhook(
                webhook_secret=secret,
                payload=payload,
                signature=signature,
            )
            return web.json_response({"run_id": run_id, "status": "triggered"})
        except PermissionError:
            return web.json_response({"error": "Invalid signature"}, status=401)
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=404)
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def _handle_manual_trigger(self, request: web.Request) -> web.Response:
        """Manual trigger endpoint."""
        try:
            body = await request.json()
        except json.JSONDecodeError:
            body = {}
        
        pipeline_args = body.get("pipeline_args", {})
        
        if not self.scheduler:
            return web.json_response({"error": "Scheduler not available"}, status=503)
        
        try:
            run_id = await self.scheduler.trigger_manual(pipeline_args)
            return web.json_response({"run_id": run_id, "status": "triggered"})
        except Exception as e:
            logger.error(f"Manual trigger error: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def _handle_list_runs(self, request: web.Request) -> web.Response:
        """List recent runs."""
        limit = int(request.query.get("limit", 10))
        
        if not self.runner:
            return web.json_response({"error": "Runner not available"}, status=503)
        
        runs = await self.runner.list_runs(limit=limit)
        return web.json_response({"runs": [r.to_dict() for r in runs]})
    
    async def _handle_get_run(self, request: web.Request) -> web.Response:
        """Get run details."""
        run_id = request.match_info["run_id"]
        
        if not self.state_store:
            return web.json_response({"error": "State store not available"}, status=503)
        
        run = await self.state_store.load_run(run_id)
        if not run:
            return web.json_response({"error": "Run not found"}, status=404)
        
        return web.json_response(run.to_dict())
    
    async def _handle_get_run_logs(self, request: web.Request) -> web.Response:
        """Get run logs."""
        run_id = request.match_info["run_id"]
        
        if not self.runner:
            return web.json_response({"error": "Runner not available"}, status=503)
        
        logs = await self.runner.get_run_logs(run_id)
        return web.json_response({"logs": [log.to_dict() for log in logs]})
    
    async def _handle_cancel_run(self, request: web.Request) -> web.Response:
        """Cancel a run."""
        run_id = request.match_info["run_id"]
        
        if not self.runner:
            return web.json_response({"error": "Runner not available"}, status=503)
        
        success = await self.runner.cancel_run(run_id)
        if success:
            return web.json_response({"run_id": run_id, "status": "cancelled"})
        else:
            return web.json_response({"error": "Run not found or already completed"}, status=404)
    
    async def _handle_list_jobs(self, request: web.Request) -> web.Response:
        """List scheduled jobs."""
        if not self.scheduler:
            return web.json_response({"error": "Scheduler not available"}, status=503)
        
        jobs = await self.scheduler.list_scheduled_jobs()
        return web.json_response({"jobs": [j.to_dict() for j in jobs]})
    
    async def _handle_pause_job(self, request: web.Request) -> web.Response:
        """Pause a scheduled job."""
        job_id = request.match_info["job_id"]
        
        if not self.scheduler:
            return web.json_response({"error": "Scheduler not available"}, status=503)
        
        success = await self.scheduler.pause_job(job_id)
        if success:
            return web.json_response({"job_id": job_id, "status": "paused"})
        else:
            return web.json_response({"error": "Job not found"}, status=404)
    
    async def _handle_resume_job(self, request: web.Request) -> web.Response:
        """Resume a scheduled job."""
        job_id = request.match_info["job_id"]
        
        if not self.scheduler:
            return web.json_response({"error": "Scheduler not available"}, status=503)
        
        success = await self.scheduler.resume_job(job_id)
        if success:
            return web.json_response({"job_id": job_id, "status": "resumed"})
        else:
            return web.json_response({"error": "Job not found"}, status=404)
    
    async def health_check(self) -> HealthStatus:
        """Return health status for monitoring."""
        now = datetime.utcnow()
        uptime_seconds = (
            (now - self._started_at).total_seconds()
            if self._started_at else 0
        )
        
        checks = {}
        
        # Check database
        if self.state_store and self.state_store.pool:
            try:
                async with self.state_store.pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                checks["database"] = "ok"
            except Exception as e:
                checks["database"] = f"error: {e}"
        else:
            checks["database"] = "not_connected"
        
        # Check runner
        checks["runner"] = "ok" if self.runner else "not_initialized"
        
        # Check scheduler
        checks["scheduler"] = "ok" if self.scheduler else "not_initialized"
        
        # Determine overall status
        if all(v == "ok" for v in checks.values()):
            status = "healthy"
        elif checks.get("database") != "ok":
            status = "unhealthy"
        else:
            status = "degraded"
        
        # Count active runs
        active_runs = 0
        queued_runs = 0
        if self.runner:
            active_runs = len(self.runner._active_runs)
        
        scheduled_jobs = 0
        if self.scheduler:
            scheduled_jobs = len(self.scheduler._scheduled_jobs)
        
        return HealthStatus(
            status=status,
            version="1.0.0",
            uptime_seconds=uptime_seconds,
            active_runs=active_runs,
            queued_runs=queued_runs,
            scheduled_jobs=scheduled_jobs,
            last_check_at=now,
            checks=checks,
        )
    
    async def _metrics_loop(self) -> None:
        """Periodic metrics collection."""
        while not self._shutdown_event.is_set():
            try:
                await self._collect_metrics()
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
            
            # Collect every minute
            for _ in range(60):
                if self._shutdown_event.is_set():
                    break
                await asyncio.sleep(1)
    
    async def _collect_metrics(self) -> None:
        """Collect and store daemon metrics."""
        if not self.state_store:
            return
        
        health = await self.health_check()
        
        metric_value = {
            "uptime_seconds": health.uptime_seconds,
            "active_runs": health.active_runs,
            "scheduled_jobs": health.scheduled_jobs,
            "checks": health.checks,
        }
        
        try:
            async with self.state_store.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO pipeline_daemon_metrics 
                    (daemon_id, metric_type, metric_value)
                    VALUES ($1, $2, $3)
                    """,
                    self._daemon_id,
                    "health",
                    json.dumps(metric_value),
                )
        except Exception as e:
            logger.error(f"Failed to store metrics: {e}")
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout),
            ],
        )


def main():
    """Entry point for running the daemon."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Pipeline Daemon")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--database-url", help="Database URL")
    parser.add_argument("--log-level", default="INFO", help="Log level")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    daemon = PipelineDaemon(
        host=args.host,
        port=args.port,
        database_url=args.database_url,
    )
    
    # Setup signal handlers
    loop = asyncio.get_event_loop()
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(daemon.stop()))
    
    try:
        loop.run_until_complete(daemon.start())
    except KeyboardInterrupt:
        loop.run_until_complete(daemon.stop())
    finally:
        loop.close()


if __name__ == "__main__":
    main()
