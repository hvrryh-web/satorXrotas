"""
Real-time monitoring dashboard for dual-game extraction pipeline.
Provides visibility into queues, agents, conflicts, and data freshness.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import asyncpg
import aiohttp
from aiohttp import web
import json


@dataclass
class QueueMetrics:
    game: str
    pending: int
    processing: int
    completed_24h: int
    failed_24h: int
    avg_wait_time: float
    oldest_job_age: float


@dataclass
class AgentMetrics:
    agent_id: str
    status: str
    current_job: Optional[str]
    last_heartbeat: datetime
    jobs_completed: int
    jobs_failed: int
    game_specialization: List[str]


@dataclass
class ConflictMetrics:
    total_conflicts: int
    duplicates_prevented: int
    content_drifts: int
    resolved_24h: int


class PipelineDashboard:
    """
    Real-time monitoring dashboard for extraction pipeline.
    
    Provides:
    - Queue depth and health
    - Agent status and performance
    - Conflict detection stats
    - Data freshness by game
    - System health checks
    """
    
    def __init__(self, db_pool: asyncpg.Pool, coordinator_url: str):
        self.db_pool = db_pool
        self.coordinator_url = coordinator_url
        self.metrics_cache = {}
        self.cache_ttl = 30  # seconds
        self._cache_timestamp = None
    
    async def get_overview(self) -> Dict:
        """Get high-level pipeline overview."""
        return {
            "queues": await self._get_queue_overview(),
            "agents": await self._get_agent_overview(),
            "data_freshness": await self._get_data_freshness(),
            "conflicts": await self._get_conflict_summary(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _get_queue_overview(self) -> Dict:
        """Get queue statistics for both games."""
        async with self.db_pool.acquire() as conn:
            # CS Queue stats
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
            
            # Valorant Queue stats
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
            
            return {
                "cs": {
                    "pending": cs_stats['pending'] or 0,
                    "processing": cs_stats['processing'] or 0,
                    "completed_24h": cs_stats['completed_24h'] or 0,
                    "failed_24h": cs_stats['failed_24h'] or 0,
                    "oldest_pending_seconds": cs_stats['oldest_pending_seconds'] or 0,
                    "health": self._calculate_queue_health(cs_stats)
                },
                "valorant": {
                    "pending": val_stats['pending'] or 0,
                    "processing": val_stats['processing'] or 0,
                    "completed_24h": val_stats['completed_24h'] or 0,
                    "failed_24h": val_stats['failed_24h'] or 0,
                    "oldest_pending_seconds": val_stats['oldest_pending_seconds'] or 0,
                    "health": self._calculate_queue_health(val_stats)
                }
            }
    
    def _calculate_queue_health(self, stats) -> str:
        """Calculate queue health status."""
        pending = stats['pending'] or 0
        oldest = stats['oldest_pending_seconds'] or 0
        
        if pending > 1000 or oldest > 3600:  # > 1000 jobs or > 1 hour oldest
            return "critical"
        elif pending > 500 or oldest > 1800:  # > 500 jobs or > 30 min oldest
            return "warning"
        else:
            return "healthy"
    
    async def _get_agent_overview(self) -> Dict:
        """Get agent status summary."""
        async with self.db_pool.acquire() as conn:
            agents = await conn.fetch(
                """
                SELECT 
                    id,
                    status,
                    current_job_id,
                    last_heartbeat,
                    total_jobs_completed,
                    total_jobs_failed,
                    game_specialization
                FROM extraction_agents
                WHERE last_heartbeat > NOW() - INTERVAL '5 minutes'
                ORDER BY status, id
                """
            )
            
            idle_cs = sum(1 for a in agents if a['status'] == 'idle' and 'cs' in a['game_specialization'])
            idle_val = sum(1 for a in agents if a['status'] == 'idle' and 'valorant' in a['game_specialization'])
            busy = sum(1 for a in agents if a['status'] == 'busy')
            offline = await conn.fetchval(
                "SELECT COUNT(*) FROM extraction_agents WHERE last_heartbeat < NOW() - INTERVAL '5 minutes'"
            )
            
            return {
                "total_active": len(agents),
                "idle_cs": idle_cs,
                "idle_valorant": idle_val,
                "busy": busy,
                "offline": offline or 0,
                "agents": [
                    {
                        "id": a['id'],
                        "status": a['status'],
                        "current_job": a['current_job_id'],
                        "games": a['game_specialization'],
                        "success_rate": self._calc_success_rate(a['total_jobs_completed'], a['total_jobs_failed'])
                    }
                    for a in agents
                ]
            }
    
    def _calc_success_rate(self, completed: int, failed: int) -> float:
        """Calculate agent success rate."""
        total = completed + failed
        if total == 0:
            return 100.0
        return round((completed / total) * 100, 1)
    
    async def _get_data_freshness(self) -> Dict:
        """Get data freshness by game and source."""
        async with self.db_pool.acquire() as conn:
            # Get from coordinator's data_freshness view
            cs_fresh = await conn.fetchrow(
                "SELECT * FROM data_freshness WHERE game = 'cs'"
            )
            val_fresh = await conn.fetchrow(
                "SELECT * FROM data_freshness WHERE game = 'valorant'"
            )
            
            # Source-specific freshness
            sources = await conn.fetch(
                """
                SELECT 
                    source,
                    game,
                    MAX(extracted_at) as last_extraction,
                    COUNT(*) FILTER (WHERE extracted_at > NOW() - INTERVAL '24 hours') as records_24h
                FROM raw_extractions
                GROUP BY source, game
                ORDER BY game, source
                """
            )
            
            return {
                "cs": {
                    "last_extraction": cs_fresh['last_extraction'].isoformat() if cs_fresh and cs_fresh['last_extraction'] else None,
                    "records_24h": cs_fresh['last_24h_records'] if cs_fresh else 0,
                    "by_source": [
                        {"source": s['source'], "last_extraction": s['last_extraction'].isoformat(), "records_24h": s['records_24h']}
                        for s in sources if s['game'] == 'cs'
                    ]
                },
                "valorant": {
                    "last_extraction": val_fresh['last_extraction'].isoformat() if val_fresh and val_fresh['last_extraction'] else None,
                    "records_24h": val_fresh['last_24h_records'] if val_fresh else 0,
                    "by_source": [
                        {"source": s['source'], "last_extraction": s['last_extraction'].isoformat(), "records_24h": s['records_24h']}
                        for s in sources if s['game'] == 'valorant'
                    ]
                }
            }
    
    async def _get_conflict_summary(self) -> Dict:
        """Get conflict detection summary."""
        async with self.db_pool.acquire() as conn:
            conflicts = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total_conflicts,
                    COUNT(*) FILTER (WHERE conflict_type = 'duplicate') as duplicates,
                    COUNT(*) FILTER (WHERE conflict_type = 'content_drift') as content_drifts,
                    COUNT(*) FILTER (WHERE detected_at > NOW() - INTERVAL '24 hours') as new_24h
                FROM extraction_conflicts
                WHERE status = 'open'
                """
            )
            
            return {
                "total_open": conflicts['total_conflicts'] or 0,
                "duplicates": conflicts['duplicates'] or 0,
                "content_drifts": conflicts['content_drifts'] or 0,
                "new_24h": conflicts['new_24h'] or 0
            }
    
    async def get_detailed_queue(self, game: Optional[str] = None) -> List[Dict]:
        """Get detailed queue information with job breakdown."""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT 
                    id,
                    game,
                    source,
                    job_type,
                    priority,
                    status,
                    epoch,
                    region,
                    created_at,
                    started_at,
                    assigned_agent,
                    retry_count,
                    error_message
                FROM extraction_jobs
                WHERE status IN ('pending', 'processing', 'assigned')
            """
            
            if game:
                query += " AND game = $1"
                rows = await conn.fetch(query + " ORDER BY priority DESC, created_at ASC", game)
            else:
                rows = await conn.fetch(query + " ORDER BY game, priority DESC, created_at ASC")
            
            return [dict(row) for row in rows]
    
    async def get_failed_jobs(self, game: Optional[str] = None, hours: int = 24) -> List[Dict]:
        """Get recently failed jobs."""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT 
                    id,
                    game,
                    source,
                    job_type,
                    completed_at,
                    retry_count,
                    error_message,
                    assigned_agent
                FROM extraction_jobs
                WHERE status = 'failed'
                  AND completed_at > NOW() - INTERVAL '$1 hours'
            """
            params = [hours]
            
            if game:
                query += " AND game = $2"
                params.append(game)
            
            query += " ORDER BY completed_at DESC"
            
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    async def get_processing_stats(self, hours: int = 24) -> Dict:
        """Get processing statistics for time period."""
        async with self.db_pool.acquire() as conn:
            stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) FILTER (WHERE status = 'completed') as completed,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed,
                    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) 
                        FILTER (WHERE status = 'completed') as avg_duration_seconds
                FROM extraction_jobs
                WHERE completed_at > NOW() - INTERVAL '$1 hours'
                """,
                hours
            )
            
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
            
            return {
                "total": {
                    "completed": stats['completed'] or 0,
                    "failed": stats['failed'] or 0,
                    "avg_duration_seconds": round(stats['avg_duration_seconds'] or 0, 2)
                },
                "by_game": {row['game']: dict(row) for row in by_game}
            }


# ============================================
# Web Dashboard Application
# ============================================

async def init_dashboard_app(db_pool: asyncpg.Pool, coordinator_url: str):
    """Initialize the web dashboard application."""
    
    dashboard = PipelineDashboard(db_pool, coordinator_url)
    app = web.Application()
    
    # API Routes
    async def api_overview(request):
        """Get pipeline overview."""
        data = await dashboard.get_overview()
        return web.json_response(data)
    
    async def api_queue(request):
        """Get detailed queue."""
        game = request.query.get('game')
        data = await dashboard.get_detailed_queue(game)
        return web.json_response(data)
    
    async def api_agents(request):
        """Get agent status."""
        data = await dashboard._get_agent_overview()
        return web.json_response(data)
    
    async def api_failed(request):
        """Get failed jobs."""
        game = request.query.get('game')
        hours = int(request.query.get('hours', 24))
        data = await dashboard.get_failed_jobs(game, hours)
        return web.json_response(data)
    
    async def api_stats(request):
        """Get processing stats."""
        hours = int(request.query.get('hours', 24))
        data = await dashboard.get_processing_stats(hours)
        return web.json_response(data)
    
    async def api_health(request):
        """Health check endpoint."""
        overview = await dashboard.get_overview()
        
        # Determine overall health
        cs_health = overview['queues']['cs']['health']
        val_health = overview['queues']['valorant']['health']
        
        if cs_health == 'critical' or val_health == 'critical':
            status = 'critical'
            status_code = 503
        elif cs_health == 'warning' or val_health == 'warning':
            status = 'degraded'
            status_code = 200
        else:
            status = 'healthy'
            status_code = 200
        
        return web.json_response(
            {"status": status, "details": overview},
            status=status_code
        )
    
    # HTML Dashboard
    async def dashboard_html(request):
        """Serve HTML dashboard."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Axiom Pipeline Dashboard</title>
            <style>
                body { font-family: system-ui, sans-serif; margin: 0; padding: 20px; background: #0a0a0f; color: #fff; }
                .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px; }
                .card { background: #141419; padding: 20px; border-radius: 8px; border: 1px solid #2a2a35; }
                .card h2 { margin-top: 0; color: #3b82f6; }
                .metric { display: flex; justify-content: space-between; margin: 10px 0; }
                .metric-value { font-weight: bold; }
                .healthy { color: #22c55e; }
                .warning { color: #f59e0b; }
                .critical { color: #ef4444; }
                .game-section { margin-top: 30px; }
                table { width: 100%; border-collapse: collapse; margin-top: 10px; }
                th, td { text-align: left; padding: 8px; border-bottom: 1px solid #2a2a35; }
                th { color: #a0a0b0; }
                .refresh { position: fixed; top: 20px; right: 20px; }
                button { background: #3b82f6; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
                button:hover { background: #2563eb; }
            </style>
        </head>
        <body>
            <h1>🎮 Axiom Dual-Game Pipeline Dashboard</h1>
            <div class="refresh">
                <button onclick="loadData()">Refresh</button>
                <label><input type="checkbox" id="autoRefresh" checked> Auto-refresh (30s)</label>
            </div>
            
            <div id="content">
                <p>Loading...</p>
            </div>
            
            <script>
                async function loadData() {
                    try {
                        const response = await fetch('/api/overview');
                        const data = await response.json();
                        renderDashboard(data);
                    } catch (e) {
                        document.getElementById('content').innerHTML = '<p class="critical">Error loading data: ' + e.message + '</p>';
                    }
                }
                
                function renderDashboard(data) {
                    const cs = data.queues.cs;
                    const val = data.queues.valorant;
                    
                    document.getElementById('content').innerHTML = `
                        <div class="grid">
                            <div class="card">
                                <h2>Counter-Strike Queue</h2>
                                <div class="metric">
                                    <span>Status</span>
                                    <span class="${cs.health}">${cs.health.toUpperCase()}</span>
                                </div>
                                <div class="metric">
                                    <span>Pending</span>
                                    <span class="metric-value">${cs.pending}</span>
                                </div>
                                <div class="metric">
                                    <span>Processing</span>
                                    <span class="metric-value">${cs.processing}</span>
                                </div>
                                <div class="metric">
                                    <span>Completed (24h)</span>
                                    <span class="metric-value">${cs.completed_24h}</span>
                                </div>
                            </div>
                            
                            <div class="card">
                                <h2>Valorant Queue</h2>
                                <div class="metric">
                                    <span>Status</span>
                                    <span class="${val.health}">${val.health.toUpperCase()}</span>
                                </div>
                                <div class="metric">
                                    <span>Pending</span>
                                    <span class="metric-value">${val.pending}</span>
                                </div>
                                <div class="metric">
                                    <span>Processing</span>
                                    <span class="metric-value">${val.processing}</span>
                                </div>
                                <div class="metric">
                                    <span>Completed (24h)</span>
                                    <span class="metric-value">${val.completed_24h}</span>
                                </div>
                            </div>
                            
                            <div class="card">
                                <h2>Agents</h2>
                                <div class="metric">
                                    <span>Active</span>
                                    <span class="metric-value">${data.agents.total_active}</span>
                                </div>
                                <div class="metric">
                                    <span>Idle (CS)</span>
                                    <span class="metric-value">${data.agents.idle_cs}</span>
                                </div>
                                <div class="metric">
                                    <span>Idle (VAL)</span>
                                    <span class="metric-value">${data.agents.idle_valorant}</span>
                                </div>
                                <div class="metric">
                                    <span>Busy</span>
                                    <span class="metric-value">${data.agents.busy}</span>
                                </div>
                            </div>
                            
                            <div class="card">
                                <h2>Conflicts</h2>
                                <div class="metric">
                                    <span>Open Conflicts</span>
                                    <span class="metric-value">${data.conflicts.total_open}</span>
                                </div>
                                <div class="metric">
                                    <span>Duplicates</span>
                                    <span class="metric-value">${data.conflicts.duplicates}</span>
                                </div>
                                <div class="metric">
                                    <span>Content Drifts</span>
                                    <span class="metric-value">${data.conflicts.content_drifts}</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="game-section">
                            <h2>Data Freshness</h2>
                            <div class="grid">
                                <div class="card">
                                    <h3>Counter-Strike</h3>
                                    <div class="metric">
                                        <span>Last Extraction</span>
                                        <span>${data.data_freshness.cs.last_extraction ? new Date(data.data_freshness.cs.last_extraction).toLocaleString() : 'Never'}</span>
                                    </div>
                                    <div class="metric">
                                        <span>Records (24h)</span>
                                        <span class="metric-value">${data.data_freshness.cs.records_24h}</span>
                                    </div>
                                </div>
                                <div class="card">
                                    <h3>Valorant</h3>
                                    <div class="metric">
                                        <span>Last Extraction</span>
                                        <span>${data.data_freshness.valorant.last_extraction ? new Date(data.data_freshness.valorant.last_extraction).toLocaleString() : 'Never'}</span>
                                    </div>
                                    <div class="metric">
                                        <span>Records (24h)</span>
                                        <span class="metric-value">${data.data_freshness.valorant.records_24h}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <p style="color: #666; margin-top: 30px;">Last updated: ${new Date(data.timestamp).toLocaleString()}</p>
                    `;
                }
                
                // Initial load
                loadData();
                
                // Auto-refresh
                setInterval(() => {
                    if (document.getElementById('autoRefresh').checked) {
                        loadData();
                    }
                }, 30000);
            </script>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    # Register routes
    app.router.add_get('/', dashboard_html)
    app.router.add_get('/api/overview', api_overview)
    app.router.add_get('/api/queue', api_queue)
    app.router.add_get('/api/agents', api_agents)
    app.router.add_get('/api/failed', api_failed)
    app.router.add_get('/api/stats', api_stats)
    app.router.add_get('/api/health', api_health)
    
    return app


# CLI for running dashboard
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Pipeline Monitoring Dashboard')
    parser.add_argument('--db-url', required=True, help='Database URL')
    parser.add_argument('--coordinator', default='http://localhost:8080', help='Coordinator URL')
    parser.add_argument('--port', type=int, default=8090, help='Dashboard port')
    parser.add_argument('--host', default='0.0.0.0', help='Dashboard host')
    
    args = parser.parse_args()
    
    async def main():
        db_pool = await asyncpg.create_pool(args.db_url)
        app = await init_dashboard_app(db_pool, args.coordinator)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, args.host, args.port)
        await site.start()
        print(f"Dashboard running at http://{args.host}:{args.port}")
        await asyncio.Event().wait()
    
    asyncio.run(main())
