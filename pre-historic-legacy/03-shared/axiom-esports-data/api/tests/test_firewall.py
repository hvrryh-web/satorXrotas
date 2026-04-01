"""Tests for firewall middleware and FantasyDataFilter."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse

from api.src.middleware.firewall import FantasyDataFilter, FirewallMiddleware


class TestFantasyDataFilter:
    """Unit tests for the FantasyDataFilter class."""
    
    def test_sanitize_removes_game_only_fields_from_dict(self):
        """GAME_ONLY_FIELDS should be removed from response data."""
        data = {
            "player_id": "123",
            "name": "TestPlayer",
            "internalAgentState": "should_be_removed",
            "radarData": [1, 2, 3],
            "kills": 15,
        }
        sanitized = FantasyDataFilter.sanitize_for_web(data)
        
        assert "internalAgentState" not in sanitized
        assert "radarData" not in sanitized
        assert sanitized["player_id"] == "123"
        assert sanitized["name"] == "TestPlayer"
        assert sanitized["kills"] == 15
    
    def test_sanitize_handles_nested_dicts(self):
        """GAME_ONLY_FIELDS should be removed from nested structures."""
        data = {
            "match_id": "m001",
            "teams": {
                "team_a": {"score": 13, "seedValue": 12345},
                "team_b": {"score": 10},
            },
            "detailedReplayFrameData": [],
        }
        sanitized = FantasyDataFilter.sanitize_for_web(data)
        
        assert "detailedReplayFrameData" not in sanitized
        assert "seedValue" not in sanitized["teams"]["team_a"]
        assert sanitized["match_id"] == "m001"
        assert sanitized["teams"]["team_a"]["score"] == 13
    
    def test_sanitize_handles_lists(self):
        """GAME_ONLY_FIELDS should be removed from list items."""
        data = [
            {"player_id": "1", "visionConeData": "secret"},
            {"player_id": "2", "smokeTickData": "secret"},
            {"player_id": "3", "kills": 10},
        ]
        sanitized = FantasyDataFilter.sanitize_for_web(data)
        
        assert len(sanitized) == 3
        assert "visionConeData" not in sanitized[0]
        assert "smokeTickData" not in sanitized[1]
        assert sanitized[2]["kills"] == 10
    
    def test_sanitize_handles_primitives(self):
        """Primitive values should pass through unchanged."""
        assert FantasyDataFilter.sanitize_for_web("string") == "string"
        assert FantasyDataFilter.sanitize_for_web(123) == 123
        assert FantasyDataFilter.sanitize_for_web(None) is None
        assert FantasyDataFilter.sanitize_for_web(True) is True
    
    def test_sanitize_all_game_only_fields(self):
        """All GAME_ONLY_FIELDS should be removed."""
        data = {field: "secret" for field in FantasyDataFilter.GAME_ONLY_FIELDS}
        data["allowed_field"] = "visible"
        
        sanitized = FantasyDataFilter.sanitize_for_web(data)
        
        for field in FantasyDataFilter.GAME_ONLY_FIELDS:
            assert field not in sanitized
        assert sanitized["allowed_field"] == "visible"
    
    def test_validate_web_input_raises_on_forbidden_field(self):
        """Validation should raise error for GAME_ONLY_FIELDS."""
        data = {"player_id": "123", "recoilPattern": "secret"}
        
        with pytest.raises(ValueError, match="recoilPattern"):
            FantasyDataFilter.validate_web_input(data)
    
    def test_validate_web_input_passes_valid_data(self):
        """Validation should pass for valid data."""
        data = {"player_id": "123", "name": "Test", "kills": 15}
        
        assert FantasyDataFilter.validate_web_input(data) is True


class TestFirewallMiddleware:
    """Integration tests for the FirewallMiddleware."""
    
    def test_middleware_sanitizes_json_responses(self):
        """Middleware should sanitize JSON responses automatically."""
        app = FastAPI()
        app.add_middleware(FirewallMiddleware)
        
        @app.get("/test")
        def test_endpoint():
            return {
                "player_id": "123",
                "name": "Test",
                "simulationTick": 9999,
            }
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
        data = response.json()
        assert "simulationTick" not in data
        assert data["player_id"] == "123"
    
    def test_middleware_allows_non_json_responses(self):
        """Non-JSON responses should pass through unchanged."""
        app = FastAPI()
        app.add_middleware(FirewallMiddleware)
        
        @app.get("/text")
        def text_endpoint():
            return "Plain text response"
        
        client = TestClient(app)
        response = client.get("/text")
        
        assert response.status_code == 200
        assert response.text == '"Plain text response"'
    
    def test_middleware_skips_health_endpoint(self):
        """Health check endpoints should not be sanitized."""
        app = FastAPI()
        app.add_middleware(FirewallMiddleware)
        
        @app.get("/health")
        def health():
            return {"status": "ok"}
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
