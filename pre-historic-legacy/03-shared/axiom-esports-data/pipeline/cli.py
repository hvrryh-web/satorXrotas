"""
Pipeline CLI
============

Rich CLI for pipeline management using Click.
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from typing import Optional
from uuid import UUID

import click
from click import echo, style

# Import pipeline modules
try:
    from pipeline.config import PipelineConfig
    from pipeline.daemon import PipelineDaemon
    from pipeline.models import JobStatus, RunStatus, TriggerType
    from pipeline.runner import PipelineRunner
    from pipeline.scheduler import PipelineScheduler
    from pipeline.state_store import StateStore
except ImportError as e:
    echo(style(f"Error importing pipeline modules: {e}", fg="red"))
    sys.exit(1)


# Helper for running async functions
def async_cmd(f):
    """Decorator to run async click commands."""
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper


# CLI Group
@click.group()
@click.option("--config", "-c", help="Path to config file")
@click.option("--database-url", "-d", envvar="DATABASE_URL", help="Database URL")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
def cli(ctx, config, database_url, verbose):
    """Axiom Pipeline CLI - Manage and run data pipelines."""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config
    ctx.obj["database_url"] = database_url
    ctx.obj["verbose"] = verbose


# Run command
@cli.command()
@click.option("--mode", "-m", default="delta", type=click.Choice(["delta", "full", "backfill"]),
              help="Pipeline mode")
@click.option("--epochs", "-e", default="1,2,3", help="Epochs to process (comma-separated)")
@click.option("--batch-size", "-b", type=int, default=100, help="Batch size")
@click.option("--max-workers", "-w", type=int, default=3, help="Max workers")
@click.option("--follow", "-f", is_flag=True, help="Follow logs")
@click.pass_context
@async_cmd
async def run(ctx, mode, epochs, batch_size, max_workers, follow):
    """Run the pipeline."""
    database_url = ctx.obj["database_url"]
    
    # Parse epochs
    epoch_list = [int(e.strip()) for e in epochs.split(",")]
    
    # Create config
    config = PipelineConfig(
        mode=mode,
        epochs=epoch_list,
        batch_size=batch_size,
        max_workers=max_workers,
        database_url=database_url,
    )
    
    echo(style(f"Starting pipeline run (mode={mode}, epochs={epoch_list})", fg="blue", bold=True))
    
    # Setup state store
    state_store = None
    if database_url:
        state_store = StateStore(database_url=database_url)
        await state_store.connect()
    
    # Create runner
    runner = PipelineRunner(state_store=state_store)
    
    # Start run
    run_instance = await runner.start_run(
        config=config,
        trigger_type=TriggerType.MANUAL,
    )
    
    echo(style(f"Run ID: {run_instance.run_id}", fg="green"))
    
    if follow:
        echo(style("\nFollowing logs... (Ctrl+C to stop following)\n", fg="cyan"))
        try:
            last_log_count = 0
            while run_instance.status in (RunStatus.PENDING, RunStatus.RUNNING):
                await asyncio.sleep(1)
                
                # Get current run status
                current_run = runner.get_run(run_instance.run_id)
                if current_run:
                    # Print new logs
                    new_logs = current_run.logs[last_log_count:]
                    for log in new_logs:
                        color = {
                            "DEBUG": "dim",
                            "INFO": "white",
                            "WARNING": "yellow",
                            "ERROR": "red",
                            "CRITICAL": "red",
                        }.get(log.level, "white")
                        echo(f"[{log.timestamp.strftime('%H:%M:%S')}] "
                             f"[{style(log.level, fg=color)}] {log.message}")
                    last_log_count = len(current_run.logs)
                    run_instance = current_run
        except KeyboardInterrupt:
            echo(style("\nStopping log follow...", fg="yellow"))
    else:
        # Wait for completion
        while run_instance.status in (RunStatus.PENDING, RunStatus.RUNNING):
            await asyncio.sleep(0.5)
            current_run = runner.get_run(run_instance.run_id)
            if current_run:
                run_instance = current_run
    
    # Final status
    echo()
    if run_instance.status == RunStatus.COMPLETED:
        echo(style(f"✓ Pipeline completed successfully", fg="green", bold=True))
        echo(f"  Records processed: {run_instance.metrics.records_processed}")
        echo(f"  Records failed: {run_instance.metrics.records_failed}")
        echo(f"  Duration: {run_instance.metrics.duration_seconds:.2f}s")
    elif run_instance.status == RunStatus.FAILED:
        echo(style(f"✗ Pipeline failed", fg="red", bold=True))
        if run_instance.error_message:
            echo(f"  Error: {run_instance.error_message}")
    elif run_instance.status == RunStatus.CANCELLED:
        echo(style(f"⚠ Pipeline cancelled", fg="yellow", bold=True))
    
    if state_store:
        await state_store.disconnect()


# Schedule group
@cli.group()
def schedule():
    """Manage scheduled jobs."""
    pass


@schedule.command("add")
@click.option("--name", "-n", required=True, help="Job name")
@click.option("--cron", "-c", required=True, help="Cron expression (e.g., '0 6 * * *')")
@click.option("--mode", "-m", default="delta", type=click.Choice(["delta", "full", "backfill"]))
@click.option("--epochs", "-e", default="1,2,3", help="Epochs to process")
@click.option("--description", "-d", default="", help="Job description")
@click.option("--webhook", is_flag=True, help="Create webhook job instead of cron")
@click.option("--event-type", help="Event type for event-based jobs")
@click.pass_context
@async_cmd
async def schedule_add(ctx, name, cron, mode, epochs, description, webhook, event_type):
    """Add a scheduled job."""
    database_url = ctx.obj["database_url"]
    
    if not database_url:
        echo(style("Error: DATABASE_URL required for scheduling", fg="red"))
        return
    
    epoch_list = [int(e.strip()) for e in epochs.split(",")]
    pipeline_args = {"mode": mode, "epochs": epoch_list}
    
    state_store = StateStore(database_url=database_url)
    await state_store.connect()
    
    scheduler = PipelineScheduler(state_store=state_store)
    
    try:
        if webhook:
            job = await scheduler.create_webhook_job(
                name=name,
                pipeline_args=pipeline_args,
                description=description or f"Webhook job: {name}",
            )
            echo(style(f"✓ Created webhook job '{name}'", fg="green", bold=True))
            echo(f"  Job ID: {job.job_id}")
            echo(f"  Webhook Secret: {job.webhook_secret}")
            echo(f"  Webhook URL: /webhook/{job.webhook_secret}")
        elif event_type:
            job = await scheduler.create_event_job(
                name=name,
                event_filter={"type": event_type},
                pipeline_args=pipeline_args,
                description=description or f"Event job: {name}",
            )
            echo(style(f"✓ Created event job '{name}'", fg="green", bold=True))
            echo(f"  Job ID: {job.job_id}")
            echo(f"  Event Type: {event_type}")
        else:
            job = await scheduler.schedule_cron(
                name=name,
                cron=cron,
                pipeline_args=pipeline_args,
                description=description,
            )
            echo(style(f"✓ Created cron job '{name}'", fg="green", bold=True))
            echo(f"  Job ID: {job.job_id}")
            echo(f"  Cron: {cron}")
            echo(f"  Next run: {job.next_run_at}")
    except Exception as e:
        echo(style(f"Error: {e}", fg="red"))
    finally:
        await state_store.disconnect()


@schedule.command("list")
@click.option("--status", type=click.Choice(["active", "paused", "disabled", "error"]))
@click.pass_context
@async_cmd
async def schedule_list(ctx, status):
    """List scheduled jobs."""
    database_url = ctx.obj["database_url"]
    
    if not database_url:
        echo(style("Error: DATABASE_URL required", fg="red"))
        return
    
    state_store = StateStore(database_url=database_url)
    await state_store.connect()
    
    scheduler = PipelineScheduler(state_store=state_store)
    await scheduler.load_jobs()
    
    job_status = JobStatus(status) if status else None
    jobs = await scheduler.list_scheduled_jobs()
    
    if job_status:
        jobs = [j for j in jobs if j.status == job_status]
    
    if not jobs:
        echo(style("No scheduled jobs found", fg="yellow"))
        await state_store.disconnect()
        return
    
    echo(style(f"{'Name':<20} {'Type':<10} {'Status':<10} {'Schedule':<20} {'Next Run'}", fg="blue", bold=True))
    echo("-" * 80)
    
    for job in jobs:
        status_color = {
            JobStatus.ACTIVE: "green",
            JobStatus.PAUSED: "yellow",
            JobStatus.DISABLED: "dim",
            JobStatus.ERROR: "red",
        }.get(job.status, "white")
        
        schedule_str = job.cron_expression or "-"
        if job.trigger_type == TriggerType.WEBHOOK:
            schedule_str = "webhook"
        elif job.trigger_type == TriggerType.EVENT:
            schedule_str = f"event:{job.event_filter.get('type', '-')}" if job.event_filter else "event"
        
        next_run = job.next_run_at.strftime("%Y-%m-%d %H:%M") if job.next_run_at else "-"
        
        echo(f"{job.name:<20} {job.trigger_type.value:<10} "
             f"{style(job.status.value, fg=status_color):<10} "
             f"{schedule_str:<20} {next_run}")
    
    echo()
    echo(f"Total: {len(jobs)} job(s)")
    
    await state_store.disconnect()


@schedule.command("pause")
@click.option("--name", "-n", help="Job name")
@click.option("--job-id", "-i", help="Job ID")
@click.pass_context
@async_cmd
async def schedule_pause(ctx, name, job_id):
    """Pause a scheduled job."""
    database_url = ctx.obj["database_url"]
    
    if not database_url:
        echo(style("Error: DATABASE_URL required", fg="red"))
        return
    
    if not name and not job_id:
        echo(style("Error: Either --name or --job-id required", fg="red"))
        return
    
    state_store = StateStore(database_url=database_url)
    await state_store.connect()
    
    scheduler = PipelineScheduler(state_store=state_store)
    await scheduler.load_jobs()
    
    try:
        if name:
            job = await scheduler.get_job_by_name(name)
            if not job:
                echo(style(f"Job '{name}' not found", fg="red"))
                return
            job_id = job.job_id
        
        success = await scheduler.pause_job(job_id)
        if success:
            echo(style(f"✓ Job paused", fg="green"))
        else:
            echo(style(f"Job not found", fg="red"))
    except Exception as e:
        echo(style(f"Error: {e}", fg="red"))
    finally:
        await state_store.disconnect()


@schedule.command("resume")
@click.option("--name", "-n", help="Job name")
@click.option("--job-id", "-i", help="Job ID")
@click.pass_context
@async_cmd
async def schedule_resume(ctx, name, job_id):
    """Resume a paused job."""
    database_url = ctx.obj["database_url"]
    
    if not database_url:
        echo(style("Error: DATABASE_URL required", fg="red"))
        return
    
    if not name and not job_id:
        echo(style("Error: Either --name or --job-id required", fg="red"))
        return
    
    state_store = StateStore(database_url=database_url)
    await state_store.connect()
    
    scheduler = PipelineScheduler(state_store=state_store)
    await scheduler.load_jobs()
    
    try:
        if name:
            job = await scheduler.get_job_by_name(name)
            if not job:
                echo(style(f"Job '{name}' not found", fg="red"))
                return
            job_id = job.job_id
        
        success = await scheduler.resume_job(job_id)
        if success:
            echo(style(f"✓ Job resumed", fg="green"))
        else:
            echo(style(f"Job not found", fg="red"))
    except Exception as e:
        echo(style(f"Error: {e}", fg="red"))
    finally:
        await state_store.disconnect()


@schedule.command("delete")
@click.option("--name", "-n", help="Job name")
@click.option("--job-id", "-i", help="Job ID")
@click.confirmation_option(prompt="Are you sure you want to delete this job?")
@click.pass_context
@async_cmd
async def schedule_delete(ctx, name, job_id):
    """Delete a scheduled job."""
    database_url = ctx.obj["database_url"]
    
    if not database_url:
        echo(style("Error: DATABASE_URL required", fg="red"))
        return
    
    if not name and not job_id:
        echo(style("Error: Either --name or --job-id required", fg="red"))
        return
    
    state_store = StateStore(database_url=database_url)
    await state_store.connect()
    
    scheduler = PipelineScheduler(state_store=state_store)
    await scheduler.load_jobs()
    
    try:
        if name:
            job = await scheduler.get_job_by_name(name)
            if not job:
                echo(style(f"Job '{name}' not found", fg="red"))
                return
            job_id = job.job_id
        
        success = await scheduler.delete_job(job_id)
        if success:
            echo(style(f"✓ Job deleted", fg="green"))
        else:
            echo(style(f"Job not found", fg="red"))
    except Exception as e:
        echo(style(f"Error: {e}", fg="red"))
    finally:
        await state_store.disconnect()


# Status command
@cli.command()
@click.pass_context
@async_cmd
async def status(ctx):
    """Check pipeline status."""
    database_url = ctx.obj["database_url"]
    
    echo(style("Pipeline Status", fg="blue", bold=True))
    echo("-" * 40)
    
    if database_url:
        state_store = StateStore(database_url=database_url)
        await state_store.connect()
        
        try:
            # Get recent runs
            runs = await state_store.list_runs(limit=5)
            jobs = await state_store.list_scheduled_jobs()
            
            # Count by status
            run_counts = {}
            for run in runs:
                run_counts[run.status] = run_counts.get(run.status, 0) + 1
            
            job_counts = {}
            for job in jobs:
                job_counts[job.status.value] = job_counts.get(job.status.value, 0) + 1
            
            echo(style("Recent Runs:", fg="cyan"))
            if runs:
                for run in runs[:3]:
                    status_color = {
                        "completed": "green",
                        "failed": "red",
                        "running": "blue",
                        "pending": "yellow",
                        "cancelled": "dim",
                    }.get(run.status, "white")
                    
                    echo(f"  {run.run_id[:8]}... "
                         f"[{style(run.status, fg=status_color)}] "
                         f"{run.trigger_type} "
                         f"({run.records_processed} processed)")
            else:
                echo("  No recent runs")
            
            echo()
            echo(style("Scheduled Jobs:", fg="cyan"))
            if jobs:
                for status, count in sorted(job_counts.items()):
                    echo(f"  {status}: {count}")
            else:
                echo("  No scheduled jobs")
                
        finally:
            await state_store.disconnect()
    else:
        echo(style("DATABASE_URL not set - showing local status only", fg="yellow"))


# Logs command
@cli.command()
@click.option("--run-id", "-r", required=True, help="Run ID")
@click.option("--follow", "-f", is_flag=True, help="Follow logs")
@click.option("--lines", "-n", type=int, default=100, help="Number of lines to show")
@click.pass_context
@async_cmd
async def logs(ctx, run_id, follow, lines):
    """View logs for a run."""
    database_url = ctx.obj["database_url"]
    
    if not database_url:
        echo(style("Error: DATABASE_URL required", fg="red"))
        return
    
    state_store = StateStore(database_url=database_url)
    await state_store.connect()
    
    runner = PipelineRunner(state_store=state_store)
    
    try:
        # Check if run exists
        run = await state_store.load_run(run_id)
        if not run:
            echo(style(f"Run '{run_id}' not found", fg="red"))
            return
        
        if follow:
            echo(style(f"Following logs for run {run_id[:8]}... (Ctrl+C to stop)\n", fg="cyan"))
            displayed = 0
            try:
                while True:
                    logs = await runner.get_run_logs(run_id)
                    new_logs = logs[displayed:]
                    
                    for log in new_logs:
                        color = {
                            "DEBUG": "dim",
                            "INFO": "white",
                            "WARNING": "yellow",
                            "ERROR": "red",
                            "CRITICAL": "red",
                        }.get(log.level, "white")
                        echo(f"[{log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] "
                             f"[{style(log.level, fg=color)}] {log.message}")
                    
                    displayed = len(logs)
                    
                    # Stop if run completed
                    if run.status not in (RunStatus.PENDING.value, RunStatus.RUNNING.value):
                        run = await state_store.load_run(run_id)
                        if run.status not in (RunStatus.PENDING, RunStatus.RUNNING):
                            break
                    
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                echo(style("\nStopped following logs", fg="yellow"))
        else:
            logs = await runner.get_run_logs(run_id)
            logs = logs[-lines:]  # Get last N lines
            
            echo(style(f"Logs for run {run_id[:8]}... (last {len(logs)} lines)", fg="cyan"))
            echo()
            
            for log in logs:
                color = {
                    "DEBUG": "dim",
                    "INFO": "white",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red",
                }.get(log.level, "white")
                echo(f"[{log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] "
                     f"[{style(log.level, fg=color)}] {log.message}")
    
    finally:
        await state_store.disconnect()


# Retry command
@cli.command()
@click.option("--run-id", "-r", required=True, help="Run ID to retry")
@click.option("--stage", "-s", help="Stage to retry from")
@click.option("--follow", "-f", is_flag=True, help="Follow logs")
@click.pass_context
@async_cmd
async def retry(ctx, run_id, stage, follow):
    """Retry a failed run."""
    database_url = ctx.obj["database_url"]
    
    if not database_url:
        echo(style("Error: DATABASE_URL required", fg="red"))
        return
    
    state_store = StateStore(database_url=database_url)
    await state_store.connect()
    
    runner = PipelineRunner(state_store=state_store)
    
    try:
        new_run = await runner.retry_run(run_id, stage)
        
        if new_run:
            echo(style(f"✓ Retry started", fg="green"))
            echo(f"  Original run: {run_id[:8]}...")
            echo(f"  New run: {new_run.run_id}")
            
            if follow:
                echo(style("\nFollowing logs... (Ctrl+C to stop)\n", fg="cyan"))
                try:
                    last_log_count = 0
                    while new_run.status in (RunStatus.PENDING, RunStatus.RUNNING):
                        await asyncio.sleep(1)
                        
                        current_run = runner.get_run(new_run.run_id)
                        if current_run:
                            new_logs = current_run.logs[last_log_count:]
                            for log in new_logs:
                                color = {
                                    "DEBUG": "dim",
                                    "INFO": "white",
                                    "WARNING": "yellow",
                                    "ERROR": "red",
                                    "CRITICAL": "red",
                                }.get(log.level, "white")
                                echo(f"[{log.timestamp.strftime('%H:%M:%S')}] "
                                     f"[{style(log.level, fg=color)}] {log.message}")
                            last_log_count = len(current_run.logs)
                            new_run = current_run
                except KeyboardInterrupt:
                    echo(style("\nStopped following", fg="yellow"))
        else:
            echo(style(f"Could not retry run {run_id}", fg="red"))
    
    finally:
        await state_store.disconnect()


# Cancel command
@cli.command()
@click.option("--run-id", "-r", required=True, help="Run ID to cancel")
@click.pass_context
@async_cmd
async def cancel(ctx, run_id):
    """Cancel a running pipeline."""
    database_url = ctx.obj["database_url"]
    
    # For cancel, we need a runner with active runs
    # This would typically connect to the daemon
    echo(style("Note: Cancel requires connection to running daemon", fg="yellow"))
    echo(f"To cancel run {run_id}, use: curl -X POST http://daemon:8080/runs/{run_id}/cancel")


# Daemon command
@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", type=int, default=8080, help="Port to bind to")
@click.option("--detach", "-d", is_flag=True, help="Run in background")
@click.pass_context
def daemon(ctx, host, port, detach):
    """Run the pipeline daemon."""
    database_url = ctx.obj["database_url"]
    
    if detach:
        echo(style("Daemon mode not implemented - use systemd instead", fg="yellow"))
        return
    
    echo(style(f"Starting pipeline daemon on {host}:{port}", fg="blue", bold=True))
    echo(style("Press Ctrl+C to stop\n", fg="dim"))
    
    daemon = PipelineDaemon(
        host=host,
        port=port,
        database_url=database_url,
    )
    
    try:
        asyncio.run(daemon.start())
    except KeyboardInterrupt:
        echo(style("\nShutting down...", fg="yellow"))


# Webhook test command
@cli.command()
@click.option("--secret", "-s", required=True, help="Webhook secret")
@click.option("--payload", "-p", default="{}", help="JSON payload")
@click.option("--url", default="http://localhost:8080", help="Daemon URL")
@click.pass_context
@async_cmd
async def webhook_test(ctx, secret, payload, url):
    """Test a webhook trigger."""
    import aiohttp
    
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as e:
        echo(style(f"Invalid JSON payload: {e}", fg="red"))
        return
    
    echo(style(f"Sending webhook to {url}/webhook/{secret[:8]}...", fg="blue"))
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{url}/webhook/{secret}",
                json=data,
            ) as resp:
                result = await resp.json()
                if resp.status == 200:
                    echo(style(f"✓ Webhook accepted", fg="green"))
                    echo(f"  Run ID: {result.get('run_id')}")
                else:
                    echo(style(f"✗ Webhook failed: {result.get('error')}", fg="red"))
        except Exception as e:
            echo(style(f"Error: {e}", fg="red"))


def main():
    """Entry point."""
    cli()


if __name__ == "__main__":
    main()
