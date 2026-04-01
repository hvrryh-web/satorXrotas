"""External services health check collector."""

from typing import List, Optional, Dict, Any
import asyncio

from .base import HealthCheckCollector
from ..models import HealthCheckResult, HealthStatus, CheckType, SystemComponent


class ExternalCollector(HealthCheckCollector):
    """Collects health checks for third-party/external services."""
    
    # Status page URLs for common services
    STATUS_PAGES = {
        "supabase": {
            "status_url": "https://status.supabase.com/api/v2/summary.json",
            "components": ["Database", "Auth", "Storage", "Realtime"]
        },
        "render": {
            "status_url": "https://status.render.com/api/v2/summary.json",
            "components": ["API", "Static Sites", "Web Services", "Databases"]
        },
        "vercel": {
            "status_url": "https://www.vercel-status.com/api/v2/summary.json",
            "components": ["Builds", "Deployments", "Edge Network", "Functions"]
        },
        "github": {
            "status_url": "https://www.githubstatus.com/api/v2/summary.json",
            "components": ["Git Operations", "API Requests", "Issues", "Actions"]
        },
    }
    
    def __init__(self, component: SystemComponent,
                 service_name: Optional[str] = None):
        super().__init__(component)
        self.service_name = service_name or self._infer_service_name()
    
    def _infer_service_name(self) -> str:
        """Infer service name from component ID or endpoint."""
        component_id = self.component.component_id.lower()
        
        for key in self.STATUS_PAGES.keys():
            if key in component_id:
                return key
        
        # Check endpoint
        if self.component.health_endpoint:
            endpoint = self.component.health_endpoint.lower()
            for key in self.STATUS_PAGES.keys():
                if key in endpoint:
                    return key
        
        return "unknown"
    
    async def collect(self) -> List[HealthCheckResult]:
        """Collect external service health metrics."""
        checks = []
        
        # Check status page if available
        if self.service_name in self.STATUS_PAGES:
            checks.append(await self._check_status_page())
        
        # Check direct endpoint connectivity
        if self.component.health_endpoint:
            checks.append(await self._check_endpoint())
        
        # If no specific checks configured, do a DNS lookup
        if not checks:
            checks.append(await self._check_dns())
        
        return checks
    
    async def _check_status_page(self) -> HealthCheckResult:
        """Check third-party status page API."""
        if self.service_name not in self.STATUS_PAGES:
            return HealthCheckResult(
                check_id=f"{self.component.component_id}_status_page",
                name="Status Page",
                layer=self.component.layer,
                check_type=CheckType.CONNECTIVITY,
                status=HealthStatus.UNKNOWN,
                message=f"No status page configured for {self.service_name}"
            )
        
        status_config = self.STATUS_PAGES[self.service_name]
        status_url = status_config["status_url"]
        
        try:
            async with self.session.get(status_url) as response:
                if response.status != 200:
                    return HealthCheckResult(
                        check_id=f"{self.component.component_id}_status_page",
                        name="Status Page",
                        layer=self.component.layer,
                        check_type=CheckType.CONNECTIVITY,
                        status=HealthStatus.UNKNOWN,
                        message=f"Status page returned {response.status}"
                    )
                
                data = await response.json()
                
                # Parse status page data
                page = data.get("page", {})
                status = data.get("status", {})
                components = data.get("components", [])
                incidents = data.get("incidents", [])
                
                overall_indicator = status.get("indicator", "none")
                overall_description = status.get("description", "Unknown")
                
                # Map status page indicator to our health status
                status_map = {
                    "none": HealthStatus.HEALTHY,
                    "minor": HealthStatus.DEGRADED,
                    "major": HealthStatus.CRITICAL,
                    "critical": HealthStatus.CRITICAL,
                    "maintenance": HealthStatus.MAINTENANCE
                }
                
                health_status = status_map.get(overall_indicator, HealthStatus.UNKNOWN)
                
                # Check specific components
                component_status = {}
                for comp in components:
                    comp_name = comp.get("name", "Unknown")
                    if any(c in comp_name for c in status_config["components"]):
                        comp_status = comp.get("status", "operational")
                        component_status[comp_name] = comp_status
                
                # Check for active incidents
                active_incidents = [
                    {
                        "name": inc.get("name"),
                        "impact": inc.get("impact"),
                        "status": inc.get("status")
                    }
                    for inc in incidents
                    if inc.get("status") != "resolved"
                ]
                
                return HealthCheckResult(
                    check_id=f"{self.component.component_id}_status_page",
                    name=f"{self.service_name.title()} Status Page",
                    layer=self.component.layer,
                    check_type=CheckType.DEPENDENCY,
                    status=health_status,
                    message=overall_description,
                    details={
                        "overall_status": overall_indicator,
                        "component_status": component_status,
                        "active_incidents": active_incidents,
                        "page_updated": page.get("updated_at")
                    }
                )
                
        except asyncio.TimeoutError:
            return HealthCheckResult(
                check_id=f"{self.component.component_id}_status_page",
                name="Status Page",
                layer=self.component.layer,
                check_type=CheckType.CONNECTIVITY,
                status=HealthStatus.UNKNOWN,
                message="Status page request timed out"
            )
        except Exception as e:
            return HealthCheckResult(
                check_id=f"{self.component.component_id}_status_page",
                name="Status Page",
                layer=self.component.layer,
                check_type=CheckType.CONNECTIVITY,
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check status page: {str(e)}"
            )
    
    async def _check_endpoint(self) -> HealthCheckResult:
        """Check direct endpoint connectivity."""
        # For external services, this is often a status page or docs page
        url = self.component.health_endpoint
        
        result = await self.check_http_endpoint(
            url=url,
            check_id=f"{self.component.component_id}_endpoint",
            check_name=f"{self.component.name} Endpoint",
            expected_status=200
        )
        
        # Adjust status - some external services return 403 for bot requests
        if result.status == HealthStatus.CRITICAL and result.message:
            if "403" in result.message:
                result.status = HealthStatus.HEALTHY
                result.message = "Endpoint accessible (403 is normal for some external services)"
        
        return result
    
    async def _check_dns(self) -> HealthCheckResult:
        """Check DNS resolution for the service."""
        import socket
        from urllib.parse import urlparse
        
        try:
            if self.component.health_endpoint:
                parsed = urlparse(self.component.health_endpoint)
                hostname = parsed.hostname
            else:
                hostname = f"{self.service_name}.com"
            
            if not hostname:
                return HealthCheckResult(
                    check_id=f"{self.component.component_id}_dns",
                    name="DNS Resolution",
                    layer=self.component.layer,
                    check_type=CheckType.CONNECTIVITY,
                    status=HealthStatus.UNKNOWN,
                    message="No hostname to resolve"
                )
            
            # Perform DNS lookup
            ip = socket.gethostbyname(hostname)
            
            return HealthCheckResult(
                check_id=f"{self.component.component_id}_dns",
                name="DNS Resolution",
                layer=self.component.layer,
                check_type=CheckType.CONNECTIVITY,
                status=HealthStatus.HEALTHY,
                message=f"{hostname} resolves to {ip}",
                details={
                    "hostname": hostname,
                    "ip_address": ip
                }
            )
            
        except socket.gaierror as e:
            return HealthCheckResult(
                check_id=f"{self.component.component_id}_dns",
                name="DNS Resolution",
                layer=self.component.layer,
                check_type=CheckType.CONNECTIVITY,
                status=HealthStatus.CRITICAL,
                message=f"DNS resolution failed: {str(e)}"
            )
        except Exception as e:
            return HealthCheckResult(
                check_id=f"{self.component.component_id}_dns",
                name="DNS Resolution",
                layer=self.component.layer,
                check_type=CheckType.CONNECTIVITY,
                status=HealthStatus.UNKNOWN,
                message=f"DNS check error: {str(e)}"
            )
    
    async def check_service_specific(self, custom_checks: Dict[str, Any]) -> List[HealthCheckResult]:
        """Run custom checks for specific services.
        
        Args:
            custom_checks: Dictionary of check_name -> check_config
        
        Returns:
            List of health check results
        """
        results = []
        
        for check_name, config in custom_checks.items():
            check_type = config.get("type", "http")
            
            if check_type == "http":
                url = config.get("url")
                if url:
                    result = await self.check_http_endpoint(
                        url=url,
                        check_id=f"{self.component.component_id}_{check_name}",
                        check_name=config.get("name", check_name),
                        expected_status=config.get("expected_status", 200)
                    )
                    results.append(result)
            
            elif check_type == "api":
                # Custom API check with response validation
                url = config.get("url")
                if url:
                    try:
                        async with self.session.get(url) as response:
                            data = await response.json()
                            
                            # Validate response against expected fields
                            expected = config.get("expected_fields", {})
                            validation_errors = []
                            
                            for field, expected_value in expected.items():
                                actual_value = self._get_nested_value(data, field)
                                if actual_value != expected_value:
                                    validation_errors.append(
                                        f"{field}: expected {expected_value}, got {actual_value}"
                                    )
                            
                            status = HealthStatus.HEALTHY if not validation_errors else HealthStatus.CRITICAL
                            
                            results.append(HealthCheckResult(
                                check_id=f"{self.component.component_id}_{check_name}",
                                check_name=config.get("name", check_name),
                                layer=self.component.layer,
                                check_type=CheckType.CUSTOM,
                                status=status,
                                message="; ".join(validation_errors) if validation_errors else "API response valid",
                                details={"response": data}
                            ))
                    except Exception as e:
                        results.append(HealthCheckResult(
                            check_id=f"{self.component.component_id}_{check_name}",
                            check_name=config.get("name", check_name),
                            layer=self.component.layer,
                            check_type=CheckType.CUSTOM,
                            status=HealthStatus.CRITICAL,
                            message=str(e)
                        ))
        
        return results
    
    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get a nested value from a dictionary using dot notation."""
        keys = path.split(".")
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value
