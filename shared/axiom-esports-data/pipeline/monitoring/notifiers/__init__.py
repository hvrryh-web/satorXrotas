"""
Notifiers — Alert notification channels.

Available notifiers:
    - SlackNotifier: Slack webhook notifications
    - GitHubNotifier: Create GitHub issues
    - WebhookNotifier: Generic HTTP webhooks
    - PagerDutyNotifier: On-call paging

Example:
    from pipeline.monitoring.notifiers import SlackNotifier
    
    slack = SlackNotifier(webhook_url="https://hooks.slack.com/...")
    slack.send(alert)
"""

from pipeline.monitoring.notifiers.slack import SlackNotifier
from pipeline.monitoring.notifiers.github import GitHubNotifier
from pipeline.monitoring.notifiers.webhook import WebhookNotifier

__all__ = [
    "SlackNotifier",
    "GitHubNotifier",
    "WebhookNotifier",
]

# Optional PagerDuty notifier
try:
    from pipeline.monitoring.notifiers.pagerduty import PagerDutyNotifier
    __all__.append("PagerDutyNotifier")
except ImportError:
    pass
