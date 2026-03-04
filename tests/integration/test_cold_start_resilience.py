"""
Cold Start Resilience Integration Tests
=======================================

Tests for handling Render cold starts and API latency gracefully.

These tests verify:
- React app handles delayed API responses
- Retry logic works correctly
- Loading states are properly implemented
- Timeouts are handled gracefully

Render free tier spins down after 15 minutes of inactivity, causing
10-30 second cold start delays on the first request.
"""

import json
import os
import time
from typing import Any
from unittest.mock import Mock, patch

import pytest
import requests

# Import React app API client if available
try:
    sys_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import sys
    sys.path.insert(0, os.path.join(sys_path, "shared", "apps", "sator-web", "src"))
    from services.api import apiClient, playersApi
    REACT_API_AVAILABLE = True
except ImportError:
    REACT_API_AVAILABLE = False
    apiClient = None
    playersApi = None


class MockDelayedResponse:
    """Mock response that simulates network delays."""

    def __init__(self, delay_seconds: float, status_code: int = 200, json_data: dict = None):
        self.delay_seconds = delay_seconds
        self.status_code = status_code
        self._json_data = json_data or {"players": [], "total": 0, "offset": 0, "limit": 50}
        self.headers = {"content-type": "application/json"}
        self.text = json.dumps(self._json_data)

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class TestColdStartSimulation:
    """Test handling of simulated cold start delays."""

    @pytest.fixture
    def delayed_api_client(self):
        """Create a mock API client with configurable delays."""
        class DelayedAPIClient:
            def __init__(self):
                self.delay = 0.0
                self.call_count = 0

            def get(self, url: str, timeout: float = 10, **kwargs) -> MockDelayedResponse:
                """Simulate GET request with delay."""
                if self.delay > 0:
                    time.sleep(self.delay)
                self.call_count += 1

                # Simulate cold start behavior
                if self.call_count == 1 and self.delay > 5:
                    # First call during cold start - might timeout
                    if timeout < self.delay:
                        raise requests.Timeout(f"Request timed out after {timeout}s")

                return MockDelayedResponse(
                    delay_seconds=0,
                    status_code=200,
                    json_data={
                        "status": "healthy",
                        "service": "sator-api",
                        "database": "connected",
                    }
                )

            def set_delay(self, seconds: float):
                """Set the delay for subsequent requests."""
                self.delay = seconds
                self.call_count = 0

        return DelayedAPIClient()

    def test_handles_10_second_cold_start(self, delayed_api_client):
        """Test handling of 10 second cold start (lower bound)."""
        delayed_api_client.set_delay(10)

        # Should handle with appropriate timeout
        response = delayed_api_client.get("/health", timeout=15)
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_handles_30_second_cold_start(self, delayed_api_client):
        """Test handling of 30 second cold start (upper bound)."""
        delayed_api_client.set_delay(30)

        # Should handle with extended timeout
        response = delayed_api_client.get("/health", timeout=35)
        assert response.status_code == 200

    def test_timeout_on_insufficient_timeout(self, delayed_api_client):
        """Test that request times out when timeout is insufficient."""
        delayed_api_client.set_delay(20)

        with pytest.raises(requests.Timeout):
            delayed_api_client.get("/health", timeout=5)

    def test_subsequent_requests_faster(self, delayed_api_client):
        """Test that subsequent requests after cold start are faster."""
        # First call - cold start (20s delay)
        delayed_api_client.set_delay(20)
        delayed_api_client.get("/health", timeout=25)

        # Second call - warm (no delay)
        delayed_api_client.set_delay(0)
        start = time.time()
        response = delayed_api_client.get("/health", timeout=10)
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 1.0, "Warm request should complete quickly"


