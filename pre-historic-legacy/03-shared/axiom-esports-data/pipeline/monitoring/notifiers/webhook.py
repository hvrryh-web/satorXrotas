"""
Webhook Notifier — Send alerts to generic HTTP endpoints.

Supports POST requests to custom webhook URLs with configurable
payload format and authentication.

Example:
    from pipeline.monitoring.notifiers import WebhookNotifier
    
    notifier = WebhookNotifier(
        webhook_url="https://my-service.com/webhooks/alerts",
        headers={"Authorization": "Bearer token123"},
    )
    notifier.send(alert)
"""

import json
import logging
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError

logger = logging.getLogger(__name__)


class WebhookNotifier:
    """Send notifications to generic webhook endpoints."""
    
    def __init__(
        self,
        webhook_url: str,
        headers: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> None:
        """
        Initialize webhook notifier.
        
        Args:
            webhook_url: Target webhook URL
            headers: Additional HTTP headers
            timeout: Request timeout in seconds
        """
        self.webhook_url = webhook_url
        self.headers = headers or {}
        self.timeout = timeout
    
    def send(self, alert: Any) -> dict:
        """
        Send alert to webhook.
        
        Args:
            alert: Alert object
            
        Returns:
            Response dict with status
        """
        payload = self._build_payload(alert)
        return self._send_request(payload)
    
    def _build_payload(self, alert: Any) -> dict:
        """Build webhook payload."""
        severity = getattr(alert, "severity", "info")
        if hasattr(severity, "value"):
            severity = severity.value
        
        return {
            "source": "axiom-pipeline",
            "timestamp": getattr(alert, "created_at", None).isoformat() if hasattr(alert, "created_at") else None,
            "alert": {
                "rule": getattr(alert, "rule", "unknown"),
                "severity": severity,
                "message": getattr(alert, "message", ""),
                "run_id": getattr(alert, "run_id", None),
                "channels": getattr(alert, "channels", []),
            },
            "context": getattr(alert, "context", {}),
            "version": "1.0.0",
        }
    
    def _send_request(self, payload: dict) -> dict:
        """Send HTTP POST request to webhook."""
        data = json.dumps(payload, default=str).encode("utf-8")
        
        headers = {
            "Content-Type": "application/json",
            **self.headers,
        }
        
        try:
            req = Request(
                self.webhook_url,
                data=data,
                headers=headers,
                method="POST",
            )
            
            with urlopen(req, timeout=self.timeout) as response:
                response_body = response.read().decode()
                
                result = {
                    "success": True,
                    "status_code": response.status,
                    "response": response_body,
                }
                
                logger.info(f"Webhook notification sent: {response.status}")
                return result
                
        except HTTPError as e:
            logger.error(f"Webhook returned error: {e.code} {e.reason}")
            return {
                "success": False,
                "status_code": e.code,
                "error": str(e.reason),
            }
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    def send_custom(self, payload: dict) -> dict:
        """
        Send custom payload to webhook.
        
        Args:
            payload: Custom payload dict
            
        Returns:
            Response dict
        """
        return self._send_request(payload)
