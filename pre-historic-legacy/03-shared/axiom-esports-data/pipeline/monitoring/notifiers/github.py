"""
GitHub Notifier — Create GitHub issues for critical alerts.

Creates GitHub issues for pipeline failures and critical alerts.
Prevents duplicate issues by checking for existing open issues
with the same alert rule.

Example:
    from pipeline.monitoring.notifiers import GitHubNotifier
    
    notifier = GitHubNotifier(
        token="ghp_...",
        repo="owner/repo",
    )
    notifier.send(alert)
"""

import json
import logging
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError

logger = logging.getLogger(__name__)


class GitHubNotifier:
    """Create GitHub issues for critical alerts."""
    
    # Issue labels by severity
    SEVERITY_LABELS = {
        "critical": ["pipeline", "critical", "alert"],
        "warning": ["pipeline", "warning", "alert"],
        "info": ["pipeline", "info"],
    }
    
    def __init__(
        self,
        token: str,
        repo: str,
        create_for_severity: list[str] | None = None,
    ) -> None:
        """
        Initialize GitHub notifier.
        
        Args:
            token: GitHub personal access token
            repo: Repository in "owner/repo" format
            create_for_severity: Only create issues for these severities
        """
        self.token = token
        self.repo = repo
        self.create_for_severity = set(create_for_severity or ["critical"])
        self.api_base = f"https://api.github.com/repos/{repo}"
    
    def send(self, alert: Any) -> dict | None:
        """
        Create GitHub issue for alert if appropriate.
        
        Args:
            alert: Alert object
            
        Returns:
            Created issue dict or None if skipped
        """
        severity = getattr(alert, "severity", "info")
        if hasattr(severity, "value"):
            severity = severity.value
        
        # Only create issues for configured severities
        if severity not in self.create_for_severity:
            logger.debug(f"Skipping GitHub issue for {severity} alert")
            return None
        
        # Check for existing open issue
        rule = getattr(alert, "rule", "unknown")
        if self._issue_exists(rule):
            logger.info(f"GitHub issue already exists for rule: {rule}")
            return None
        
        # Create new issue
        return self._create_issue(alert)
    
    def _issue_exists(self, rule: str) -> bool:
        """Check if an open issue already exists for this rule."""
        try:
            # Search for open issues with the alert rule in title
            url = f"{self.api_base}/issues?state=open&labels=pipeline,alert"
            
            req = Request(
                url,
                headers={
                    "Authorization": f"token {self.token}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            
            with urlopen(req, timeout=30) as response:
                issues = json.loads(response.read().decode())
                for issue in issues:
                    if rule in issue.get("title", ""):
                        return True
                return False
                
        except Exception as e:
            logger.warning(f"Failed to check for existing issues: {e}")
            return False
    
    def _create_issue(self, alert: Any) -> dict:
        """Create a new GitHub issue."""
        severity = getattr(alert, "severity", "info")
        if hasattr(severity, "value"):
            severity = severity.value
        
        title = f"[Pipeline Alert] {getattr(alert, 'rule', 'Unknown')}"
        
        # Build issue body
        body_lines = [
            f"## Alert Details",
            f"",
            f"**Rule:** {getattr(alert, 'rule', 'Unknown')}",
            f"**Severity:** {severity.upper()}",
            f"**Time:** {getattr(alert, 'created_at', 'Unknown')}",
            f"**Run ID:** {getattr(alert, 'run_id', 'Unknown')}",
            f"",
            f"## Message",
            f"{getattr(alert, 'message', 'No message')}",
            f"",
            f"## Context",
            f"```json",
            json.dumps(getattr(alert, "context", {}), indent=2),
            f"```",
            f"",
            f"---",
            f"*This issue was created automatically by the Axiom Pipeline Monitor*",
        ]
        
        payload = {
            "title": title,
            "body": "\n".join(body_lines),
            "labels": self.SEVERITY_LABELS.get(severity, ["pipeline", "alert"]),
        }
        
        try:
            req = Request(
                f"{self.api_base}/issues",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"token {self.token}",
                    "Accept": "application/vnd.github.v3+json",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            
            with urlopen(req, timeout=30) as response:
                issue = json.loads(response.read().decode())
                logger.info(f"Created GitHub issue #{issue['number']}: {issue['html_url']}")
                return issue
                
        except HTTPError as e:
            logger.error(f"Failed to create GitHub issue: {e.code} {e.reason}")
            raise
        except Exception as e:
            logger.error(f"Failed to create GitHub issue: {e}")
            raise
    
    def close_issue(self, rule: str) -> bool:
        """
        Close an issue for a resolved alert rule.
        
        Args:
            rule: Alert rule name
            
        Returns:
            True if an issue was closed
        """
        try:
            # Find the issue
            url = f"{self.api_base}/issues?state=open&labels=pipeline,alert"
            
            req = Request(
                url,
                headers={
                    "Authorization": f"token {self.token}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            
            with urlopen(req, timeout=30) as response:
                issues = json.loads(response.read().decode())
                for issue in issues:
                    if rule in issue.get("title", ""):
                        # Close the issue
                        close_req = Request(
                            f"{self.api_base}/issues/{issue['number']}",
                            data=json.dumps({"state": "closed"}).encode("utf-8"),
                            headers={
                                "Authorization": f"token {self.token}",
                                "Accept": "application/vnd.github.v3+json",
                                "Content-Type": "application/json",
                            },
                            method="PATCH",
                        )
                        
                        with urlopen(close_req, timeout=30):
                            logger.info(f"Closed GitHub issue #{issue['number']}")
                            return True
                        
            return False
            
        except Exception as e:
            logger.error(f"Failed to close GitHub issue: {e}")
            return False
