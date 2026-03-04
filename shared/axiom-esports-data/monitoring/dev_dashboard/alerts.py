"""
Alert Management System
Monitors health checks and generates alerts based on rules.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import asyncpg
import logging
import uuid

from .models import (
    AlertRule, HealthCheckResult, HealthStatus, 
    Severity, SystemLayer, CheckType
)

logger = logging.getLogger(__name__)


class Alert:
    """An active alert."""
    
    def __init__(
        self,
        alert_id: str,
        rule_id: str,
        component_id: str,
        severity: Severity,
        message: str,
        details: Dict,
        triggered_at: datetime
    ):
        self.alert_id = alert_id
        self.rule_id = rule_id
        self.component_id = component_id
        self.severity = severity
        self.message = message
        self.details = details
        self.triggered_at = triggered_at
        self.acknowledged_at: Optional[datetime] = None
        self.resolved_at: Optional[datetime] = None


class AlertManager:
    """
    Manages alert rules and generates alerts.
    Handles alert deduplication and notification routing.
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.active_alerts: Dict[str, Alert] = {}
        self._monitor_task = None
        self._running = False
    
    async def start(self):
        """Start the alert monitor."""
        self._running = True
        # Load active alerts from database
        await self._load_active_alerts()
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Alert manager started")
    
    async def stop(self):
        """Stop the alert monitor."""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Alert manager stopped")
    
    async def _load_active_alerts(self):
        """Load active alerts from database."""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM active_alerts
                WHERE resolved_at IS NULL
                """
            )
            for row in rows:
                alert = Alert(
                    alert_id=row['id'],
                    rule_id=row['rule_id'],
                    component_id=row['component_id'],
                    severity=Severity(row['severity']),
                    message=row['message'],
                    details=row['details'],
                    triggered_at=row['triggered_at']
                )
                alert.acknowledged_at = row.get('acknowledged_at')
                self.active_alerts[alert.alert_id] = alert
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                # Get recent health check results
                results = await self._get_recent_results()
                
                # Load alert rules
                rules = await self._get_alert_rules()
                
                # Evaluate rules against results
                for result in results:
                    for rule in rules:
                        if self._rule_applies(rule, result):
                            if self._check_condition(rule, result):
                                await self._trigger_alert(rule, result)
                
                # Auto-resolve recovered alerts
                await self._auto_resolve(results)
                
            except Exception as e:
                logger.exception("Alert monitor error")
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def _get_recent_results(self, minutes: int = 5) -> List[HealthCheckResult]:
        """Get health check results from last N minutes."""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM component_health_history
                WHERE recorded_at > NOW() - $1::INTERVAL
                ORDER BY recorded_at DESC
                """,
                f"{minutes} minutes"
            )
            results = []
            for row in rows:
                # Convert stored checks JSON to HealthCheckResult objects
                checks = row.get('checks', [])
                if checks:
                    for check in checks:
                        results.append(HealthCheckResult(
                            check_id=check.get('check_id', str(uuid.uuid4())),
                            name=check.get('name', 'unknown'),
                            layer=SystemLayer(row['layer']),
                            check_type=CheckType(check.get('check_type', 'custom')),
                            status=HealthStatus(check.get('status', 'unknown')),
                            checked_at=row['recorded_at'],
                            response_time_ms=check.get('response_time_ms'),
                            message=check.get('message'),
                            details=check.get('details', {}),
                            actual_value=check.get('actual_value'),
                            consecutive_failures=check.get('consecutive_failures', 0)
                        ))
            return results
    
    async def _get_alert_rules(self) -> List[AlertRule]:
        """Get all active alert rules."""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM alert_rules WHERE enabled = TRUE"
            )
            return [self._row_to_rule(row) for row in rows]
    
    def _row_to_rule(self, row) -> AlertRule:
        """Convert database row to AlertRule model."""
        return AlertRule(
            rule_id=row['rule_id'],
            name=row['name'],
            component_id=row['component_id'],
            layer=SystemLayer(row['layer']) if row['layer'] else None,
            check_type=CheckType(row['check_type']) if row['check_type'] else None,
            condition=row['condition_type'],
            threshold=row.get('critical_threshold') or row.get('warning_threshold'),
            consecutive_count=row['consecutive_count'],
            severity=Severity(row['severity']),
            channels=row.get('notify_channels', []),
            recipients=row.get('notify_recipients', []),
            cooldown_minutes=row['cooldown_minutes'],
            last_triggered_at=row.get('last_triggered_at')
        )
    
    def _rule_applies(self, rule: AlertRule, result: HealthCheckResult) -> bool:
        """Check if rule applies to this health check result."""
        if rule.component_id and rule.component_id != result.component_id:
            return False
        if rule.layer and rule.layer != result.layer:
            return False
        if rule.check_type and rule.check_type != result.check_type:
            return False
        return True
    
    def _check_condition(
        self,
        rule: AlertRule,
        result: HealthCheckResult
    ) -> bool:
        """Evaluate alert condition."""
        if rule.condition == "status_change":
            # Trigger on any status change to non-healthy
            return result.status in [HealthStatus.CRITICAL, HealthStatus.DEGRADED]
        
        elif rule.condition == "threshold_exceeded":
            if result.actual_value is None or rule.threshold is None:
                return False
            return result.actual_value > rule.threshold
        
        elif rule.condition == "consecutive_failures":
            if rule.consecutive_count is None:
                return False
            return result.consecutive_failures >= rule.consecutive_count
        
        return False
    
    async def _trigger_alert(
        self,
        rule: AlertRule,
        result: HealthCheckResult
    ):
        """Trigger an alert."""
        # Check cooldown
        if rule.last_triggered_at:
            cooldown_end = rule.last_triggered_at + timedelta(
                minutes=rule.cooldown_minutes
            )
            if datetime.utcnow() < cooldown_end:
                return  # Still in cooldown
        
        # Create alert ID
        alert_id = f"{rule.rule_id}:{result.component_id}:{int(datetime.utcnow().timestamp())}"
        
        # Check if similar alert already active
        for alert in self.active_alerts.values():
            if alert.rule_id == rule.rule_id and alert.component_id == result.component_id:
                return  # Already have active alert for this
        
        # Create alert
        alert = Alert(
            alert_id=alert_id,
            rule_id=rule.rule_id,
            component_id=result.component_id,
            severity=rule.severity,
            message=self._format_alert_message(rule, result),
            details={
                "check_name": result.name,
                "check_type": result.check_type,
                "actual_value": result.actual_value,
                "message": result.message
            },
            triggered_at=datetime.utcnow()
        )
        
        self.active_alerts[alert_id] = alert
        
        # Persist to database
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO active_alerts (
                    id, rule_id, component_id, severity,
                    message, details, triggered_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                alert_id,
                rule.rule_id,
                result.component_id,
                rule.severity.value,
                alert.message,
                alert.details,
                alert.triggered_at
            )
            
            # Update rule last_triggered
            await conn.execute(
                """
                UPDATE alert_rules
                SET last_triggered_at = NOW(),
                    trigger_count = trigger_count + 1
                WHERE rule_id = $1
                """,
                rule.rule_id
            )
        
        # Send notification
        await self._send_notification(alert, rule)
        
        logger.warning(f"ALERT triggered: {alert.message}")
    
    def _format_alert_message(
        self,
        rule: AlertRule,
        result: HealthCheckResult
    ) -> str:
        """Format human-readable alert message."""
        if rule.condition == "status_change":
            return f"{result.name} is {result.status.value}"
        elif rule.condition == "threshold_exceeded":
            return f"{result.name} exceeded threshold: {result.actual_value:.2f} > {rule.threshold}"
        elif rule.condition == "consecutive_failures":
            return f"{result.name} failed {result.consecutive_failures} times consecutively"
        return f"Alert: {result.name}"
    
    async def _send_notification(self, alert: Alert, rule: AlertRule):
        """Send notification through configured channels."""
        for channel in rule.channels:
            if channel == "slack":
                await self._send_slack_notification(alert)
            elif channel == "email":
                await self._send_email_notification(alert)
            elif channel == "pagerduty":
                await self._send_pagerduty_notification(alert)
            elif channel == "webhook":
                await self._send_webhook_notification(alert)
    
    async def _send_slack_notification(self, alert: Alert):
        """Send Slack notification."""
        # TODO: Implement Slack webhook
        logger.info(f"Would send Slack notification: {alert.message}")
    
    async def _send_email_notification(self, alert: Alert):
        """Send email notification."""
        # TODO: Implement email
        logger.info(f"Would send email notification: {alert.message}")
    
    async def _send_pagerduty_notification(self, alert: Alert):
        """Send PagerDuty notification."""
        # TODO: Implement PagerDuty integration
        logger.info(f"Would send PagerDuty notification: {alert.message}")
    
    async def _send_webhook_notification(self, alert: Alert):
        """Send webhook notification."""
        # TODO: Implement webhook
        logger.info(f"Would send webhook notification: {alert.message}")
    
    async def _auto_resolve(self, recent_results: List[HealthCheckResult]):
        """Auto-resolve alerts when conditions recover."""
        for alert in list(self.active_alerts.values()):
            # Find latest result for this component
            latest = next(
                (r for r in recent_results if r.component_id == alert.component_id),
                None
            )
            
            if latest and latest.status == HealthStatus.HEALTHY:
                await self.resolve_alert(alert.alert_id, "Auto-resolved: system recovered")
    
    async def resolve_alert(
        self,
        alert_id: str,
        resolution_note: str
    ) -> bool:
        """Manually or automatically resolve an alert."""
        if alert_id not in self.active_alerts:
            return False
        
        alert = self.active_alerts[alert_id]
        alert.resolved_at = datetime.utcnow()
        
        # Update database
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE active_alerts
                SET resolved_at = NOW(),
                    resolution_note = $2
                WHERE id = $1
                """,
                alert_id,
                resolution_note
            )
        
        del self.active_alerts[alert_id]
        logger.info(f"ALERT resolved: {alert_id}")
        return True
    
    async def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str
    ) -> bool:
        """Acknowledge an alert."""
        if alert_id not in self.active_alerts:
            return False
        
        alert = self.active_alerts[alert_id]
        alert.acknowledged_at = datetime.utcnow()
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE active_alerts
                SET acknowledged_at = NOW(),
                    acknowledged_by = $2
                WHERE id = $1
                """,
                alert_id,
                acknowledged_by
            )
        
        return True
    
    def get_active_alerts(
        self,
        severity: Optional[Severity] = None
    ) -> List[Alert]:
        """Get currently active alerts."""
        alerts = list(self.active_alerts.values())
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return sorted(alerts, key=lambda a: a.triggered_at, reverse=True)
    
    async def create_alert_rule(self, rule: AlertRule) -> AlertRule:
        """Create a new alert rule."""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO alert_rules (
                    rule_id, name, component_id, layer, check_type,
                    condition_type, warning_threshold, critical_threshold,
                    consecutive_count, severity,
                    notify_channels, notify_recipients, cooldown_minutes,
                    created_by
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                RETURNING *
                """,
                rule.rule_id,
                rule.name,
                rule.component_id,
                rule.layer.value if rule.layer else None,
                rule.check_type.value if rule.check_type else None,
                rule.condition,
                rule.threshold if rule.condition == "threshold_exceeded" else None,
                rule.threshold if rule.condition == "threshold_exceeded" else None,
                rule.consecutive_count,
                rule.severity.value,
                rule.channels,
                rule.recipients,
                rule.cooldown_minutes,
                "system"  # Default created_by
            )
            return self._row_to_rule(row)
    
    async def delete_alert_rule(self, rule_id: str) -> bool:
        """Delete an alert rule."""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM alert_rules WHERE rule_id = $1",
                rule_id
            )
            return 'DELETE 1' in result
    
    async def disable_alert_rule(self, rule_id: str) -> bool:
        """Disable an alert rule."""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE alert_rules SET enabled = FALSE WHERE rule_id = $1",
                rule_id
            )
            return 'UPDATE 1' in result
    
    async def enable_alert_rule(self, rule_id: str) -> bool:
        """Enable an alert rule."""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE alert_rules SET enabled = TRUE WHERE rule_id = $1",
                rule_id
            )
            return 'UPDATE 1' in result