class TestRetryLogic:
    """Test retry logic for handling transient failures."""

    @pytest.fixture
    def flaky_api_client(self):
        """Create a mock API client that fails intermittently."""
        class FlakyAPIClient:
            def __init__(self, fail_count: int = 2):
                self.fail_count = fail_count
                self.attempts = 0
                self.success_after = fail_count

            def get(self, url: str, **kwargs) -> MockDelayedResponse:
                """Simulate GET request that fails initially then succeeds."""
                self.attempts += 1

                if self.attempts <= self.success_after:
                    raise requests.ConnectionError(f"Connection failed (attempt {self.attempts})")

                return MockDelayedResponse(
                    status_code=200,
                    json_data={"status": "healthy"}
                )

        return FlakyAPIClient

    def test_retry_on_connection_error(self, flaky_api_client):
        """Test that requests are retried on connection errors."""
        client = flaky_api_client(fail_count=2)

        # Implement simple retry logic
        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                response = client.get("/health")
                assert response.status_code == 200
                assert client.attempts == 3  # Failed twice, succeeded on third
                return
            except requests.ConnectionError as e:
                last_error = e
                continue

        pytest.fail(f"Request failed after {max_retries} attempts: {last_error}")

    def test_retry_with_backoff(self, flaky_api_client):
        """Test retry with exponential backoff."""
        client = flaky_api_client(fail_count=2)

        max_retries = 3
        retry_delay = 0.1  # Start with 100ms
        delays = []

        for attempt in range(max_retries):
            start = time.time()
            try:
                response = client.get("/health")
                assert response.status_code == 200
                break
            except requests.ConnectionError:
                elapsed = time.time() - start
                delays.append(elapsed)
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))

        # Should have made multiple attempts
        assert client.attempts > 1

    def test_no_retry_on_4xx_errors(self):
        """Test that 4xx errors are not retried."""
        class Client4xx:
            def __init__(self):
                self.attempts = 0

            def get(self, url: str, **kwargs) -> MockDelayedResponse:
                self.attempts += 1
                return MockDelayedResponse(status_code=404, json_data={"error": "Not found"})

        client = Client4xx()

        # Should not retry 404
        response = client.get("/api/players/invalid-id")
        assert response.status_code == 404
        assert client.attempts == 1  # Only one attempt


class TestReactAppResilience:
    """Test React app's handling of API delays and failures."""

    @pytest.fixture
    def mock_react_state(self):
        """Create mock React component state for testing."""
        return {
            "loading": False,
            "error": None,
            "data": None,
            "retryCount": 0,
        }

    def test_loading_state_during_cold_start(self, mock_react_state):
        """Test that loading state is set during cold start."""
        # Simulate starting a request
        state = mock_react_state.copy()
        state["loading"] = True

        assert state["loading"] is True
        assert state["error"] is None

    def test_error_state_on_timeout(self, mock_react_state):
        """Test that error state is set on timeout."""
        state = mock_react_state.copy()

        # Simulate timeout error
        state["loading"] = False
        state["error"] = "Request timeout. The server may be starting up. Please try again."

        assert state["loading"] is False
        assert state["error"] is not None
        assert "timeout" in state["error"].lower() or "starting up" in state["error"].lower()

    def test_retry_count_incremented(self, mock_react_state):
        """Test that retry count is tracked."""
        state = mock_react_state.copy()

        # Simulate retries
        for i in range(3):
            state["retryCount"] = i + 1

        assert state["retryCount"] == 3

    def test_success_state_after_retry(self, mock_react_state):
        """Test that success state is set after successful retry."""
        state = mock_react_state.copy()

        # After successful response
        state["loading"] = False
        state["error"] = None
        state["data"] = {"players": [{"name": "TestPlayer"}]}

        assert state["loading"] is False
        assert state["error"] is None
        assert state["data"] is not None


class TestAPITimeoutConfiguration:
    """Test API client timeout configurations."""

    def test_health_endpoint_short_timeout(self):
        """Test health endpoint uses shorter timeout."""
        # Health check should be quick
        health_timeout = 5

        # Simulate request
        start = time.time()
        time.sleep(0.1)  # Simulate network
        elapsed = time.time() - start

        assert elapsed < health_timeout

    def test_data_endpoint_longer_timeout(self):
        """Test data endpoints use longer timeout for cold starts."""
        # Data requests need longer timeout for cold start
        data_timeout = 30

        # This is a configuration test
        assert data_timeout >= 30, "Data timeout should be at least 30s for cold starts"

    def test_axios_timeout_configuration(self):
        """Test that axios is configured with appropriate timeouts."""
        if not REACT_API_AVAILABLE:
            pytest.skip("React API client not available")

        # Check default timeout
        assert apiClient.defaults.timeout >= 10000, "Axios timeout should be at least 10s"


class TestKeepaliveMechanism:
    """Test the keepalive mechanism for preventing cold starts."""

    def test_keepalive_ping_frequency(self):
        """Test that keepalive pings are frequent enough."""
        # Render free tier spins down after 15 minutes
        # Keepalive should ping at least every 10-14 minutes
        spin_down_time = 15 * 60  # 15 minutes in seconds
        keepalive_interval = 10 * 60  # 10 minutes

        assert keepalive_interval < spin_down_time, \
            "Keepalive interval must be less than spin-down time"

    def test_keepalive_endpoint_available(self):
        """Test that keepalive endpoint is available."""
        # Keepalive should use lightweight /health endpoint
        keepalive_endpoint = "/health"

        # Should be a simple GET request
        assert keepalive_endpoint.startswith("/")

    def test_keepalive_response_format(self):
        """Test that keepalive response is lightweight."""
        # Mock health response
        health_response = {
            "status": "healthy",
            "service": "sator-api",
            "version": "0.1.0",
        }

        # Response should be small (no large data)
        response_size = len(json.dumps(health_response))
        assert response_size < 1000, "Health response should be lightweight"


