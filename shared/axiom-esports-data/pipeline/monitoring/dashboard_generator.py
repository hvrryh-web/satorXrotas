"""
Dashboard Generator — Generate monitoring dashboards.

Supports:
    - Grafana: JSON dashboard for Grafana import
    - HTML: Standalone HTML dashboard

Example:
    from pipeline.monitoring import DashboardGenerator
    
    generator = DashboardGenerator()
    
    # Generate Grafana dashboard
    grafana_json = generator.generate_grafana_dashboard()
    
    # Generate HTML dashboard
    html = generator.generate_html_dashboard(metrics_data)
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Any
from pathlib import Path


@dataclass
class DashboardConfig:
    """Configuration for dashboard generation."""
    title: str = "Axiom Pipeline Dashboard"
    datasource: str = "prometheus"
    refresh_interval: str = "30s"
    timezone: str = "utc"


class DashboardGenerator:
    """
    Generate monitoring dashboards for the pipeline.
    
    Can create:
        - Grafana dashboard JSON for import
        - Standalone HTML dashboard
    """
    
    # Default colors
    COLOR_GREEN = "#73BF69"
    COLOR_YELLOW = "#F2CC0C"
    COLOR_RED = "#F2495C"
    COLOR_BLUE = "#5794F2"
    COLOR_PURPLE = "#B877D9"
    
    def __init__(self, config: Optional[DashboardConfig] = None) -> None:
        """Initialize dashboard generator."""
        self.config = config or DashboardConfig()
    
    def generate_grafana_dashboard(self) -> dict:
        """
        Generate Grafana dashboard JSON.
        
        Returns:
            Dashboard JSON as dictionary (can be dumped to JSON)
        """
        return {
            "dashboard": {
                "id": None,
                "uid": "axiom-pipeline",
                "title": self.config.title,
                "tags": ["axiom", "pipeline", "monitoring"],
                "timezone": self.config.timezone,
                "refresh": self.config.refresh_interval,
                "schemaVersion": 36,
                "version": 1,
                "panels": self._generate_grafana_panels(),
                "time": {
                    "from": "now-6h",
                    "to": "now",
                },
                "templating": {
                    "list": [
                        {
                            "name": "datasource",
                            "type": "datasource",
                            "query": "prometheus",
                            "current": {
                                "text": self.config.datasource,
                                "value": self.config.datasource,
                            },
                        }
                    ]
                },
            },
            "overwrite": True,
        }
    
    def _generate_grafana_panels(self) -> list[dict]:
        """Generate Grafana panel definitions."""
        panels = []
        y_pos = 0
        
        # Row: Overview
        panels.append(self._grafana_row("Overview", y_pos))
        y_pos += 1
        
        # Panel: Records Processed (counter)
        panels.append(self._grafana_stat_panel(
            title="Records Processed",
            query='sum(rate(axiom_records_processed_total[5m]))',
            y_pos=y_pos,
            x_pos=0,
            width=6,
            color=self.COLOR_GREEN,
            unit="ops",
        ))
        
        # Panel: Error Rate
        panels.append(self._grafana_stat_panel(
            title="Error Rate",
            query='sum(rate(axiom_records_failed_total[5m])) / sum(rate(axiom_records_processed_total[5m]))',
            y_pos=y_pos,
            x_pos=6,
            width=6,
            color=self.COLOR_RED,
            unit="percentunit",
            thresholds=[0.05, 0.1],
        ))
        
        # Panel: Active Runs
        panels.append(self._grafana_stat_panel(
            title="Active Runs",
            query='axiom_pipeline_active_runs',
            y_pos=y_pos,
            x_pos=12,
            width=6,
            color=self.COLOR_BLUE,
        ))
        
        # Panel: Data Quality Score
        panels.append(self._grafana_gauge_panel(
            title="Data Quality Score",
            query='axiom_data_quality_score',
            y_pos=y_pos,
            x_pos=18,
            width=6,
            min=0,
            max=100,
            thresholds=[50, 75, 90],
        ))
        
        y_pos += 6
        
        # Row: Throughput
        panels.append(self._grafana_row("Throughput", y_pos))
        y_pos += 1
        
        # Panel: Records by Stage (graph)
        panels.append(self._grafana_graph_panel(
            title="Records Processed by Stage",
            queries=[
                {
                    "expr": 'sum(rate(axiom_records_processed_total[5m])) by (stage)',
                    "legend": '{{stage}}',
                }
            ],
            y_pos=y_pos,
            x_pos=0,
            width=12,
            unit="ops",
        ))
        
        # Panel: Stage Duration (heatmap)
        panels.append(self._grafana_heatmap_panel(
            title="Stage Duration Distribution",
            query='sum(rate(axiom_stage_duration_seconds_bucket[5m])) by (le, stage)',
            y_pos=y_pos,
            x_pos=12,
            width=12,
        ))
        
        y_pos += 8
        
        # Row: Data Quality
        panels.append(self._grafana_row("Data Quality", y_pos))
        y_pos += 1
        
        # Panel: Validation Failures
        panels.append(self._grafana_graph_panel(
            title="Validation Failures",
            queries=[
                {
                    "expr": 'sum(rate(axiom_validation_failures_total[5m])) by (check_type)',
                    "legend": '{{check_type}}',
                }
            ],
            y_pos=y_pos,
            x_pos=0,
            width=8,
            unit="ops",
        ))
        
        # Panel: Duplicates Detected
        panels.append(self._grafana_graph_panel(
            title="Duplicates Detected",
            queries=[
                {
                    "expr": 'sum(rate(axiom_duplicates_detected_total[5m])) by (duplicate_type)',
                    "legend": '{{duplicate_type}}',
                }
            ],
            y_pos=y_pos,
            x_pos=8,
            width=8,
            unit="ops",
        ))
        
        # Panel: Queue Depth
        panels.append(self._grafana_graph_panel(
            title="Queue Depth",
            queries=[
                {
                    "expr": 'axiom_pipeline_queue_depth',
                    "legend": '{{queue_type}}',
                }
            ],
            y_pos=y_pos,
            x_pos=16,
            width=8,
        ))
        
        y_pos += 8
        
        # Row: System Health
        panels.append(self._grafana_row("System Health", y_pos))
        y_pos += 1
        
        # Panel: DB Query Duration
        panels.append(self _grafana_graph_panel(
            title="Database Query Duration",
            queries=[
                {
                    "expr": 'histogram_quantile(0.95, sum(rate(axiom_db_query_duration_seconds_bucket[5m])) by (le, query_type))',
                    "legend": 'p95 {{query_type}}',
                },
                {
                    "expr": 'histogram_quantile(0.50, sum(rate(axiom_db_query_duration_seconds_bucket[5m])) by (le, query_type))',
                    "legend": 'p50 {{query_type}}',
                }
            ],
            y_pos=y_pos,
            x_pos=0,
            width=12,
            unit="s",
        ))
        
        # Panel: Registry Cache Size
        panels.append(self _grafana_stat_panel(
            title="Registry Cache Size",
            query='axiom_registry_cache_size',
            y_pos=y_pos,
            x_pos=12,
            width=6,
            color=self.COLOR_PURPLE,
        ))
        
        # Panel: Last Success
        panels.append(self._grafana_stat_panel(
            title="Time Since Last Success",
            query='time() - axiom_last_success_timestamp',
            y_pos=y_pos,
            x_pos=18,
            width=6,
            color=self.COLOR_YELLOW,
            unit="s",
        ))
        
        return panels
    
    def _grafana_row(self, title: str, y_pos: int) -> dict:
        """Create a row panel."""
        return {
            "id": None,
            "title": title,
            "type": "row",
            "gridPos": {"h": 1, "w": 24, "x": 0, "y": y_pos},
            "collapsed": False,
        }
    
    def _grafana_stat_panel(
        self,
        title: str,
        query: str,
        y_pos: int,
        x_pos: int = 0,
        width: int = 6,
        height: int = 5,
        color: str = COLOR_BLUE,
        unit: str = "short",
        thresholds: Optional[list[float]] = None,
    ) -> dict:
        """Create a stat panel."""
        panel = {
            "id": None,
            "title": title,
            "type": "stat",
            "targets": [
                {
                    "expr": query,
                    "refId": "A",
                    "datasource": {"type": "prometheus", "uid": "${datasource}"},
                }
            ],
            "gridPos": {"h": height, "w": width, "x": x_pos, "y": y_pos},
            "fieldConfig": {
                "defaults": {
                    "unit": unit,
                    "color": {"mode": "fixed", "fixedColor": color},
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": color, "value": None},
                        ],
                    },
                },
                "overrides": [],
            },
            "options": {
                "graphMode": "area",
                "colorMode": "value",
                "orientation": "auto",
            },
        }
        
        if thresholds:
            panel["fieldConfig"]["defaults"]["thresholds"]["steps"] = [
                {"color": self.COLOR_GREEN, "value": None},
                {"color": self.COLOR_YELLOW, "value": thresholds[0]},
                {"color": self.COLOR_RED, "value": thresholds[1] if len(thresholds) > 1 else thresholds[0] * 2},
            ]
        
        return panel
    
    def _grafana_gauge_panel(
        self,
        title: str,
        query: str,
        y_pos: int,
        x_pos: int = 0,
        width: int = 6,
        min: float = 0,
        max: float = 100,
        thresholds: list[float] = None,
    ) -> dict:
        """Create a gauge panel."""
        threshold_steps = [
            {"color": self.COLOR_RED, "value": None},
            {"color": self.COLOR_YELLOW, "value": thresholds[0] if thresholds else 50},
            {"color": self.COLOR_GREEN, "value": thresholds[2] if thresholds and len(thresholds) > 2 else 75},
        ]
        
        return {
            "id": None,
            "title": title,
            "type": "gauge",
            "targets": [
                {
                    "expr": query,
                    "refId": "A",
                    "datasource": {"type": "prometheus", "uid": "${datasource}"},
                }
            ],
            "gridPos": {"h": 5, "w": width, "x": x_pos, "y": y_pos},
            "fieldConfig": {
                "defaults": {
                    "min": min,
                    "max": max,
                    "unit": "percent",
                    "thresholds": {
                        "mode": "absolute",
                        "steps": threshold_steps,
                    },
                },
                "overrides": [],
            },
            "options": {
                "showThresholdLabels": True,
                "showThresholdMarkers": True,
            },
        }
    
    def _grafana_graph_panel(
        self,
        title: str,
        queries: list[dict],
        y_pos: int,
        x_pos: int = 0,
        width: int = 12,
        height: int = 7,
        unit: str = "short",
    ) -> dict:
        """Create a time series graph panel."""
        return {
            "id": None,
            "title": title,
            "type": "timeseries",
            "targets": [
                {
                    "expr": q["expr"],
                    "legendFormat": q.get("legend", ""),
                    "refId": chr(65 + i),
                    "datasource": {"type": "prometheus", "uid": "${datasource}"},
                }
                for i, q in enumerate(queries)
            ],
            "gridPos": {"h": height, "w": width, "x": x_pos, "y": y_pos},
            "fieldConfig": {
                "defaults": {
                    "unit": unit,
                    "custom": {
                        "drawStyle": "line",
                        "lineInterpolation": "linear",
                        "pointSize": 5,
                        "showPoints": "auto",
                    },
                },
                "overrides": [],
            },
            "options": {
                "legend": {"displayMode": "list", "placement": "bottom"},
                "tooltip": {"mode": "multi"},
            },
        }
    
    def _grafana_heatmap_panel(
        self,
        title: str,
        query: str,
        y_pos: int,
        x_pos: int = 0,
        width: int = 12,
    ) -> dict:
        """Create a heatmap panel."""
        return {
            "id": None,
            "title": title,
            "type": "heatmap",
            "targets": [
                {
                    "expr": query,
                    "refId": "A",
                    "datasource": {"type": "prometheus", "uid": "${datasource}"},
                    "format": "heatmap",
                }
            ],
            "gridPos": {"h": 7, "w": width, "x": x_pos, "y": y_pos},
            "heatmap": {},
            "dataFormat": "tsbuckets",
            "options": {},
        }
    
    def generate_html_dashboard(self, metrics: Optional[dict] = None) -> str:
        """
        Generate standalone HTML dashboard.
        
        Args:
            metrics: Current metrics data to display
            
        Returns:
            HTML string for the dashboard
        """
        metrics = metrics or {}
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.config.title}</title>
    <style>
        :root {{
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --accent-green: #22c55e;
            --accent-yellow: #eab308;
            --accent-red: #ef4444;
            --accent-blue: #3b82f6;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-color);
            color: var(--text-primary);
            padding: 20px;
            line-height: 1.6;
        }}
        
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--card-bg);
        }}
        
        .header h1 {{
            font-size: 24px;
            font-weight: 600;
        }}
        
        .last-updated {{
            color: var(--text-secondary);
            font-size: 14px;
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        
        .card {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        }}
        
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}
        
        .card-title {{
            font-size: 14px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .card-value {{
            font-size: 32px;
            font-weight: 700;
            margin: 8px 0;
        }}
        
        .card-trend {{
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 4px;
        }}
        
        .trend-up {{ color: var(--accent-green); }}
        .trend-down {{ color: var(--accent-red); }}
        .trend-neutral {{ color: var(--text-secondary); }}
        
        .status-indicator {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }}
        
        .status-healthy {{ background: var(--accent-green); box-shadow: 0 0 8px var(--accent-green); }}
        .status-warning {{ background: var(--accent-yellow); box-shadow: 0 0 8px var(--accent-yellow); }}
        .status-critical {{ background: var(--accent-red); box-shadow: 0 0 8px var(--accent-red); animation: pulse 2s infinite; }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        .section {{
            margin-bottom: 32px;
        }}
        
        .section-title {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .alerts-list {{
            background: var(--card-bg);
            border-radius: 12px;
            overflow: hidden;
        }}
        
        .alert-item {{
            padding: 16px 20px;
            border-bottom: 1px solid var(--bg-color);
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .alert-item:last-child {{
            border-bottom: none;
        }}
        
        .alert-severity {{
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .severity-critical {{ background: rgba(239, 68, 68, 0.2); color: var(--accent-red); }}
        .severity-warning {{ background: rgba(234, 179, 8, 0.2); color: var(--accent-yellow); }}
        .severity-info {{ background: rgba(59, 130, 246, 0.2); color: var(--accent-blue); }}
        
        .chart-container {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 20px;
            height: 300px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-secondary);
        }}
        
        .refresh-btn {{
            background: var(--accent-blue);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
        }}
        
        .refresh-btn:hover {{
            opacity: 0.9;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔮 {self.config.title}</h1>
        <div style="display: flex; align-items: center; gap: 16px;">
            <span class="last-updated">Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</span>
            <button class="refresh-btn" onclick="location.reload()">Refresh</button>
        </div>
    </div>
    
    <div class="section">
        <div class="section-title">
            <span class="status-indicator status-healthy"></span>
            System Overview
        </div>
        <div class="grid">
            {self._generate_overview_cards(metrics)}
        </div>
    </div>
    
    <div class="section">
        <div class="section-title">📊 Pipeline Metrics</div>
        <div class="grid">
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Records Processed (24h)</span>
                </div>
                <div class="card-value">{metrics.get('records_processed_24h', 'N/A'):,}</div>
                <div class="card-trend trend-up">↑ 12% from yesterday</div>
            </div>
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Success Rate</span>
                </div>
                <div class="card-value">{metrics.get('success_rate', 'N/A'):.1%}</div>
                <div class="card-trend trend-up">Target: 99%</div>
            </div>
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Avg Processing Time</span>
                </div>
                <div class="card-value">{metrics.get('avg_processing_time', 'N/A'):.2f}s</div>
                <div class="card-trend trend-neutral">Per record</div>
            </div>
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Active Alerts</span>
                </div>
                <div class="card-value">{metrics.get('active_alerts', 0)}</div>
                <div class="card-trend {'trend-down' if metrics.get('active_alerts', 0) > 0 else 'trend-neutral'}">
                    {metrics.get('active_alerts', 0)} requiring attention
                </div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <div class="section-title">🚨 Recent Alerts</div>
        <div class="alerts-list">
            {self._generate_alerts_list(metrics.get('recent_alerts', []))}
        </div>
    </div>
    
    <div class="section">
        <div class="section-title">📈 Stage Performance</div>
        <div class="grid">
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Extraction</span>
                    <span class="status-indicator status-healthy"></span>
                </div>
                <div class="card-value">{metrics.get('extraction_latency', 0):.2f}s</div>
                <div class="card-trend trend-neutral">avg latency</div>
            </div>
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Validation</span>
                    <span class="status-indicator status-healthy"></span>
                </div>
                <div class="card-value">{metrics.get('validation_latency', 0):.2f}s</div>
                <div class="card-trend trend-neutral">avg latency</div>
            </div>
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Transformation</span>
                    <span class="status-indicator status-healthy"></span>
                </div>
                <div class="card-value">{metrics.get('transformation_latency', 0):.2f}s</div>
                <div class="card-trend trend-neutral">avg latency</div>
            </div>
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Storage</span>
                    <span class="status-indicator status-healthy"></span>
                </div>
                <div class="card-value">{metrics.get('storage_latency', 0):.2f}s</div>
                <div class="card-trend trend-neutral">avg latency</div>
            </div>
        </div>
    </div>
    
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>"""
        return html
    
    def _generate_overview_cards(self, metrics: dict) -> str:
        """Generate overview status cards HTML."""
        health = metrics.get('health', {})
        health_status = health.get('status', 'unknown')
        
        status_class = 'status-healthy' if health_status == 'healthy' else \
                      'status-warning' if health_status == 'degraded' else 'status-critical'
        
        cards = f"""
            <div class="card">
                <div class="card-header">
                    <span class="card-title">System Health</span>
                    <span class="status-indicator {status_class}"></span>
                </div>
                <div class="card-value" style="text-transform: capitalize;">{health_status}</div>
                <div class="card-trend trend-neutral">{len(health.get('issues', []))} issues</div>
            </div>
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Active Runs</span>
                </div>
                <div class="card-value">{metrics.get('active_runs', 0)}</div>
                <div class="card-trend trend-neutral">Pipeline instances</div>
            </div>
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Registry Size</span>
                </div>
                <div class="card-value">{metrics.get('registry_size', 0):,}</div>
                <div class="card-trend trend-neutral">Known records</div>
            </div>
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Data Quality</span>
                </div>
                <div class="card-value">{metrics.get('data_quality', 0):.0f}%</div>
                <div class="card-trend {'trend-up' if metrics.get('data_quality', 0) > 90 else 'trend-down'}">Overall score</div>
            </div>
        """
        return cards
    
    def _generate_alerts_list(self, alerts: list[dict]) -> str:
        """Generate alerts list HTML."""
        if not alerts:
            return '<div class="alert-item"><span class="alert-severity severity-info">INFO</span>No active alerts</div>'
        
        items = []
        for alert in alerts[:5]:  # Show last 5
            severity = alert.get('severity', 'info')
            items.append(f"""
                <div class="alert-item">
                    <span class="alert-severity severity-{severity}">{severity}</span>
                    <div>
                        <div style="font-weight: 600;">{alert.get('rule', 'Unknown')}</div>
                        <div style="font-size: 12px; color: var(--text-secondary);">{alert.get('message', '')}</div>
                    </div>
                    <div style="margin-left: auto; font-size: 12px; color: var(--text-secondary);">
                        {alert.get('time', 'Just now')}
                    </div>
                </div>
            """)
        
        return "\n".join(items)
    
    def export_grafana_json(self, path: str) -> None:
        """Export Grafana dashboard to JSON file."""
        dashboard = self.generate_grafana_dashboard()
        with open(path, 'w') as f:
            json.dump(dashboard, f, indent=2)
    
    def export_html(self, path: str, metrics: Optional[dict] = None) -> None:
        """Export HTML dashboard to file."""
        html = self.generate_html_dashboard(metrics)
        with open(path, 'w') as f:
            f.write(html)
