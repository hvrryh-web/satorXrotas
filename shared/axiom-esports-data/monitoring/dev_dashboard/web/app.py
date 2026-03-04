"""
Developer Dashboard Web Application
Serves the health check dashboard with layered views.
"""

import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any

import asyncpg
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from ..models import (
    DashboardSummary, SystemLayer, HealthStatus,
    MaintenanceWindow, AlertRule, SystemComponent
)
from ..registry import ComponentRegistry, default_registry
from ..collectors import (
    DatabaseCollector, APICollector, PipelineCollector,
    WebsiteCollector, ExternalCollector
)

app = FastAPI(
    title="SATOR Developer Dashboard",
    description="Health monitoring and maintenance dashboard",
    version="1.0.0"
)

# Global state
registry = default_registry
db_pool: Optional[asyncpg.Pool] = None
latest_results: Dict[str, Dict[str, Any]] = {}


def get_collector_for_component(
    component: SystemComponent,
    pool: Optional[asyncpg.Pool] = None
):
    """Get appropriate collector for a component."""
    layer_collectors = {
        SystemLayer.INFRASTRUCTURE: DatabaseCollector,
        SystemLayer.API_SERVICES: APICollector,
        SystemLayer.DATA_PIPELINE: PipelineCollector,
        SystemLayer.WEB_PLATFORM: WebsiteCollector,
        SystemLayer.EXTERNAL: ExternalCollector,
    }
    
    collector_class = layer_collectors.get(component.layer)
    if collector_class:
        # DatabaseCollector requires db_pool
        if collector_class == DatabaseCollector:
            return collector_class(component, db_pool=pool)
        return collector_class(component)
    return None


@app.on_event("startup")
async def startup():
    """Initialize database connection."""
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(
            "postgresql://localhost/axiom_monitoring",
            min_size=2,
            max_size=10
        )
    except Exception as e:
        print(f"Warning: Could not connect to database: {e}")
        db_pool = None
    
    # Start background health check collection
    asyncio.create_task(health_check_loop())


@app.on_event("shutdown")
async def shutdown():
    """Cleanup."""
    if db_pool:
        await db_pool.close()


async def health_check_loop():
    """Background task to collect health checks."""
    while True:
        try:
            await collect_all_health_checks()
        except Exception as e:
            print(f"Health check collection failed: {e}")
        
        # Collect every 30 seconds
        await asyncio.sleep(30)


async def collect_all_health_checks():
    """Collect health checks from all components."""
    global latest_results
    
    for component in registry.get_all():
        try:
            collector = get_collector_for_component(component, db_pool)
            if collector:
                async with collector as c:
                    results = await c.collect()
                    latest_results[component.component_id] = {
                        "component": component,
                        "checks": results,
                        "timestamp": datetime.utcnow()
                    }
        except Exception as e:
            print(f"Failed to collect from {component.component_id}: {e}")


# API Routes
@app.get("/api/summary", response_model=DashboardSummary)
async def get_summary():
    """Get high-level dashboard summary."""
    
    # Calculate stats from latest results
    total = len(latest_results)
    healthy = sum(
        1 for r in latest_results.values()
        if all(c.status == HealthStatus.HEALTHY for c in r["checks"])
    )
    critical = sum(
        1 for r in latest_results.values()
        if any(c.status == HealthStatus.CRITICAL for c in r["checks"])
    )
    degraded = total - healthy - critical
    
    # Layer status
    layer_status = {}
    for layer in SystemLayer:
        components = registry.get_by_layer(layer)
        if not components:
            continue
        
        statuses = []
        for comp in components:
            if comp.component_id in latest_results:
                checks = latest_results[comp.component_id]["checks"]
                if any(c.status == HealthStatus.CRITICAL for c in checks):
                    statuses.append(HealthStatus.CRITICAL)
                elif any(c.status == HealthStatus.DEGRADED for c in checks):
                    statuses.append(HealthStatus.DEGRADED)
                elif checks:
                    statuses.append(HealthStatus.HEALTHY)
        
        if statuses:
            layer_status[layer] = max(statuses, key=lambda s: {
                HealthStatus.HEALTHY: 0,
                HealthStatus.DEGRADED: 1,
                HealthStatus.CRITICAL: 2
            }.get(s, 0))
    
    # Determine overall status
    if critical > 0:
        overall = HealthStatus.CRITICAL
    elif degraded > 0:
        overall = HealthStatus.DEGRADED
    else:
        overall = HealthStatus.HEALTHY
    
    return DashboardSummary(
        overall_status=overall,
        layer_status=layer_status,
        total_components=total,
        healthy_count=healthy,
        degraded_count=degraded,
        critical_count=critical,
        maintenance_count=0,
        active_alerts=0,
        failed_checks_1h=0
    )