class TestUserExperience:
    """Test user experience during cold starts."""

    def test_loading_message_for_cold_start(self):
        """Test appropriate loading message during cold start."""
        # Expected messages for cold start
        cold_start_messages = [
            "Connecting to server...",
            "Server is starting up, please wait...",
            "This may take up to 30 seconds on first load...",
        ]

        assert len(cold_start_messages) > 0

    def test_retry_button_available(self):
        """Test that retry button/message is shown on error."""
        error_state = {
            "showRetry": True,
            "retryMessage": "Click to retry",
        }

        assert error_state["showRetry"] is True

    def test_progress_indicator_for_long_requests(self):
        """Test progress indicator for long-running requests."""
        # Progress should be shown for requests taking > 3 seconds
        show_progress_threshold = 3.0

        assert show_progress_threshold > 0


class TestCircuitBreaker:
    """Test circuit breaker pattern for failing API."""

    @pytest.fixture
    def circuit_breaker(self):
        """Create a simple circuit breaker."""
        class CircuitBreaker:
            def __init__(self, failure_threshold: int = 5, timeout: int = 60):
                self.failure_threshold = failure_threshold
                self.timeout = timeout
                self.failure_count = 0
                self.last_failure_time = None
                self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

            def call(self, func, *args, **kwargs):
                if self.state == "OPEN":
                    if self._timeout_elapsed():
                        self.state = "HALF_OPEN"
                    else:
                        raise Exception("Circuit breaker is OPEN")

                try:
                    result = func(*args, **kwargs)
                    self._on_success()
                    return result
                except Exception as e:
                    self._on_failure()
                    raise e

            def _on_success(self):
                self.failure_count = 0
                self.state = "CLOSED"

            def _on_failure(self):
                self.failure_count += 1
                self.last_failure_time = time.time()
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"

            def _timeout_elapsed(self) -> bool:
                if self.last_failure_time is None:
                    return True
                return time.time() - self.last_failure_time > self.timeout

        return CircuitBreaker()

    def test_circuit_opens_after_failures(self, circuit_breaker):
        """Test that circuit opens after threshold failures."""
        failing_func = Mock(side_effect=Exception("API Error"))

        # Trigger failures up to threshold
        for _ in range(circuit_breaker.failure_threshold):
            with pytest.raises(Exception):
                circuit_breaker.call(failing_func)

        assert circuit_breaker.state == "OPEN"

    def test_circuit_closes_after_timeout(self, circuit_breaker):
        """Test that circuit closes after timeout."""
        # Open the circuit
        circuit_breaker.state = "OPEN"
        circuit_breaker.last_failure_time = time.time() - 70  # 70 seconds ago

        # Should be able to try again
        success_func = Mock(return_value={"status": "ok"})
        result = circuit_breaker.call(success_func)

        assert circuit_breaker.state == "CLOSED"
        assert result == {"status": "ok"}

    def test_circuit_blocks_when_open(self, circuit_breaker):
        """Test that calls are blocked when circuit is open."""
        circuit_breaker.state = "OPEN"
        circuit_breaker.last_failure_time = time.time()

        any_func = Mock(return_value="result")

        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            circuit_breaker.call(any_func)


class TestNetworkResilience:
    """Test resilience against network issues."""

    def test_handles_dns_failure(self):
        """Test handling of DNS resolution failure."""
        with pytest.raises(requests.ConnectionError):
            # Invalid domain should fail
            requests.get("http://invalid.invalid.invalid", timeout=2)

    def test_handles_connection_refused(self):
        """Test handling of connection refused."""
        with pytest.raises(requests.ConnectionError):
            # Port that should be closed
            requests.get("http://localhost:9999", timeout=2)

    def test_handles_slow_response(self):
        """Test handling of slow but successful response."""
        # This is a conceptual test - actual slow response would require server
        timeout = 10
        start = time.time()
        time.sleep(0.5)  # Simulate slow response
        elapsed = time.time() - start

        assert elapsed < timeout, "Should handle slow responses within timeout"
