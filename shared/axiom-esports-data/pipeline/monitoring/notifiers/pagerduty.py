"""
PagerDuty Notifier — Send critical alerts to PagerDuty.

Integrates with PagerDuty Events API v2 for on-call paging.
Only recommended for critical alerts that require immediate response.

Example:
    from pipeline.monitoring.notifiers import PagerDutyNotifier
    
    notifier = PagerDutyNotifier(integration_key="your-key")
    notifier.send(alert)
"""

import json
import logging
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError

logger = logging.getLogger(__name__)


class PagerDutyNotifier:
    """Send critical alerts to PagerDuty."""
    
    EVENTS_API_URL = "https://events.pagerduty.com/v2/enqueue"
    
    # Severity mapping to PagerDuty severity
    SEVERITY_MAP = {
        "critical": "critical",
        "warning": "warning",
        "info": "info",
    }
    
    def __init__(
        self,
        integration_key: str,
        source: str = "axiom-pipeline",
    ) -> None:
        """
        Initialize PagerDuty notifier.
        
        Args:
            integration_key: PagerDuty integration key (routing key)
            source: Source identifier for events
        """
        self.integration_key = integration_key
        self.source = source
    
    def send(self, alert: Any) -> dict:
        """
        Send alert to PagerDuty.
        
        Args:
            alert: Alert object
            
        Returns:
            Response dict from PagerDuty
        """
        severity = getattr(alert, "severity", "info")
        if hasattr(severity, "value"):
            severity = severity.value
        
        # Only send critical and warning to PagerDuty
        if severity not in ("critical", "warning"):
            logger.debug(f"Skipping PagerDuty for {severity} alert")
            return {"skipped": True, "reason": f"Severity {severity} not sent to PagerDuty"}
        
        payload = self._build_payload(alert)
        return self._send_request(payload)
    
    def _build_payload(self, alert: Any) -> dict:
        """Build PagerDuty event payload."""
        severity = getattr(alert, "severity", "info")
        if hasattr(severity, "value"):
            severity = severity.value
        
        rule = getattr(alert, "rule", "unknown")
        message = getattr(alert, "message", "")
        run_id = getattr(alert, "run_id", "unknown")
        context = getattr(alert, "context", {})
        
        # Build custom details
        custom_details = {
            "rule": rule,
            "run_id": run_id,
            **context,
        }
        
        # Dedup key based on rule and run
        dedup_key = f"axiom-{rule}-{run_id}"
        
        return {
            "routing_key": self.integration_key,
            "event_action": "trigger",
            "dedup_key": dedup_key,
            "payload": {
                "summary": f"[Axiom Pipeline] {rule}: {message[:100]}",
                "severity": self.SEVERITY_MAP.get(severity, "warning"),
                "source": self.source,
                "component": "pipeline",
                "group": "data-pipeline",
                "class": rule,
                "custom_details": custom_details,
            },
        }
    
    def _send_request(self, payload: dict) -> dict:
        """Send event to PagerDuty Events API."""
        try:
            data = json.dumps(payload).encode("utf-8")
            
            req = Request(
                self.EVENTS_API_URL,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            
            with urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode())
                
                if result.get("status") == "success":
                    logger.info(f"PagerDuty event sent: {result.get('dedup_key')}")
                else:
                    logger.warning(f"PagerDuty returned: {result}")
                
                return result
                
        except HTTPError as e:
            error_body = e.read().decode()
            logger.error(f"PagerDuty API error: {e.code} - {error_body}")
            return {
                "status": "error",
                "error": error_body,
            }
        except Exception as e:
            logger.error(f"Failed to send PagerDuty event: {e}")
            return {
                "status": "error",
                "error": str(e),
            }
    
    def resolve(self, dedup_key: str) -> dict:
        """
        Resolve a previously triggered alert.
        
        Args:
            dedup_key: The deduplication key of the alert to resolve
            
        Returns:
            Response dict from PagerDuty
        """
        payload = {
            "routing_key": self.integration_key,
            "event_action": "resolve",
            "dedup_key": dedup_key,
        }
        
        return self._send_request(payload)
    
    def acknowledge(self, dedup_key: str) -> dict:
        """
        Acknowledge a triggered alert.
        
        Args:
            dedup_key: The deduplication key of the alert to acknowledge
            
        Returns:
            Response dict from PagerDuty
        """
        payload = {
            "routing_key": self.integration_key,
            "event_action": "acknowledge",
            "dedup_key": dedup_key,
        }
        
        return self._send_request(payload)
