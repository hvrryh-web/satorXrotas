"""
Developer Dashboard Data Models
Defines the structure for health checks, system status, and maintenance data.
"""

from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Literal, Any
from enum import Enum


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
    MAINTENANCE = "maintenance"


class SystemLayer(str, Enum):
    """Dashboard layers for organizing systems."""
    INFRASTRUCTURE = "infrastructure"  # DB, Network, Storage
    API_SERVICES = "api_services"      # FastAPI, Coordinator
    DATA_PIPELINE = "data_pipeline"    # Extractors, Queue
    WEB_PLATFORM = "web_platform"      # Website, React App
    SIMULATION = "simulation"          # Godot, Game Systems
    SECURITY = "security"              # Firewall, Auth
    EXTERNAL = "external"              # Third-party services


class CheckType(str, Enum):
    """Types of health checks."""
    CONNECTIVITY = "connectivity"
    LATENCY = "latency"
    CAPACITY = "capacity"
    ERROR_RATE = "error_rate"
    DATA_FRESHNESS = "data_freshness"
    BUILD_STATUS = "build_status"
    DEPENDENCY = "dependency"
    CUSTOM = "custom"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class HealthCheckResult(BaseModel):
    """Result of a single health check."""
    check_id: str
    name: str
    layer: SystemLayer
    check_type: CheckType
    status: HealthStatus
    
    # Timing
    checked_at: datetime = Field(default_factory=datetime.utcnow)
    response_time_ms: Optional[float] = None
    
    # Details
    message: Optional[str] = None
    details: Dict[str, Any] = {}
    
    # Thresholds
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    actual_value: Optional[float] = None
    
    # History
    consecutive_failures: int = 0
    last_success_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


class SystemComponent(BaseModel):
    """A system component that can be monitored."""
    component_id: str
    name: str
    layer: SystemLayer
    description: Optional[str] = None
    
    # Dependencies
    depends_on: List[str] = []  # Other component IDs
    
    # Endpoints
    health_endpoint: Optional[str] = None
    metrics_endpoint: Optional[str] = None
    
    # Configuration
    check_interval_seconds: int = 60
    timeout_seconds: int = 10
    retries: int = 3
    
    # Metadata
    owner: Optional[str] = None  # Team/person responsible
    documentation_url: Optional[str] = None


class SystemStatus(BaseModel):
    """Aggregated status for a system component."""
    component: SystemComponent
    overall_status: HealthStatus
    
    # Latest checks
    checks: List[HealthCheckResult] = []
    last_check_at: Optional[datetime] = None
    
    # Aggregated metrics
    uptime_percentage_24h: Optional[float] = None
    avg_response_time_ms: Optional[float] = None
    error_rate_1h: Optional[float] = None
    
    # Alerts
    active_alerts: int = 0
    last_alert_at: Optional[datetime] = None


class DashboardView(BaseModel):
    """A dashboard view configuration."""
    view_id: str
    name: str
    description: Optional[str] = None
    
    # Filter
    layers: List[SystemLayer] = []
    components: List[str] = []  # Specific component IDs
    
    # Display
    layout: Literal["grid", "list", "hierarchy"] = "grid"
    refresh_interval_seconds: int = 30
    
    # Permissions
    allowed_roles: List[str] = ["developer", "admin"]


class MaintenanceWindow(BaseModel):
    """Scheduled maintenance window."""
    window_id: str
    title: str
    description: Optional[str] = None
    
    # Timing
    start_time: datetime
    end_time: datetime
    timezone: str = "UTC"
    
    # Affected systems
    affected_layers: List[SystemLayer] = []
    affected_components: List[str] = []
    
    # Status
    status: Literal["scheduled", "in_progress", "completed", "cancelled"] = "scheduled"
    
    # Notification
    notify_before_minutes: List[int] = [60, 15]
    notifications_sent: List[datetime] = []
    
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AlertRule(BaseModel):
    """Rule for generating alerts."""
    rule_id: str
    name: str
    
    # Condition
    component_id: Optional[str] = None
    layer: Optional[SystemLayer] = None
    check_type: Optional[CheckType] = None
    
    # Threshold
    condition: Literal["status_change", "threshold_exceeded", "consecutive_failures"]
    threshold: Optional[float] = None
    consecutive_count: Optional[int] = None
    
    # Severity
    severity: Severity
    
    # Notification
    channels: List[Literal["email", "slack", "pagerduty", "webhook"]] = []
    recipients: List[str] = []
    
    # Cooldown
    cooldown_minutes: int = 15
    last_triggered_at: Optional[datetime] = None


class DashboardSummary(BaseModel):
    """High-level dashboard summary."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Overall status
    overall_status: HealthStatus
    
    # Layer summaries
    layer_status: Dict[SystemLayer, HealthStatus] = {}
    
    # Component counts
    total_components: int = 0
    healthy_count: int = 0
    degraded_count: int = 0
    critical_count: int = 0
    maintenance_count: int = 0
    
    # Active issues
    active_alerts: int = 0
    maintenance_windows_active: int = 0
    failed_checks_1h: int = 0
    
    # Recent activity
    last_deployment: Optional[datetime] = None
    last_incident: Optional[datetime] = None


class MetricSeries(BaseModel):
    """Time-series metric data."""
    metric_name: str
    component_id: str
    
    # Data points
    timestamps: List[datetime]
    values: List[float]
    
    # Metadata
    unit: Optional[str] = None
    labels: Dict[str, str] = {}
