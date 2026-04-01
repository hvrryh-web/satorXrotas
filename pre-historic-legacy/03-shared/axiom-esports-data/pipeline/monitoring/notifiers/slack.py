"""
Slack Notifier — Send alerts to Slack channels.

Uses Slack Incoming Webhooks for simple integration.
Supports rich formatting with blocks for critical alerts.

Example:
    from pipeline.monitoring.notifiers import SlackNotifier
    
    notifier = SlackNotifier(webhook_url="https://hooks.slack.com/...")
    notifier.send(alert)
"""

import json
import logging
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError

logger = logging.getLogger(__name__)


class SlackNotifier:
    """Send notifications to Slack via webhook."""
    
    # Color mapping for severity
    SEVERITY_COLORS = {
        "critical": "#FF0000",  # Red
        "warning": "#FFA500",   # Orange
        "info": "#36A64F",      # Green
    }
    
    # Emoji mapping for severity
    SEVERITY_EMOJI = {
        "critical": "🚨",
        "warning": "⚠️",
        "info": "ℹ️",
    }
    
    def __init__(self, webhook_url: str, channel: str | None = None) -> None:
        """
        Initialize Slack notifier.
        
        Args:
            webhook_url: Slack incoming webhook URL
            channel: Optional channel override
        """
        self.webhook_url = webhook_url
        self.channel = channel
    
    def send(self, alert: Any) -> None:
        """
        Send alert to Slack.
        
        Args:
            alert: Alert object with rule, severity, message, context attributes
        """
        payload = self._build_payload(alert)
        self._send_request(payload)
    
    def _build_payload(self, alert: Any) -> dict:
        """Build Slack message payload."""
        severity = getattr(alert, "severity", "info")
        if hasattr(severity, "value"):
            severity = severity.value
        
        color = self.SEVERITY_COLORS.get(severity, "#808080")
        emoji = self.SEVERITY_EMOJI.get(severity, "📋")
        
        # Build context fields
        context = getattr(alert, "context", {})
        fields = []
        for key, value in list(context.items())[:8]:  # Limit fields
            fields.append({
                "title": key.replace("_", " ").title(),
                "value": str(value),
                "short": True,
            })
        
        # Build attachment
        attachment = {
            "color": color,
            "title": f"{emoji} Pipeline Alert: {getattr(alert, 'rule', 'Unknown')}",
            "text": getattr(alert, "message", ""),
            "fields": fields,
            "footer": "Axiom Pipeline Monitor",
            "ts": int(getattr(alert, "created_at", None).timestamp()) if hasattr(alert, "created_at") else None,
        }
        
        payload: dict[str, Any] = {
            "attachments": [attachment],
        }
        
        if self.channel:
            payload["channel"] = self.channel
        
        return payload
    
    def _send_request(self, payload: dict) -> None:
        """Send HTTP request to Slack webhook."""
        try:
            data = json.dumps(payload).encode("utf-8")
            req = Request(
                self.webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            
            with urlopen(req, timeout=30) as response:
                if response.status == 200:
                    logger.info("Slack notification sent successfully")
                else:
                    logger.warning(f"Slack returned status {response.status}")
                    
        except HTTPError as e:
            logger.error(f"Failed to send Slack notification: {e.code} {e.reason}")
            raise
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            raise
    
    def send_test_message(self) -> bool:
        """Send a test message to verify configuration."""
        try:
            test_payload = {
                "text": "🔧 Test message from Axiom Pipeline Monitor",
                "attachments": [{
                    "color": "#36A64F",
                    "text": "If you see this, Slack notifications are configured correctly!",
                }],
            }
            self._send_request(test_payload)
            return True
        except Exception as e:
            logger.error(f"Test message failed: {e}")
            return False