@app.get("/api/layers/{layer}/components")
async def get_layer_components(layer: SystemLayer):
    """Get all components for a specific layer."""
    components = registry.get_by_layer(layer)
    
    result = []
    for comp in components:
        data = latest_results.get(comp.component_id, {})
        checks = data.get("checks", [])
        timestamp = data.get("timestamp")
        
        # Determine overall status
        if any(c.status == HealthStatus.CRITICAL for c in checks):
            status = HealthStatus.CRITICAL
        elif any(c.status == HealthStatus.DEGRADED for c in checks):
            status = HealthStatus.DEGRADED
        elif checks:
            status = HealthStatus.HEALTHY
        else:
            status = HealthStatus.UNKNOWN
        
        result.append({
            "component": comp.dict(),
            "status": status.value,
            "checks": [c.dict() for c in checks],
            "last_check": timestamp.isoformat() if timestamp else None
        })
    
    return result


@app.get("/api/components/{component_id}/checks")
async def get_component_checks(component_id: str):
    """Get detailed health checks for a specific component."""
    if component_id not in latest_results:
        raise HTTPException(404, "Component not found")
    
    data = latest_results[component_id]
    return {
        "component": data["component"].dict(),
        "checks": [c.dict() for c in data["checks"]],
        "timestamp": data["timestamp"].isoformat()
    }


@app.get("/api/layers")
async def get_layers():
    """Get all available layers with counts."""
    return [
        {
            "id": layer.value,
            "name": layer.value.replace("_", " ").title(),
            "component_count": len(registry.get_by_layer(layer)),
            "icon": get_layer_icon(layer)
        }
        for layer in SystemLayer
    ]


def get_layer_icon(layer: SystemLayer) -> str:
    """Get icon for layer."""
    icons = {
        SystemLayer.INFRASTRUCTURE: "🗄️",
        SystemLayer.API_SERVICES: "🔌",
        SystemLayer.DATA_PIPELINE: "📊",
        SystemLayer.WEB_PLATFORM: "🌐",
        SystemLayer.SIMULATION: "🎮",
        SystemLayer.SECURITY: "🔒",
        SystemLayer.EXTERNAL: "🔗"
    }
    return icons.get(layer, "📦")


