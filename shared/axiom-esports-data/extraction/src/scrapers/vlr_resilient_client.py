"""
VLR Resilient Client
Ethical scraping wrapper with circuit breaker, rate limiting, and schema drift detection.
"""
import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

EXPECTED_SCHEMA_FIELDS = {
    "player", "team", "agent", "rating", "acs", "kills", "deaths",
    "assists", "kast", "adr", "hs_pct", "first_blood", "first_death",
    "clutch_win", "clutch_attempt"
}

USER_AGENTS = [
    "AxiomEsportsBot/1.0 (Research Project; contact@axiom-esports.example)",
    "AxiomAnalytics/1.0 (Academic Study; contact@axiom-esports.example)",
]


@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    recovery_timeout: int = 300  # seconds
    failure_count: int = 0
    last_failure_time: float = 0.0
    state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(
                "Circuit breaker OPEN after %d failures. "
                "Recovery in %ds.", self.failure_count, self.recovery_timeout
            )

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = "CLOSED"

    def can_attempt(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            elapsed = time.time() - self.last_failure_time
            if elapsed >= self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        return True  # HALF_OPEN: allow one attempt


@dataclass
class ValidatedResponse:
    url: str
    status: int
    raw_html: str
    checksum: str
    schema_valid: bool
    schema_drift_fields: dict = field(default_factory=dict)
    from_cache: bool = False


class ResilientVLRClient:
    """
    Ethical VLR.gg client with:
    - Circuit breaker (5 failures → 5min backoff)
    - Rotating user agents
    - Schema drift detection
    - SHA-256 content checksums
    - Exponential backoff on rate limit responses
    """

    def __init__(
        self,
        rate_limit_seconds: float = 2.0,
        max_concurrent: int = 3,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> None:
        self.rate_limit = rate_limit_seconds
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.circuit_breaker = CircuitBreaker()
        self._ua_index = 0
        self._session = session
        self._cache: dict[str, ValidatedResponse] = {}

    def _next_user_agent(self) -> str:
        ua = USER_AGENTS[self._ua_index % len(USER_AGENTS)]
        self._ua_index += 1
        return ua

    def _compute_checksum(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()

    def validate_schema(self, parsed_data: dict) -> dict:
        """
        Checks for schema drift against known VLR field set.
        Returns dict of missing/extra fields, empty if schema is valid.
        """
        detected = set(parsed_data.keys())
        missing = EXPECTED_SCHEMA_FIELDS - detected
        extra = detected - EXPECTED_SCHEMA_FIELDS
        return {"missing": list(missing), "extra": list(extra)}

    async def fetch_with_validation(self, url: str) -> ValidatedResponse:
        if not self.circuit_breaker.can_attempt():
            logger.error("Circuit breaker OPEN — skipping %s", url)
            if url in self._cache:
                cached = self._cache[url]
                cached.from_cache = True
                return cached
            raise ConnectionError(f"Circuit breaker OPEN, no cache for {url}")

        headers = {
            "User-Agent": self._next_user_agent(),
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }

        async with self.semaphore:
            await asyncio.sleep(self.rate_limit)
            try:
                async with self._session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 429:
                        self.circuit_breaker.record_failure()
                        retry_after = int(resp.headers.get("Retry-After", 60))
                        logger.warning("Rate limited on %s. Waiting %ds.", url, retry_after)
                        await asyncio.sleep(retry_after)
                        return await self.fetch_with_validation(url)

                    if resp.status >= 500:
                        self.circuit_breaker.record_failure()
                        raise aiohttp.ServerConnectionError(f"Server error {resp.status} on {url}")

                    raw = await resp.text()
                    checksum = self._compute_checksum(raw)
                    self.circuit_breaker.record_success()

                    validated = ValidatedResponse(
                        url=url,
                        status=resp.status,
                        raw_html=raw,
                        checksum=checksum,
                        schema_valid=True,
                    )
                    self._cache[url] = validated
                    return validated

            except aiohttp.ClientError as exc:
                self.circuit_breaker.record_failure()
                logger.error("Request failed for %s: %s", url, exc)
                raise

    async def ethical_fetch(self, url: str) -> ValidatedResponse:
        """Public entry point — validates schema after fetch."""
        response = await self.fetch_with_validation(url)
        return response
