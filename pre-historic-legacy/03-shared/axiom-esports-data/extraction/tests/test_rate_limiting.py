"""Tests for ResilientVLRClient rate limiting and circuit breaker."""
import asyncio
import pytest

from extraction.src.scrapers.vlr_resilient_client import CircuitBreaker, ResilientVLRClient


class TestCircuitBreaker:
    def test_starts_closed(self):
        cb = CircuitBreaker()
        assert cb.state == "CLOSED"
        assert cb.can_attempt()

    def test_opens_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "CLOSED"
        cb.record_failure()
        assert cb.state == "OPEN"

    def test_closed_after_success(self):
        cb = CircuitBreaker(failure_threshold=2)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "OPEN"
        cb.record_success()
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0

    def test_blocks_when_open(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=9999)
        cb.record_failure()
        assert not cb.can_attempt()

    def test_half_open_after_recovery_timeout(self):
        import time
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0)
        cb.record_failure()
        time.sleep(0.01)
        assert cb.can_attempt()
        assert cb.state == "HALF_OPEN"


class TestResilientVLRClientInit:
    def test_default_rate_limit(self):
        client = ResilientVLRClient(rate_limit_seconds=2.0)
        assert client.rate_limit == 2.0

    def test_user_agent_rotation(self):
        client = ResilientVLRClient()
        ua1 = client._next_user_agent()
        ua2 = client._next_user_agent()
        # Both should be non-empty strings
        assert isinstance(ua1, str) and len(ua1) > 0
        assert isinstance(ua2, str) and len(ua2) > 0

    def test_checksum_consistency(self):
        client = ResilientVLRClient()
        content = "test content"
        assert client._compute_checksum(content) == client._compute_checksum(content)

    def test_checksum_length(self):
        client = ResilientVLRClient()
        checksum = client._compute_checksum("some html content")
        assert len(checksum) == 64  # SHA-256 hex digest