# HTML Dashboard
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve main dashboard HTML."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SATOR Developer Dashboard</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #0a0a0f;
                color: #e2e8f0;
                line-height: 1.6;
            }
            
            /* Header */
            .header {
                background: #141419;
                border-bottom: 1px solid #2a2a35;
                padding: 1rem 2rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
                position: sticky;
                top: 0;
                z-index: 100;
            }
            
            .header h1 {
                font-size: 1.5rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .header-status {
                display: flex;
                align-items: center;
                gap: 1rem;
            }
            
            .status-badge {
                padding: 0.25rem 1rem;
                border-radius: 20px;
                font-size: 0.875rem;
                font-weight: 600;
                text-transform: uppercase;
            }
            
            .status-healthy {
                background: rgba(34, 197, 94, 0.2);
                color: #22c55e;
            }
            
            .status-degraded {
                background: rgba(245, 158, 11, 0.2);
                color: #f59e0b;
            }
            
            .status-critical {
                background: rgba(239, 68, 68, 0.2);
                color: #ef4444;
            }
            
            .last-updated {
                color: #64748b;
                font-size: 0.875rem;
            }
            
            /* Layout */
            .container {
                display: flex;
                min-height: calc(100vh - 65px);
            }
            
            /* Sidebar */
            .sidebar {
                width: 280px;
                background: #141419;
                border-right: 1px solid #2a2a35;
                padding: 1.5rem;
                overflow-y: auto;
            }
            
            .sidebar-section {
                margin-bottom: 2rem;
            }
            
            .sidebar-title {
                font-size: 0.75rem;
                text-transform: uppercase;
                color: #64748b;
                margin-bottom: 0.75rem;
                letter-spacing: 0.05em;
            }
            
            .layer-nav {
                list-style: none;
            }
            
            .layer-item {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                padding: 0.75rem;
                border-radius: 6px;
                cursor: pointer;
                transition: all 0.2s;
                margin-bottom: 0.25rem;
            }
            
            .layer-item:hover {
                background: #1e1e28;
            }
            
            .layer-item.active {
                background: #3b82f6;
            }
            
            .layer-icon {
                font-size: 1.25rem;
            }
            
            .layer-name {
                flex: 1;
            }
            
            .layer-count {
                background: #2a2a35;
                padding: 0.125rem 0.5rem;
                border-radius: 10px;
                font-size: 0.75rem;
            }
            
            /* Main Content */
            .main {
                flex: 1;
                padding: 2rem;
                overflow-y: auto;
            }
            
            /* Stats Grid */
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1rem;
                margin-bottom: 2rem;
            }
            
            .stat-card {
                background: #141419;
                border: 1px solid #2a2a35;
                border-radius: 8px;
                padding: 1.5rem;
            }
            
            .stat-label {
                color: #64748b;
                font-size: 0.875rem;
                margin-bottom: 0.5rem;
            }
            
            .stat-value {
                font-size: 2rem;
                font-weight: 700;
            }
            
            .stat-value.healthy { color: #22c55e; }
            .stat-value.degraded { color: #f59e0b; }
            .stat-value.critical { color: #ef4444; }
            
            /* Components Grid */
            .section-title {
                font-size: 1.25rem;
                margin-bottom: 1rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .components-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                gap: 1rem;
            }
            
            .component-card {
                background: #141419;
                border: 1px solid #2a2a35;
                border-radius: 8px;
                padding: 1.25rem;
                transition: border-color 0.2s;
            }
            
            .component-card:hover {
                border-color: #3b82f6;
            }
            
            .component-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 1rem;
            }
            
            .component-name {
                font-weight: 600;
                margin-bottom: 0.25rem;
            }
            
            .component-description {
                color: #64748b;
                font-size: 0.875rem;
            }
            
            .component-status {
                width: 12px;
                height: 12px;
                border-radius: 50%;
                flex-shrink: 0;
            }
            
            .status-indicator-healthy { background: #22c55e; box-shadow: 0 0 8px #22c55e; }
            .status-indicator-degraded { background: #f59e0b; box-shadow: 0 0 8px #f59e0b; }
            .status-indicator-critical { background: #ef4444; box-shadow: 0 0 8px #ef4444; }
            .status-indicator-unknown { background: #64748b; }
            
            .checks-list {
                list-style: none;
            }
            
            .check-item {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                padding: 0.5rem;
                border-radius: 4px;
                margin-bottom: 0.25rem;
                font-size: 0.875rem;
            }
            
            .check-item:hover {
                background: #1e1e28;
            }
            
            .check-status {
                width: 8px;
                height: 8px;
                border-radius: 50%;
            }
            
            .check-name {
                flex: 1;
            }
            
            .check-value {
                color: #64748b;
                font-family: monospace;
            }
            
            .check-message {
                color: #94a3b8;
                font-size: 0.75rem;
                margin-left: 1.25rem;
                margin-top: 0.25rem;
            }
            
            /* Loading State */
            .loading {
                text-align: center;
                padding: 4rem;
                color: #64748b;
            }
            
            .spinner {
                width: 40px;
                height: 40px;
                border: 3px solid #2a2a35;
                border-top-color: #3b82f6;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 1rem;
            }
            
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            
            /* Modal */
            .modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.8);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 1000;
                opacity: 0;
                visibility: hidden;
                transition: all 0.3s;
            }
            
            .modal-overlay.active {
                opacity: 1;
                visibility: visible;
            }
            
            .modal-content {
                background: #141419;
                border: 1px solid #2a2a35;
                border-radius: 12px;
                padding: 2rem;
                max-width: 600px;
                width: 90%;
                max-height: 80vh;
                overflow-y: auto;
            }
            
            .modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 1.5rem;
            }
            
            .modal-close {
                background: none;
                border: none;
                color: #64748b;
                font-size: 1.5rem;
                cursor: pointer;
            }
            
            .modal-close:hover {
                color: #e2e8f0;
            }
            
            /* Responsive */
            @media (max-width: 768px) {
                .sidebar {
                    display: none;
                }
                
                .components-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <header class="header">
            <h1>🎮 SATOR Developer Dashboard</h1>
            <div class="header-status">
                <span id="overall-status" class="status-badge">Loading...</span>
                <span id="last-updated" class="last-updated">--</span>
            </div>
        </header>
        
        <div class="container">
            <aside class="sidebar">
                <div class="sidebar-section">
                    <div class="sidebar-title">System Layers</div>
                    <ul id="layer-nav" class="layer-nav">
                        <!-- Populated by JS -->
                    </ul>
                </div>
                
                <div class="sidebar-section">
                    <div class="sidebar-title">Quick Links</div>
                    <ul class="layer-nav">
                        <li class="layer-item" onclick="showMaintenance()">
                            <span class="layer-icon">🔧</span>
                            <span class="layer-name">Maintenance</span>
                        </li>
                        <li class="layer-item" onclick="showAlerts()">
                            <span class="layer-icon">🔔</span>
                            <span class="layer-name">Alerts</span>
                        </li>
                        <li class="layer-item" onclick="showMetrics()">
                            <span class="layer-icon">📈</span>
                            <span class="layer-name">Metrics</span>
                        </li>
                    </ul>
                </div>
            </aside>
            
            <main class="main">
                <div id="content">
                    <div class="loading">
                        <div class="spinner"></div>
                        <p>Loading dashboard...</p>
                    </div>
                </div>
            </main>
        </div>
        
        <!-- Modal for detailed views -->
        <div id="modal" class="modal-overlay" onclick="closeModal(event)">
            <div class="modal-content" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h2 id="modal-title">Details</h2>
                    <button class="modal-close" onclick="closeModal()">&times;</button>
                </div>
                <div id="modal-body">
                    <!-- Populated by JS -->
                </div>
            </div>
        </div>
        
        <script src="/static/dashboard.js"></script>
    </body>
    </html>
    """


# Mount static files
import os
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8095)
