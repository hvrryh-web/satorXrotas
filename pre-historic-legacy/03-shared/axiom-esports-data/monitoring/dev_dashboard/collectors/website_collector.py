"""Website health check collector."""

from typing import List, Optional
from urllib.parse import urljoin

from .base import HealthCheckCollector
from ..models import HealthCheckResult, HealthStatus, CheckType, SystemComponent


class WebsiteCollector(HealthCheckCollector):
    """Collects health checks for static websites and React apps."""
    
    def __init__(self, component: SystemComponent, 
                 base_url: Optional[str] = None):
        super().__init__(component)
        self.base_url = base_url or component.health_endpoint
        self.base_url = self.base_url.rstrip('/') if self.base_url else None
    
    async def collect(self) -> List[HealthCheckResult]:
        """Collect website health metrics."""
        checks = []
        
        if not self.base_url:
            return [HealthCheckResult(
                check_id=f"{self.component.component_id}_no_url",
                name="Website URL",
                layer=self.component.layer,
                check_type=CheckType.CONNECTIVITY,
                status=HealthStatus.UNKNOWN,
                message="No base URL configured for website checks"
            )]
        
        # Basic connectivity
        checks.append(await self._check_connectivity())
        
        # SSL certificate check
        checks.append(await self._check_ssl())
        
        # Content check (ensure page loads with expected content)
        checks.append(await self._check_content())
        
        # Static assets check (CSS, JS)
        checks.append(await self._check_static_assets())
        
        # Response time check
        checks.append(await self._check_response_time())
        
        return checks
    
    async def _check_connectivity(self) -> HealthCheckResult:
        """Check basic website connectivity."""
        return await self.check_http_endpoint(
            url=self.base_url,
            check_id=f"{self.component.component_id}_connectivity",
            check_name="Website Connectivity",
            expected_status=200
        )
    
    async def _check_ssl(self) -> HealthCheckResult:
        """Check SSL certificate status."""
        import ssl
        import socket
        from datetime import datetime
        
        try:
            # Parse URL to get hostname
            from urllib.parse import urlparse
            parsed = urlparse(self.base_url)
            hostname = parsed.hostname
            port = parsed.port or 443
            
            if not hostname:
                return HealthCheckResult(
                    check_id=f"{self.component.component_id}_ssl",
                    name="SSL Certificate",
                    layer=self.component.layer,
                    check_type=CheckType.SECURITY,
                    status=HealthStatus.UNKNOWN,
                    message="Could not parse hostname from URL"
                )
            
            context = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Check expiration
                    not_after = cert.get('notAfter')
                    if not_after:
                        from datetime import datetime
                        expire_date = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                        days_until_expiry = (expire_date - datetime.utcnow()).days
                        
                        status = HealthStatus.HEALTHY
                        if days_until_expiry < 7:
                            status = HealthStatus.CRITICAL
                        elif days_until_expiry < 30:
                            status = HealthStatus.DEGRADED
                        
                        return HealthCheckResult(
                            check_id=f"{self.component.component_id}_ssl",
                            name="SSL Certificate",
                            layer=self.component.layer,
                            check_type=CheckType.SECURITY,
                            status=status,
                            actual_value=days_until_expiry,
                            warning_threshold=30,
                            critical_threshold=7,
                            details={
                                "expires": expire_date.isoformat(),
                                "days_remaining": days_until_expiry,
                                "issuer": cert.get('issuer', [])
                            }
                        )
            
            return HealthCheckResult(
                check_id=f"{self.component.component_id}_ssl",
                name="SSL Certificate",
                layer=self.component.layer,
                check_type=CheckType.SECURITY,
                status=HealthStatus.HEALTHY,
                message="SSL certificate valid"
            )
            
        except ssl.SSLError as e:
            return HealthCheckResult(
                check_id=f"{self.component.component_id}_ssl",
                name="SSL Certificate",
                layer=self.component.layer,
                check_type=CheckType.SECURITY,
                status=HealthStatus.CRITICAL,
                message=f"SSL Error: {str(e)}"
            )
        except Exception as e:
            return HealthCheckResult(
                check_id=f"{self.component.component_id}_ssl",
                name="SSL Certificate",
                layer=self.component.layer,
                check_type=CheckType.SECURITY,
                status=HealthStatus.UNKNOWN,
                message=f"Could not check SSL: {str(e)}"
            )
    
    async def _check_content(self) -> HealthCheckResult:
        """Check that page content loads correctly."""
        try:
            import time
            
            start = time.time()
            async with self.session.get(self.base_url) as response:
                elapsed = (time.time() - start) * 1000
                
                if response.status != 200:
                    return HealthCheckResult(
                        check_id=f"{self.component.component_id}_content",
                        name="Page Content",
                        layer=self.component.layer,
                        check_type=CheckType.CUSTOM,
                        status=HealthStatus.CRITICAL,
                        response_time_ms=elapsed,
                        message=f"Page returned status {response.status}"
                    )
                
                content = await response.text()
                content_length = len(content)
                
                # Check for common error indicators
                error_indicators = ["404", "not found", "error", "exception"]
                has_error = any(indicator in content.lower() for indicator in error_indicators)
                
                # Check for expected content (title tag for basic check)
                has_title = "<title>" in content.lower()
                
                status = HealthStatus.HEALTHY
                message = "Page content loaded successfully"
                
                if has_error:
                    status = HealthStatus.DEGRADED
                    message = "Page may contain errors"
                if content_length < 100 or not has_title:
                    status = HealthStatus.CRITICAL
                    message = "Page content incomplete or missing"
                
                return HealthCheckResult(
                    check_id=f"{self.component.component_id}_content",
                    name="Page Content",
                    layer=self.component.layer,
                    check_type=CheckType.CUSTOM,
                    status=status,
                    response_time_ms=elapsed,
                    actual_value=content_length,
                    message=message,
                    details={
                        "content_length": content_length,
                        "has_title": has_title,
                        "potential_errors": has_error
                    }
                )
                
        except Exception as e:
            return HealthCheckResult(
                check_id=f"{self.component.component_id}_content",
                name="Page Content",
                layer=self.component.layer,
                check_type=CheckType.CUSTOM,
                status=HealthStatus.CRITICAL,
                message=f"Failed to load content: {str(e)}"
            )
    
    async def _check_static_assets(self) -> HealthCheckResult:
        """Check that static assets (CSS, JS) are accessible."""
        try:
            # Fetch the main page to find asset links
            async with self.session.get(self.base_url) as response:
                html = await response.text()
            
            # Extract asset URLs (simple regex approach)
            import re
            css_urls = re.findall(r'href="([^"]+\.css[^"]*)"', html)
            js_urls = re.findall(r'src="([^"]+\.js[^"]*)"', html)
            
            # Test first CSS and JS files found
            test_urls = []
            if css_urls:
                test_urls.append(("CSS", css_urls[0]))
            if js_urls:
                test_urls.append(("JS", js_urls[0]))
            
            failed_assets = []
            successful_assets = []
            
            for asset_type, asset_path in test_urls:
                # Convert relative URLs to absolute
                if asset_path.startswith('http'):
                    asset_url = asset_path
                elif asset_path.startswith('/'):
                    asset_url = urljoin(self.base_url, asset_path)
                else:
                    asset_url = urljoin(self.base_url + '/', asset_path)
                
                try:
                    async with self.session.get(asset_url) as asset_response:
                        if asset_response.status != 200:
                            failed_assets.append(f"{asset_type}: {asset_path}")
                        else:
                            successful_assets.append(f"{asset_type}: {asset_path}")
                except:
                    failed_assets.append(f"{asset_type}: {asset_path}")
            
            if not test_urls:
                return HealthCheckResult(
                    check_id=f"{self.component.component_id}_assets",
                    name="Static Assets",
                    layer=self.component.layer,
                    check_type=CheckType.CUSTOM,
                    status=HealthStatus.HEALTHY,
                    message="No static assets detected"
                )
            
            status = HealthStatus.HEALTHY
            if failed_assets:
                status = HealthStatus.DEGRADED
            if len(failed_assets) == len(test_urls):
                status = HealthStatus.CRITICAL
            
            return HealthCheckResult(
                check_id=f"{self.component.component_id}_assets",
                name="Static Assets",
                layer=self.component.layer,
                check_type=CheckType.CUSTOM,
                status=status,
                message=f"{len(failed_assets)} of {len(test_urls)} assets failed",
                details={
                    "tested": len(test_urls),
                    "failed": len(failed_assets),
                    "failed_assets": failed_assets,
                    "successful_assets": successful_assets
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                check_id=f"{self.component.component_id}_assets",
                name="Static Assets",
                layer=self.component.layer,
                check_type=CheckType.CUSTOM,
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check assets: {str(e)}"
            )
    
    async def _check_response_time(self) -> HealthCheckResult:
        """Check page response time."""
        import time
        
        # Perform multiple requests for average
        times = []
        for _ in range(3):
            try:
                start = time.time()
                async with self.session.get(self.base_url) as response:
                    await response.text()
                    elapsed = (time.time() - start) * 1000
                    times.append(elapsed)
            except:
                pass
        
        if not times:
            return HealthCheckResult(
                check_id=f"{self.component.component_id}_response_time",
                name="Response Time",
                layer=self.component.layer,
                check_type=CheckType.LATENCY,
                status=HealthStatus.CRITICAL,
                message="All requests failed"
            )
        
        avg_time = sum(times) / len(times)
        
        status = HealthStatus.HEALTHY
        if avg_time > 1000:  # 1 second
            status = HealthStatus.DEGRADED
        if avg_time > 3000:  # 3 seconds
            status = HealthStatus.CRITICAL
        
        return HealthCheckResult(
            check_id=f"{self.component.component_id}_response_time",
            name="Response Time",
            layer=self.component.layer,
            check_type=CheckType.LATENCY,
            status=status,
            actual_value=avg_time,
            response_time_ms=avg_time,
            warning_threshold=1000,
            critical_threshold=3000,
            details={
                "average_ms": round(avg_time, 2),
                "samples": len(times),
                "min_ms": round(min(times), 2),
                "max_ms": round(max(times), 2)
            }
        )
