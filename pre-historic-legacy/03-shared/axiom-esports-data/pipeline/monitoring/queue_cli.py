"""
Command-line interface for queue management and monitoring.

Provides administrative commands for:
- Viewing queue status and jobs
- Managing jobs (retry, cancel, prioritize)
- Agent management and inspection
- Conflict resolution
- System health checks

Usage:
    python queue_cli.py status                    # Show pipeline overview
    python queue_cli.py queue --game cs           # Show CS queue details
    python queue_cli.py jobs --failed --game val  # Show failed Valorant jobs
    python queue_cli.py retry --job-id <uuid>     # Retry a specific job
    python queue_cli.py agents                    # List all agents
    python queue_cli.py conflicts                 # Show open conflicts
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from dataclasses import dataclass
from enum import Enum

import asyncpg
import aiohttp
from tabulate import tabulate


class ColorCode(Enum):
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"


def color(text: str, color: ColorCode) -> str:
    """Apply color to text."""
    return f"{color.value}{text}{ColorCode.RESET.value}"


def format_timestamp(ts: Optional[datetime]) -> str:
    """Format timestamp for display."""
    if not ts:
        return "N/A"
    if isinstance(ts, str):
        try:
            ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        except:
            return ts
    ago = datetime.utcnow() - ts.replace(tzinfo=None)
    if ago.total_seconds() < 60:
        return f"{int(ago.total_seconds())}s ago"
    elif ago.total_seconds() < 3600:
        return f"{int(ago.total_seconds() / 60)}m ago"
    elif ago.total_seconds() < 86400:
        return f"{int(ago.total_seconds() / 3600)}h ago"
    else:
        return f"{int(ago.total_seconds() / 86400)}d ago"


def format_duration(seconds: float) -> str:
    """Format duration in human-readable form."""
    if not seconds:
        return "N/A"
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"


class QueueManagerCLI:
    """Command-line interface for pipeline queue management."""
    
    def __init__(self, db_pool: asyncpg.Pool, coordinator_url: str):
        self.db_pool = db_pool
        self.coordinator_url = coordinator_url
    
    # ============================================
    # Status Commands
    # ============================================
    
    async def show_status(self):
        """Display pipeline overview status."""
        async with self.db_pool.acquire() as conn:
            # Queue statistics
            cs_stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) FILTER (WHERE status = 'pending') as pending,
                    COUNT(*) FILTER (WHERE status = 'processing') as processing,
                    COUNT(*) FILTER (WHERE status = 'completed' AND completed_at > NOW() - INTERVAL '24 hours') as completed_24h,
                    COUNT(*) FILTER (WHERE status = 'failed' AND completed_at > NOW() - INTERVAL '24 hours') as failed_24h,
                    EXTRACT(EPOCH FROM (NOW() - MIN(created_at))) FILTER (WHERE status = 'pending') as oldest_pending_seconds
                FROM extraction_jobs
                WHERE game = 'cs'
                """
            )
            
            val_stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) FILTER (WHERE status = 'pending') as pending,
                    COUNT(*) FILTER (WHERE status = 'processing') as processing,
                    COUNT(*) FILTER (WHERE status = 'completed' AND completed_at > NOW() - INTERVAL '24 hours') as completed_24h,
                    COUNT(*) FILTER (WHERE status = 'failed' AND completed_at > NOW() - INTERVAL '24 hours') as failed_24h,
                    EXTRACT(EPOCH FROM (NOW() - MIN(created_at))) FILTER (WHERE status = 'pending') as oldest_pending_seconds
                FROM extraction_jobs
                WHERE game = 'valorant'
                """
            )
            
            # Agent counts
            agents = await conn.fetch(
                """
                SELECT status, game_specialization
                FROM extraction_agents
                WHERE last_heartbeat > NOW() - INTERVAL '5 minutes'
                """
            )
            
            idle_cs = sum(1 for a in agents if a['status'] == 'idle' and 'cs' in a['game_specialization'])
            idle_val = sum(1 for a in agents if a['status'] == 'idle' and 'valorant' in a['game_specialization'])
            busy = sum(1 for a in agents if a['status'] == 'busy')
            offline = await conn.fetchval(
                "SELECT COUNT(*) FROM extraction_agents WHERE last_heartbeat < NOW() - INTERVAL '5 minutes'"
            )
            
            # Conflicts
            conflicts = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE conflict_type = 'duplicate') as duplicates,
                    COUNT(*) FILTER (WHERE conflict_type = 'content_drift') as content_drifts
                FROM extraction_conflicts
                WHERE status = 'open'
                """
            )
        
        # Print header
        print()
        print(color("=" * 70, ColorCode.BOLD))
        print(color("  🎮 AXION DUAL-GAME PIPELINE STATUS", ColorCode.CYAN))
        print(color("=" * 70, ColorCode.BOLD))
        print()
        
        # CS Queue
        cs_health = self._get_health_status(cs_stats['pending'] or 0, cs_stats['oldest_pending_seconds'] or 0)
        print(color("  Counter-Strike Queue", ColorCode.BOLD))
        print(f"    Status:     {self._health_indicator(cs_health)}")
        print(f"    Pending:    {color(str(cs_stats['pending'] or 0), ColorCode.YELLOW)}")
        print(f"    Processing: {cs_stats['processing'] or 0}")
        print(f"    Completed:  {color(str(cs_stats['completed_24h'] or 0), ColorCode.GREEN)} (24h)")
        print(f"    Failed:     {color(str(cs_stats['failed_24h'] or 0), ColorCode.RED if cs_stats['failed_24h'] else ColorCode.GRAY)} (24h)")
        if cs_stats['oldest_pending_seconds']:
            print(f"    Oldest:     {format_duration(cs_stats['oldest_pending_seconds'])}")
        print()
        
        # Valorant Queue
        val_health = self._get_health_status(val_stats['pending'] or 0, val_stats['oldest_pending_seconds'] or 0)
        print(color("  Valorant Queue", ColorCode.BOLD))
        print(f"    Status:     {self._health_indicator(val_health)}")
        print(f"    Pending:    {color(str(val_stats['pending'] or 0), ColorCode.YELLOW)}")
        print(f"    Processing: {val_stats['processing'] or 0}")
        print(f"    Completed:  {color(str(val_stats['completed_24h'] or 0), ColorCode.GREEN)} (24h)")
        print(f"    Failed:     {color(str(val_stats['failed_24h'] or 0), ColorCode.RED if val_stats['failed_24h'] else ColorCode.GRAY)} (24h)")
        if val_stats['oldest_pending_seconds']:
            print(f"    Oldest:     {format_duration(val_stats['oldest_pending_seconds'])}")
        print()
        
        # Agents
        print(color("  Agents", ColorCode.BOLD))
        print(f"    Active:     {color(str(len(agents)), ColorCode.GREEN)}")
        print(f"    Idle (CS):  {idle_cs}")
        print(f"    Idle (VAL): {idle_val}")
        print(f"    Busy:       {color(str(busy), ColorCode.YELLOW)}")
        if offline:
            print(f"    Offline:    {color(str(offline), ColorCode.RED)}")
        print()
        
        # Conflicts
        print(color("  Conflicts", ColorCode.BOLD))
        print(f"    Open:       {color(str(conflicts['total'] or 0), ColorCode.YELLOW if conflicts['total'] else ColorCode.GRAY)}")
        print(f"    Duplicates: {conflicts['duplicates'] or 0}")
        print(f"    Drifts:     {conflicts['content_drifts'] or 0}")
        print()
        
        # Overall health
        overall = "healthy"
        if cs_health == 'critical' or val_health == 'critical':
            overall = 'critical'
        elif cs_health == 'warning' or val_health == 'warning':
            overall = 'warning'
        
        print(color("  Overall Status: ", ColorCode.BOLD) + self._health_indicator(overall))
        print(color("=" * 70, ColorCode.BOLD))
        print()
    
    def _get_health_status(self, pending: int, oldest_seconds: float) -> str:
        """Calculate health status."""
        if pending > 1000 or oldest_seconds > 3600:
            return "critical"
        elif pending > 500 or oldest_seconds > 1800:
            return "warning"
        return "healthy"
    
    def _health_indicator(self, status: str) -> str:
        """Get colored health indicator."""
        if status == "healthy":
            return color("● HEALTHY", ColorCode.GREEN)
        elif status == "warning":
            return color("● WARNING", ColorCode.YELLOW)
        elif status == "critical":
            return color("● CRITICAL", ColorCode.RED)
        return color("● UNKNOWN", ColorCode.GRAY)
    
    # ============================================
    # Queue Commands
    # ============================================
    
    async def show_queue(self, game: Optional[str] = None, limit: int = 50):
        """Display detailed queue information."""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT 
                    id,
                    game,
                    source,
                    job_type,
                    priority,
                    status,
                    created_at,
                    assigned_agent,
                    retry_count
                FROM extraction_jobs
                WHERE status IN ('pending', 'processing', 'assigned')
            """
            
            params = []
            if game:
                query += " AND game = $1"
                params.append(game)
            
            query += " ORDER BY priority DESC, created_at ASC LIMIT $" + str(len(params) + 1)
            params.append(limit)
            
            rows = await conn.fetch(query, *params)
        
        if not rows:
            print(f"\n  No active jobs found{' for ' + game if game else ''}.\n")
            return
        
        print()
        print(color(f"  {'Counter-Strike' if game == 'cs' else 'Valorant' if game == 'valorant' else 'All'} Queue", ColorCode.BOLD))
        print()
        
        table_data = []
        for row in rows:
            status_color = ColorCode.GRAY
            if row['status'] == 'processing':
                status_color = ColorCode.YELLOW
            elif row['status'] == 'pending':
                status_color = ColorCode.BLUE
            
            table_data.append([
                row['id'][:8] + "...",
                color(row['game'].upper(), ColorCode.CYAN),
                row['source'],
                row['job_type'],
                color(str(row['priority']), ColorCode.YELLOW if row['priority'] >= 7 else ColorCode.GRAY),
                color(row['status'].upper(), status_color),
                format_timestamp(row['created_at']),
                row['assigned_agent'][:8] + "..." if row['assigned_agent'] else "-",
                row['retry_count'] if row['retry_count'] > 0 else "-"
            ])
        
        headers = ["ID", "Game", "Source", "Type", "Prio", "Status", "Created", "Agent", "Retries"]
        print(tabulate(table_data, headers=headers, tablefmt="simple"))
        print(f"\n  Showing {len(rows)} jobs")
        print()
    
    # ============================================
    # Job Commands
    # ============================================
    
    async def list_jobs(self, status: Optional[str] = None, game: Optional[str] = None, 
                        hours: int = 24, failed: bool = False, limit: int = 20):
        """List jobs with filters."""
        async with self.db_pool.acquire() as conn:
            conditions = ["1=1"]
            params = []
            param_idx = 1
            
            if failed or status == 'failed':
                conditions.append(f"status = 'failed'")
                conditions.append(f"completed_at > NOW() - INTERVAL '${param_idx} hours'")
                params.append(hours)
                param_idx += 1
            elif status:
                conditions.append(f"status = ${param_idx}")
                params.append(status)
                param_idx += 1
            
            if game:
                conditions.append(f"game = ${param_idx}")
                params.append(game)
                param_idx += 1
            
            query = f"""
                SELECT 
                    id,
                    game,
                    source,
                    job_type,
                    status,
                    priority,
                    created_at,
                    completed_at,
                    assigned_agent,
                    retry_count,
                    error_message
                FROM extraction_jobs
                WHERE {' AND '.join(conditions)}
                ORDER BY completed_at DESC NULLS LAST, created_at DESC
                LIMIT ${param_idx}
            """
            params.append(limit)
            
            rows = await conn.fetch(query, *params)
        
        if not rows:
            print(f"\n  No jobs found matching criteria.\n")
            return
        
        print()
        table_data = []
        for row in rows:
            error_preview = ""
            if row['error_message']:
                error_preview = row['error_message'][:40] + "..." if len(row['error_message']) > 40 else row['error_message']
            
            table_data.append([
                row['id'][:12] + "...",
                row['game'].upper(),
                row['source'],
                row['job_type'],
                row['status'],
                format_timestamp(row['created_at']),
                format_timestamp(row['completed_at']) if row['completed_at'] else "-",
                row['retry_count'],
                error_preview
            ])
        
        headers = ["ID", "Game", "Source", "Type", "Status", "Created", "Completed", "Retries", "Error"]
        print(tabulate(table_data, headers=headers, tablefmt="simple"))
        print(f"\n  Showing {len(rows)} jobs")
        print()
    
    async def show_job(self, job_id: str):
        """Show detailed information for a specific job."""
        async with self.db_pool.acquire() as conn:
            job = await conn.fetchrow(
                """
                SELECT * FROM extraction_jobs WHERE id = $1
                """,
                job_id
            )
        
        if not job:
            print(f"\n  {color('Error:', ColorCode.RED)} Job not found: {job_id}\n")
            return
        
        print()
        print(color("  Job Details", ColorCode.BOLD))
        print(color("  " + "-" * 50, ColorCode.GRAY))
        
        fields = [
            ("ID", job['id']),
            ("Game", job['game'].upper()),
            ("Source", job['source']),
            ("Type", job['job_type']),
            ("Status", color(job['status'].upper(), self._status_color(job['status']))),
            ("Priority", job['priority']),
            ("Epoch", job['epoch']),
            ("Region", job['region'] or "N/A"),
            ("Created", job['created_at']),
            ("Started", job['started_at'] or "N/A"),
            ("Completed", job['completed_at'] or "N/A"),
            ("Assigned Agent", job['assigned_agent'] or "N/A"),
            ("Retry Count", job['retry_count']),
            ("Max Retries", job['max_retries']),
        ]
        
        for label, value in fields:
            print(f"    {label:.<20} {value}")
        
        if job['error_message']:
            print()
            print(color("  Error Message:", ColorCode.RED))
            print(f"    {job['error_message']}")
        
        if job['metadata']:
            print()
            print(color("  Metadata:", ColorCode.GRAY))
            for key, value in job['metadata'].items():
                print(f"    {key}: {value}")
        
        print(color("  " + "-" * 50, ColorCode.GRAY))
        print()
    
    def _status_color(self, status: str) -> ColorCode:
        """Get color for status."""
        colors = {
            'pending': ColorCode.BLUE,
            'processing': ColorCode.YELLOW,
            'completed': ColorCode.GREEN,
            'failed': ColorCode.RED,
            'cancelled': ColorCode.GRAY,
        }
        return colors.get(status, ColorCode.GRAY)
    
    async def retry_job(self, job_id: str):
        """Retry a failed job."""
        async with self.db_pool.acquire() as conn:
            job = await conn.fetchrow(
                "SELECT * FROM extraction_jobs WHERE id = $1",
                job_id
            )
            
            if not job:
                print(f"\n  {color('Error:', ColorCode.RED)} Job not found: {job_id}\n")
                return False
            
            if job['status'] not in ('failed', 'cancelled'):
                print(f"\n  {color('Error:', ColorCode.RED)} Can only retry failed or cancelled jobs. Current status: {job['status']}\n")
                return False
            
            await conn.execute(
                """
                UPDATE extraction_jobs
                SET status = 'pending',
                    retry_count = retry_count + 1,
                    error_message = NULL,
                    assigned_agent = NULL,
                    started_at = NULL,
                    completed_at = NULL
                WHERE id = $1
                """,
                job_id
            )
        
        print(f"\n  ✓ Job {job_id[:8]}... marked for retry.\n")
        return True
    
    async def cancel_job(self, job_id: str, reason: str = "Manual cancellation"):
        """Cancel a pending or processing job."""
        async with self.db_pool.acquire() as conn:
            job = await conn.fetchrow(
                "SELECT * FROM extraction_jobs WHERE id = $1",
                job_id
            )
            
            if not job:
                print(f"\n  {color('Error:', ColorCode.RED)} Job not found: {job_id}\n")
                return False
            
            if job['status'] not in ('pending', 'processing', 'assigned'):
                print(f"\n  {color('Error:', ColorCode.RED)} Can only cancel pending/processing jobs. Current status: {job['status']}\n")
                return False
            
            await conn.execute(
                """
                UPDATE extraction_jobs
                SET status = 'cancelled',
                    completed_at = NOW(),
                    error_message = $2
                WHERE id = $1
                """,
                job_id, reason
            )
        
        print(f"\n  ✓ Job {job_id[:8]}... cancelled.\n")
        return True
    
    async def prioritize_job(self, job_id: str, priority: int):
        """Change job priority."""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE extraction_jobs
                SET priority = $2
                WHERE id = $1 AND status = 'pending'
                """,
                job_id, priority
            )
            
            if result == "UPDATE 0":
                print(f"\n  {color('Error:', ColorCode.RED)} Job not found or not in pending status.\n")
                return False
        
        print(f"\n  ✓ Job {job_id[:8]}... priority set to {priority}.\n")
        return True
    
    # ============================================
    # Agent Commands
    # ============================================
    
    async def list_agents(self, show_offline: bool = False):
        """List all agents."""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT 
                    id,
                    status,
                    current_job_id,
                    last_heartbeat,
                    total_jobs_completed,
                    total_jobs_failed,
                    game_specialization,
                    source_capabilities
                FROM extraction_agents
            """
            
            if not show_offline:
                query += " WHERE last_heartbeat > NOW() - INTERVAL '5 minutes'"
            
            query += " ORDER BY status, id"
            
            agents = await conn.fetch(query)
        
        if not agents:
            print("\n  No agents found.\n")
            return
        
        print()
        table_data = []
        for agent in agents:
            # Calculate success rate
            total = agent['total_jobs_completed'] + agent['total_jobs_failed']
            success_rate = (agent['total_jobs_completed'] / total * 100) if total > 0 else 100
            
            # Check if offline
            is_offline = agent['last_heartbeat'] < datetime.utcnow() - timedelta(minutes=5)
            
            status = agent['status']
            if is_offline:
                status = 'offline'
            
            status_color = ColorCode.GREEN
            if status == 'busy':
                status_color = ColorCode.YELLOW
            elif status == 'offline':
                status_color = ColorCode.RED
            
            table_data.append([
                agent['id'][:12] + "...",
                color(status.upper(), status_color),
                ",".join(agent['game_specialization']),
                ",".join(agent['source_capabilities'][:2]) + ("..." if len(agent['source_capabilities']) > 2 else ""),
                agent['current_job_id'][:8] + "..." if agent['current_job_id'] else "-",
                format_timestamp(agent['last_heartbeat']),
                agent['total_jobs_completed'],
                color(f"{success_rate:.0f}%", ColorCode.GREEN if success_rate > 90 else ColorCode.YELLOW if success_rate > 70 else ColorCode.RED)
            ])
        
        headers = ["ID", "Status", "Games", "Sources", "Current Job", "Heartbeat", "Completed", "Success Rate"]
        print(tabulate(table_data, headers=headers, tablefmt="simple"))
        print(f"\n  Showing {len(agents)} agents")
        print()
    
    async def show_agent(self, agent_id: str):
        """Show detailed agent information."""
        async with self.db_pool.acquire() as conn:
            agent = await conn.fetchrow(
                "SELECT * FROM extraction_agents WHERE id = $1",
                agent_id
            )
            
            if not agent:
                print(f"\n  {color('Error:', ColorCode.RED)} Agent not found: {agent_id}\n")
                return
            
            # Get recent jobs
            recent_jobs = await conn.fetch(
                """
                SELECT id, status, completed_at, error_message
                FROM extraction_jobs
                WHERE assigned_agent = $1
                ORDER BY completed_at DESC NULLS LAST
                LIMIT 10
                """,
                agent_id
            )
        
        print()
        print(color("  Agent Details", ColorCode.BOLD))
        print(color("  " + "-" * 50, ColorCode.GRAY))
        
        total = agent['total_jobs_completed'] + agent['total_jobs_failed']
        success_rate = (agent['total_jobs_completed'] / total * 100) if total > 0 else 100
        
        is_offline = agent['last_heartbeat'] < datetime.utcnow() - timedelta(minutes=5)
        
        fields = [
            ("ID", agent['id']),
            ("Status", color(agent['status'].upper() + (" (OFFLINE)" if is_offline else ""), 
                           ColorCode.RED if is_offline else ColorCode.YELLOW if agent['status'] == 'busy' else ColorCode.GREEN)),
            ("Games", ", ".join(agent['game_specialization'])),
            ("Sources", ", ".join(agent['source_capabilities'])),
            ("Current Job", agent['current_job_id'] or "None"),
            ("Last Heartbeat", f"{agent['last_heartbeat']} ({format_timestamp(agent['last_heartbeat'])})"),
            ("Jobs Completed", agent['total_jobs_completed']),
            ("Jobs Failed", agent['total_jobs_failed']),
            ("Success Rate", f"{success_rate:.1f}%"),
        ]
        
        for label, value in fields:
            print(f"    {label:.<20} {value}")
        
        if recent_jobs:
            print()
            print(color("  Recent Jobs:", ColorCode.GRAY))
            for job in recent_jobs:
                status = job['status']
                status_str = color(status, self._status_color(status))
                print(f"    {job['id'][:12]}... {status_str} {format_timestamp(job['completed_at']) if job['completed_at'] else 'N/A'}")
        
        print(color("  " + "-" * 50, ColorCode.GRAY))
        print()
    
    # ============================================
    # Conflict Commands
    # ============================================
    
    async def list_conflicts(self, conflict_type: Optional[str] = None, game: Optional[str] = None):
        """List open conflicts."""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT 
                    id,
                    game,
                    source_a,
                    source_b,
                    conflict_type,
                    confidence,
                    detected_at,
                    status
                FROM extraction_conflicts
                WHERE status = 'open'
            """
            params = []
            
            if conflict_type:
                query += " AND conflict_type = $" + str(len(params) + 1)
                params.append(conflict_type)
            
            if game:
                query += " AND game = $" + str(len(params) + 1)
                params.append(game)
            
            query += " ORDER BY detected_at DESC"
            
            conflicts = await conn.fetch(query, *params)
        
        if not conflicts:
            print("\n  No open conflicts found.\n")
            return
        
        print()
        table_data = []
        for c in conflicts:
            type_color = ColorCode.YELLOW if c['conflict_type'] == 'duplicate' else ColorCode.MAGENTA
            
            table_data.append([
                c['id'][:8] + "...",
                c['game'].upper(),
                color(c['conflict_type'], type_color),
                f"{c['confidence']:.0%}",
                f"{c['source_a']} vs {c['source_b']}",
                format_timestamp(c['detected_at'])
            ])
        
        headers = ["ID", "Game", "Type", "Confidence", "Sources", "Detected"]
        print(tabulate(table_data, headers=headers, tablefmt="simple"))
        print(f"\n  Showing {len(conflicts)} conflicts")
        print()
    
    async def resolve_conflict(self, conflict_id: str, resolution: str, notes: str = ""):
        """Resolve a conflict."""
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchrow(
                """
                UPDATE extraction_conflicts
                SET status = 'resolved',
                    resolution = $2,
                    resolution_notes = $3,
                    resolved_at = NOW()
                WHERE id = $1 AND status = 'open'
                RETURNING id
                """,
                conflict_id, resolution, notes
            )
            
            if not result:
                print(f"\n  {color('Error:', ColorCode.RED)} Conflict not found or already resolved.\n")
                return False
        
        print(f"\n  ✓ Conflict {conflict_id[:8]}... resolved with: {resolution}\n")
        return True
    
    # ============================================
    # Stats Commands
    # ============================================
    
    async def show_stats(self, hours: int = 24, game: Optional[str] = None):
        """Show processing statistics."""
        async with self.db_pool.acquire() as conn:
            # Overall stats
            stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) FILTER (WHERE status = 'completed') as completed,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed,
                    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) 
                        FILTER (WHERE status = 'completed') as avg_duration_seconds,
                    SUM(records_extracted) FILTER (WHERE status = 'completed') as total_records
                FROM extraction_jobs
                WHERE completed_at > NOW() - INTERVAL '$1 hours'
                """,
                hours
            )
            
            # By game
            by_game = await conn.fetch(
                """
                SELECT 
                    game,
                    COUNT(*) FILTER (WHERE status = 'completed') as completed,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed,
                    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) 
                        FILTER (WHERE status = 'completed') as avg_duration_seconds
                FROM extraction_jobs
                WHERE completed_at > NOW() - INTERVAL '$1 hours'
                GROUP BY game
                """,
                hours
            )
            
            # By source
            by_source = await conn.fetch(
                """
                SELECT 
                    source,
                    COUNT(*) FILTER (WHERE status = 'completed') as completed,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed
                FROM extraction_jobs
                WHERE completed_at > NOW() - INTERVAL '$1 hours'
                GROUP BY source
                ORDER BY completed DESC
                """,
                hours
            )
        
        print()
        print(color(f"  Processing Statistics (Last {hours}h)", ColorCode.BOLD))
        print()
        
        completed = stats['completed'] or 0
        failed = stats['failed'] or 0
        total = completed + failed
        success_rate = (completed / total * 100) if total > 0 else 0
        
        print(f"    Total Jobs:     {total}")
        print(f"    Completed:      {color(str(completed), ColorCode.GREEN)}")
        print(f"    Failed:         {color(str(failed), ColorCode.RED if failed else ColorCode.GRAY)}")
        print(f"    Success Rate:   {color(f'{success_rate:.1f}%', ColorCode.GREEN if success_rate > 90 else ColorCode.YELLOW if success_rate > 70 else ColorCode.RED)}")
        print(f"    Avg Duration:   {format_duration(stats['avg_duration_seconds'] or 0)}")
        print(f"    Records:        {stats['total_records'] or 0:,}")
        print()
        
        if by_game:
            print(color("  By Game:", ColorCode.GRAY))
            for row in by_game:
                total_g = (row['completed'] or 0) + (row['failed'] or 0)
                rate = (row['completed'] / total_g * 100) if total_g > 0 else 0
                print(f"    {row['game'].upper():.<15} {row['completed'] or 0} completed, {rate:.1f}% success")
            print()
        
        if by_source:
            print(color("  By Source:", ColorCode.GRAY))
            for row in by_source[:10]:
                print(f"    {row['source']:<15} {row['completed'] or 0} completed")
            print()


# ============================================
# Main CLI Entry Point
# ============================================

async def main():
    parser = argparse.ArgumentParser(
        description="Axiom Pipeline Queue Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s status                          # Show pipeline overview
  %(prog)s queue --game cs                 # Show CS queue
  %(prog)s jobs --failed --limit 10        # Show last 10 failed jobs
  %(prog)s job <id>                        # Show job details
  %(prog)s retry --job-id <uuid>           # Retry a failed job
  %(prog)s agents                          # List all agents
  %(prog)s conflicts                       # Show open conflicts
  %(prog)s stats --hours 48                # Show 48h statistics
        """
    )
    
    parser.add_argument('--db-url', default='postgresql://localhost/axiom', 
                       help='Database URL (default: postgresql://localhost/axiom)')
    parser.add_argument('--coordinator', default='http://localhost:8080',
                       help='Coordinator URL (default: http://localhost:8080)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    subparsers.add_parser('status', help='Show pipeline overview')
    
    # Queue command
    queue_parser = subparsers.add_parser('queue', help='Show queue details')
    queue_parser.add_argument('--game', choices=['cs', 'valorant'], help='Filter by game')
    queue_parser.add_argument('--limit', type=int, default=50, help='Maximum jobs to show')
    
    # Jobs command
    jobs_parser = subparsers.add_parser('jobs', help='List jobs')
    jobs_parser.add_argument('--status', choices=['pending', 'processing', 'completed', 'failed', 'cancelled'])
    jobs_parser.add_argument('--game', choices=['cs', 'valorant'])
    jobs_parser.add_argument('--failed', action='store_true', help='Show only failed jobs')
    jobs_parser.add_argument('--hours', type=int, default=24, help='Time window for failed jobs')
    jobs_parser.add_argument('--limit', type=int, default=20, help='Maximum jobs to show')
    
    # Job command (single job details)
    job_parser = subparsers.add_parser('job', help='Show job details')
    job_parser.add_argument('job_id', help='Job ID')
    
    # Retry command
    retry_parser = subparsers.add_parser('retry', help='Retry a failed job')
    retry_parser.add_argument('--job-id', required=True, help='Job ID to retry')
    
    # Cancel command
    cancel_parser = subparsers.add_parser('cancel', help='Cancel a job')
    cancel_parser.add_argument('--job-id', required=True, help='Job ID to cancel')
    cancel_parser.add_argument('--reason', default='Manual cancellation', help='Cancellation reason')
    
    # Prioritize command
    prio_parser = subparsers.add_parser('prioritize', help='Change job priority')
    prio_parser.add_argument('--job-id', required=True, help='Job ID')
    prio_parser.add_argument('--priority', type=int, required=True, help='New priority (1-10)')
    
    # Agents command
    agents_parser = subparsers.add_parser('agents', help='List agents')
    agents_parser.add_argument('--offline', action='store_true', help='Include offline agents')
    
    # Agent command
    agent_parser = subparsers.add_parser('agent', help='Show agent details')
    agent_parser.add_argument('agent_id', help='Agent ID')
    
    # Conflicts command
    conflicts_parser = subparsers.add_parser('conflicts', help='List conflicts')
    conflicts_parser.add_argument('--type', choices=['duplicate', 'content_drift'], help='Filter by type')
    conflicts_parser.add_argument('--game', choices=['cs', 'valorant'], help='Filter by game')
    
    # Resolve command
    resolve_parser = subparsers.add_parser('resolve', help='Resolve a conflict')
    resolve_parser.add_argument('--conflict-id', required=True, help='Conflict ID')
    resolve_parser.add_argument('--resolution', required=True, choices=['source_a', 'source_b', 'merged', 'invalid'],
                               help='Resolution strategy')
    resolve_parser.add_argument('--notes', default='', help='Resolution notes')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show processing statistics')
    stats_parser.add_argument('--hours', type=int, default=24, help='Time window')
    stats_parser.add_argument('--game', choices=['cs', 'valorant'], help='Filter by game')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Create database pool
    db_pool = await asyncpg.create_pool(args.db_url)
    cli = QueueManagerCLI(db_pool, args.coordinator)
    
    try:
        if args.command == 'status':
            await cli.show_status()
        
        elif args.command == 'queue':
            await cli.show_queue(game=args.game, limit=args.limit)
        
        elif args.command == 'jobs':
            await cli.list_jobs(
                status=args.status,
                game=args.game,
                hours=args.hours,
                failed=args.failed,
                limit=args.limit
            )
        
        elif args.command == 'job':
            await cli.show_job(args.job_id)
        
        elif args.command == 'retry':
            await cli.retry_job(args.job_id)
        
        elif args.command == 'cancel':
            await cli.cancel_job(args.job_id, args.reason)
        
        elif args.command == 'prioritize':
            await cli.prioritize_job(args.job_id, args.priority)
        
        elif args.command == 'agents':
            await cli.list_agents(show_offline=args.offline)
        
        elif args.command == 'agent':
            await cli.show_agent(args.agent_id)
        
        elif args.command == 'conflicts':
            await cli.list_conflicts(conflict_type=args.type, game=args.game)
        
        elif args.command == 'resolve':
            await cli.resolve_conflict(args.conflict_id, args.resolution, args.notes)
        
        elif args.command == 'stats':
            await cli.show_stats(hours=args.hours, game=args.game)
    
    finally:
        await db_pool.close()


if __name__ == '__main__':
    asyncio.run(main())
