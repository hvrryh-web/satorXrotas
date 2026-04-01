"""
Alert Manager — Alert routing system for the data pipeline.

Supports multiple notification channels:
    - Slack: Real-time notifications to channels
    - GitHub Issues: Create issues on critical failures
    - Email: SMTP-based email notifications
    - PagerDuty: On-call paging for critical alerts
    - Webhook: Generic HTTP webhook endpoints

Alert rules are evaluated against pipeline run state and routed
to appropriate channels based on severity.

Example:
    from pipeline.monitoring import AlertManager, AlertSeverity
    
    manager = AlertManager()
    
    # Check all rules against current run
    alerts = manager.check_alerts(run_instance)
    
    # Send alert manually
    manager.send_alert(Alert(
        rule="custom_check",
        severity=AlertSeverity.WARNING,
        message="Data volume below threshold",
        context={"expected": 1000, "actual": 500}
    ))
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Any, Callable
from pathlib import Path

from pipeline.monitoring.notifiers.slack import SlackNotifier
from pipeline.monitoring.notifiers.github import GitHubNotifier
from pipeline.monitoring.notifiers.webhook import WebhookNotifier

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    CRITICAL = "critical"  # Immediate action required
    WARNING = "warning"    # Attention needed soon
    INFO = "info"          # FYI, no action required


class AlertStatus(str, Enum):
    """Alert lifecycle status."""
    PENDING = "pending"
    FIRING = "firing"
    RESOLVED = "resolved"
    SILENCED = "silenced"


@dataclass
class Alert:
    """Single alert instance."""
    rule: str
    severity: AlertSeverity
    message: str
    context: dict[str, Any] = field(default_factory=dict)
    status: AlertStatus = AlertStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    run_id: Optional[str] = None
    channels: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert alert to dictionary."""
        return {
            "rule": self.rule,
            "severity": self.severity.value,
            "message": self.message,
            "context": self.context,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "run_id": self.run_id,
            "channels": self.channels,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Alert":
        """Create alert from dictionary."""
        return cls(
            rule=data["rule"],
            severity=AlertSeverity(data["severity"]),
            message=data["message"],
            context=data.get("context", {}),
            status=AlertStatus(data.get("status", "pending")),
            created_at=datetime.fromisoformat(data["created_at"]),
            resolved_at=datetime.fromisoformat(data["resolved_at"]) if data.get("resolved_at") else None,
            run_id=data.get("run_id"),
            channels=data.get("channels", []),
        )


@dataclass
class RunInstance:
    """Pipeline run instance for alert evaluation."""
    run_id: str
    status: str  # running, completed, failed
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    records_processed: int = 0
    records_failed: int = 0
    error_count: int = 0
    validation_failure_rate: float = 0.0
    duplicate_rate: float = 0.0
    stage: Optional[str] = None
    error_type: Optional[str] = None
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate."""
        total = self.records_processed + self.records_failed
        if total == 0:
            return 0.0
        return self.records_failed / total


@dataclass
class AlertRule:
    """Alert rule definition."""
    name: str
    condition: str  # Python expression to evaluate
    severity: AlertSeverity
    channels: list[str]
    message_template: str
    cooldown_minutes: int = 60  # Minimum time between repeated alerts
    enabled: bool = True
    
    def evaluate(self, run: RunInstance) -> bool:
        """Evaluate the rule condition against a run instance."""
        try:
            # Create safe evaluation context
            context = {
                "run": run,
                "status": run.status,
                "duration": run.duration_seconds,
                "error_rate": run.error_rate,
                "validation_failure_rate": run.validation_failure_rate,
                "duplicate_rate": run.duplicate_rate,
                "records_processed": run.records_processed,
                "records_failed": run.records_failed,
            }
            return bool(eval(self.condition, {"__builtins__": {}}, context))
        except Exception as e:
            logger.error(f"Error evaluating alert rule '{self.name}': {e}")
            return False


class AlertManager:
    """
    Alert routing system for pipeline monitoring.
    
    Evaluates alert rules against pipeline runs and routes
    notifications to appropriate channels.
    
    Built-in alert rules:
        - pipeline_failure: Run failed completely
        - high_error_rate: >10% error rate
        - data_quality_drop: >5% validation failures
        - stuck_pipeline: Running >1 hour
        - duplicate_surge: >20% duplicates detected
    """
    
    ALERT_RULES: dict[str, AlertRule] = {
        "pipeline_failure": AlertRule(
            name="pipeline_failure",
            condition='run.status == "failed"',
            severity=AlertSeverity.CRITICAL,
            channels=["slack", "github"],
            message_template="Pipeline run {run_id} failed at stage {stage}",
            cooldown_minutes=5,
        ),
        "high_error_rate": AlertRule(
            name="high_error_rate",
            condition="error_rate > 0.1 and records_processed > 100",
            severity=AlertSeverity.WARNING,
            channels=["slack"],
            message_template="High error rate ({error_rate:.1%}) in run {run_id}",
            cooldown_minutes=30,
        ),
        "data_quality_drop": AlertRule(
            name="data_quality_drop",
            condition="validation_failure_rate > 0.05 and records_processed > 50",
            severity=AlertSeverity.WARNING,
            channels=["slack", "email"],
            message_template="Data quality degraded: {validation_failure_rate:.1%} validation failures",
            cooldown_minutes=60,
        ),
        "stuck_pipeline": AlertRule(
            name="stuck_pipeline",
            condition="duration > 3600 and status == 'running'",
            severity=AlertSeverity.WARNING,
            channels=["slack"],
            message_template="Pipeline {run_id} stuck for {duration/60:.0f} minutes",
            cooldown_minutes=30,
        ),
        "duplicate_surge": AlertRule(
            name="duplicate_surge",
            condition="duplicate_rate > 0.2 and records_processed > 50",
            severity=AlertSeverity.INFO,
            channels=["slack"],
            message_template="High duplicate rate: {duplicate_rate:.1%}",
            cooldown_minutes=120,
        ),
        "no_recent_success": AlertRule(
            name="no_recent_success",
            condition="duration > 7200 and records_processed == 0",
            severity=AlertSeverity.CRITICAL,
            channels=["slack", "github", "pagerduty"],
            message_template="No successful pipeline runs in 2+ hours",
            cooldown_minutes=60,
        ),
    }
    
    def __init__(
        self,
        slack_webhook: Optional[str] = None,
        github_token: Optional[str] = None,
        github_repo: Optional[str] = None,
        pagerduty_key: Optional[str] = None,
        webhook_url: Optional[str] = None,
        alert_history_path: Optional[Path] = None,
    ) -> None:
        """
        Initialize alert manager with notification channels.
        
        Args:
            slack_webhook: Slack incoming webhook URL
            github_token: GitHub personal access token
            github_repo: GitHub repo (format: owner/repo)
            pagerduty_key: PagerDuty integration key
            webhook_url: Generic webhook URL
            alert_history_path: Path to store alert history
        """
        self.rules = dict(self.ALERT_RULES)
        self._alert_history: list[Alert] = []
        self._last_alert_time: dict[str, datetime] = {}
        self._alert_history_path = alert_history_path or Path("data/alerts/history.jsonl")
        
        # Initialize notifiers
        self._notifiers: dict[str, Any] = {}
        
        if slack_webhook or os.getenv("SLACK_WEBHOOK_URL"):
            self._notifiers["slack"] = SlackNotifier(
                webhook_url=slack_webhook or os.getenv("SLACK_WEBHOOK_URL")
            )
        
        if (github_token or os.getenv("GITHUB_TOKEN")) and \
           (github_repo or os.getenv("GITHUB_REPO")):
            self._notifiers["github"] = GitHubNotifier(
                token=github_token or os.getenv("GITHUB_TOKEN"),
                repo=github_repo or os.getenv("GITHUB_REPO"),
            )
        
        if pagerduty_key or os.getenv("PAGERDUTY_KEY"):
            from pipeline.monitoring.notifiers.pagerduty import PagerDutyNotifier
            self._notifiers["pagerduty"] = PagerDutyNotifier(
                integration_key=pagerduty_key or os.getenv("PAGERDUTY_KEY")
            )
        
        if webhook_url or os.getenv("ALERT_WEBHOOK_URL"):
            self._notifiers["webhook"] = WebhookNotifier(
                webhook_url=webhook_url or os.getenv("ALERT_WEBHOOK_URL")
            )
        
        # Load alert history
        self._load_history()
    
    def add_rule(self, rule: AlertRule) -> None:
        """Add a custom alert rule."""
        self.rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_rule(self, name: str) -> None:
        """Remove an alert rule."""
        if name in self.rules:
            del self.rules[name]
            logger.info(f"Removed alert rule: {name}")
    
    def check_alerts(self, run: RunInstance) -> list[Alert]:
        """
        Evaluate all alert rules against current run state.
        
        Args:
            run: Pipeline run instance to evaluate
            
        Returns:
            List of triggered alerts
        """
        triggered: list[Alert] = []
        
        for name, rule in self.rules.items():
            if not rule.enabled:
                continue
            
            # Check cooldown
            last_time = self._last_alert_time.get(name)
            if last_time:
                cooldown = rule.cooldown_minutes * 60
                if (datetime.utcnow() - last_time).total_seconds() < cooldown:
                    continue
            
            # Evaluate rule
            if rule.evaluate(run):
                # Format message
                context = {
                    "run_id": run.run_id,
                    "status": run.status,
                    "stage": run.stage,
                    "duration": run.duration_seconds,
                    "error_rate": run.error_rate,
                    "validation_failure_rate": run.validation_failure_rate,
                    "duplicate_rate": run.duplicate_rate,
                    "records_processed": run.records_processed,
                    "records_failed": run.records_failed,
                }
                message = rule.message_template.format(**context)
                
                alert = Alert(
                    rule=name,
                    severity=rule.severity,
                    message=message,
                    context=context,
                    status=AlertStatus.FIRING,
                    run_id=run.run_id,
                    channels=rule.channels,
                )
                
                triggered.append(alert)
                self._last_alert_time[name] = datetime.utcnow()
                
                # Send immediately
                self.send_alert(alert)
        
        return triggered
    
    def send_alert(self, alert: Alert) -> None:
        """
        Route alert to appropriate channels.
        
        Args:
            alert: Alert to send
        """
        self._alert_history.append(alert)
        
        for channel in alert.channels:
            notifier = self._notifiers.get(channel)
            if notifier:
                try:
                    notifier.send(alert)
                    logger.info(f"Sent alert '{alert.rule}' via {channel}")
                except Exception as e:
                    logger.error(f"Failed to send alert via {channel}: {e}")
            else:
                logger.warning(f"No notifier configured for channel: {channel}")
        
        # Persist to history
        self._save_history()
    
    def resolve_alert(self, rule_name: str, run_id: Optional[str] = None) -> None:
        """Mark alerts as resolved."""
        for alert in self._alert_history:
            if alert.rule == rule_name and alert.status == AlertStatus.FIRING:
                if run_id is None or alert.run_id == run_id:
                    alert.status = AlertStatus.RESOLVED
                    alert.resolved_at = datetime.utcnow()
                    logger.info(f"Resolved alert: {rule_name}")
        
        self._save_history()
    
    def silence_alert(self, rule_name: str, duration_minutes: int) -> None:
        """Silence an alert rule for a duration."""
        if rule_name in self.rules:
            self.rules[rule_name].enabled = False
            # Re-enable after duration
            # In production, use a scheduler
            logger.info(f"Silenced alert '{rule_name}' for {duration_minutes} minutes")
    
    def get_active_alerts(self) -> list[Alert]:
        """Get all currently firing alerts."""
        return [a for a in self._alert_history if a.status == AlertStatus.FIRING]
    
    def get_alert_history(
        self,
        severity: Optional[AlertSeverity] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[Alert]:
        """Get alert history with optional filtering."""
        alerts = self._alert_history
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if since:
            alerts = [a for a in alerts if a.created_at >= since]
        
        return sorted(alerts, key=lambda a: a.created_at, reverse=True)[:limit]
    
    def _load_history(self) -> None:
        """Load alert history from disk."""
        if self._alert_history_path.exists():
            try:
                with open(self._alert_history_path, "r") as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            self._alert_history.append(Alert.from_dict(data))
                logger.info(f"Loaded {len(self._alert_history)} alerts from history")
            except Exception as e:
                logger.warning(f"Failed to load alert history: {e}")
    
    def _save_history(self) -> None:
        """Save alert history to disk."""
        try:
            self._alert_history_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._alert_history_path, "w") as f:
                for alert in self._alert_history[-1000:]:  # Keep last 1000
                    f.write(json.dumps(alert.to_dict()) + "\n")
        except Exception as e:
            logger.warning(f"Failed to save alert history: {e}")
    
    def get_stats(self) -> dict:
        """Get alert statistics."""
        total = len(self._alert_history)
        active = len(self.get_active_alerts())
        by_severity: dict[str, int] = {}
        
        for alert in self._alert_history:
            sev = alert.severity.value
            by_severity[sev] = by_severity.get(sev, 0) + 1
        
        return {
            "total_alerts": total,
            "active_alerts": active,
            "by_severity": by_severity,
            "rules_configured": len(self.rules),
            "channels_configured": list(self._notifiers.keys()),
        }
