"""
Firewall Middleware — GAME_ONLY_FIELDS Response Sanitization

Implements the FantasyDataFilter concept from shared/packages/data-partition-lib
as a FastAPI middleware that sanitizes all outgoing responses.

Blocks sensitive game-internal fields from leaking to the web platform.
"""
import logging
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse

logger = logging.getLogger(__name__)


class FantasyDataFilter:
    """
    Python implementation of the FantasyDataFilter from data-partition-lib.
    
    Enforces the SATOR data partition policy: game-internal fields must never
    reach the web platform or be stored in the public database.
    """
    
    # Fields that exist exclusively inside the game simulation
    # and must never be transmitted to the web platform
    GAME_ONLY_FIELDS: set[str] = {
        "internalAgentState",
        "radarData",
        "detailedReplayFrameData",
        "simulationTick",
        "seedValue",
        "visionConeData",
        "smokeTickData",
        "recoilPattern",
    }
    
    @classmethod
    def sanitize_for_web(cls, data: Any) -> Any:
        """
        Sanitize data object before sending to web platform.
        
        Recursively traverses dicts and lists, removing all GAME_ONLY_FIELDS.
        
        Args:
            data: Raw data object (dict, list, or primitive)
            
        Returns:
            Sanitized copy safe for web consumption
        """
        if isinstance(data, dict):
            sanitized: dict[str, Any] = {}
            for key, value in data.items():
                # Skip game-only fields
                if key in cls.GAME_ONLY_FIELDS:
                    continue
                # Recursively sanitize nested structures
                sanitized[key] = cls.sanitize_for_web(value)
            return sanitized
        
        elif isinstance(data, list):
            return [cls.sanitize_for_web(item) for item in data]
        
        elif isinstance(data, tuple):
            return tuple(cls.sanitize_for_web(item) for item in data)
        
        # Primitive value — return as-is
        return data
    
    @classmethod
    def validate_web_input(cls, data: Any) -> bool:
        """
        Validate that incoming web data does not contain game-internal fields.
        
        Call this at API ingestion points before persisting data.
        
        Args:
            data: Data received from or destined for the web layer
            
        Returns:
            True if all fields are valid
            
        Raises:
            ValueError: If a forbidden field is detected
        """
        if isinstance(data, dict):
            for key in data.keys():
                if key in cls.GAME_ONLY_FIELDS:
                    raise ValueError(
                        f"Web attempted to write game-internal field: {key}"
                    )
                # Recursively validate nested structures
                cls.validate_web_input(data[key])
        
        elif isinstance(data, (list, tuple)):
            for item in data:
                cls.validate_web_input(item)
        
        return True


class FirewallMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware that applies FantasyDataFilter to all outgoing responses.
    
    Automatically sanitizes JSON responses to ensure no GAME_ONLY_FIELDS leak.
    Logs any attempts to send forbidden fields for security auditing.
    """
    
    def __init__(self, app: Any):
        super().__init__(app)
        self.filter = FantasyDataFilter()
    
    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """
        Process request and sanitize response.
        
        Only sanitizes JSON responses. Passes through other response types
        (HTML, binary, streaming) unchanged.
        """
        response = await call_next(request)
        
        # Only sanitize JSON responses
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response
        
        # Don't sanitize health check or docs endpoints
        path = request.url.path
        if path in ("/health", "/docs", "/redoc", "/openapi.json"):
            return response
        
        try:
            # Get response body
            if hasattr(response, "body"):
                import json
                body = json.loads(response.body)
                
                # Check for forbidden fields before sanitizing
                has_forbidden = self._contains_game_only_fields(body)
                if has_forbidden:
                    logger.warning(
                        f"Firewall: Blocking GAME_ONLY_FIELDS in response to {path}"
                    )
                
                # Sanitize the response
                sanitized_body = self.filter.sanitize_for_web(body)
                
                # Return sanitized response
                return JSONResponse(
                    content=sanitized_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                )
        except Exception as e:
            # If sanitization fails, log but don't break the response
            logger.error(f"Firewall: Error sanitizing response: {e}")
        
        return response
    
    def _contains_game_only_fields(self, data: Any, path: str = "") -> bool:
        """
        Check if data contains any GAME_ONLY_FIELDS (for logging purposes).
        
        Args:
            data: Data structure to check
            path: Current path in nested structure (for logging)
            
        Returns:
            True if any game-only fields were found
        """
        found = False
        
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                if key in self.filter.GAME_ONLY_FIELDS:
                    logger.warning(f"Firewall: Found forbidden field at {current_path}")
                    found = True
                elif isinstance(value, (dict, list)):
                    if self._contains_game_only_fields(value, current_path):
                        found = True
        
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]"
                if isinstance(item, (dict, list)):
                    if self._contains_game_only_fields(item, current_path):
                        found = True
        
        return found
