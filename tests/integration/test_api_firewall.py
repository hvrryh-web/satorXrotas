"""
API Firewall Integration Tests
==============================

Tests that the API properly blocks GAME_ONLY_FIELDS from reaching the web platform.

These tests verify that the FantasyDataFilter correctly sanitizes responses and
that all 8 GAME_ONLY_FIELDS are properly stripped.
"""

import json
from typing import Any

import pytest

# Import the firewall module
try:
    from api.src.middleware.firewall import FantasyDataFilter, FirewallMiddleware
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from fastapi.responses import JSONResponse

    FIREWALL_AVAILABLE = True
except ImportError:
    FIREWALL_AVAILABLE = False
    FantasyDataFilter = None
    FirewallMiddleware = None


# All 8 GAME_ONLY_FIELDS as defined in the firewall
GAME_ONLY_FIELDS = [
    "internalAgentState",
    "radarData",
    "detailedReplayFrameData",
    "simulationTick",
    "seedValue",
    "visionConeData",
    "smokeTickData",
    "recoilPattern",
]


@pytest.mark.skipif(not FIREWALL_AVAILABLE, reason="Firewall module not available")
class TestAPIFirewallBlocking:
    """Test that the API properly blocks GAME_ONLY_FIELDS in requests and responses."""

    def test_all_game_only_fields_defined(self):
        """Verify all 8 GAME_ONLY_FIELDS are defined in the firewall."""
        expected_fields = set(GAME_ONLY_FIELDS)
        actual_fields = FantasyDataFilter.GAME_ONLY_FIELDS

        assert actual_fields == expected_fields, (
            f"GAME_ONLY_FIELDS mismatch.\n"
            f"Expected: {expected_fields}\n"
            f"Actual: {actual_fields}\n"
            f"Missing: {expected_fields - actual_fields}\n"
            f"Extra: {actual_fields - expected_fields}"
        )

    @pytest.mark.parametrize("field_name", GAME_ONLY_FIELDS)
    def test_individual_field_stripped_from_response(self, field_name: str):
        """Test that each GAME_ONLY_FIELD is individually stripped from response."""
        data = {
            "player_id": "p001",
            "name": "TestPlayer",
            "acs": 250.0,
            field_name: "secret_value_that_should_be_removed",
        }

        sanitized = FantasyDataFilter.sanitize_for_web(data)

        assert field_name not in sanitized, (
            f"GAME_ONLY_FIELD '{field_name}' was not stripped from response"
        )
        assert sanitized["player_id"] == "p001"
        assert sanitized["name"] == "TestPlayer"
        assert sanitized["acs"] == 250.0

    def test_all_eight_fields_stripped_simultaneously(self):
        """Test that all 8 GAME_ONLY_FIELDS are stripped when present together."""
        data = {"player_id": "p001", "name": "TestPlayer", "public_field": "visible"}

        # Add all game-only fields
        for field in GAME_ONLY_FIELDS:
            data[field] = f"secret_{field}_value"

        sanitized = FantasyDataFilter.sanitize_for_web(data)

        # Verify all game-only fields are removed
        for field in GAME_ONLY_FIELDS:
            assert field not in sanitized, (
                f"GAME_ONLY_FIELD '{field}' was not stripped"
            )

        # Verify public fields remain
        assert sanitized["player_id"] == "p001"
        assert sanitized["name"] == "TestPlayer"
        assert sanitized["public_field"] == "visible"
        assert len(sanitized) == 3  # Only the 3 public fields

    def test_nested_dict_game_only_fields_removed(self):
        """Test GAME_ONLY_FIELDS are removed from nested dictionaries."""
        data = {
            "match_id": "m001",
            "teams": {
                "team_a": {
                    "score": 13,
                    "seedValue": 12345,  # Should be removed
                    "internalAgentState": {"ai": "data"},  # Should be removed
                },
                "team_b": {
                    "score": 10,
                    "radarData": [],  # Should be removed
                },
            },
            "simulationTick": 999999,  # Should be removed at top level
        }

        sanitized = FantasyDataFilter.sanitize_for_web(data)

        # Top level
        assert "simulationTick" not in sanitized
        assert sanitized["match_id"] == "m001"

        # Nested level
        assert "seedValue" not in sanitized["teams"]["team_a"]
        assert "internalAgentState" not in sanitized["teams"]["team_a"]
        assert "radarData" not in sanitized["teams"]["team_b"]

        # Public fields preserved
        assert sanitized["teams"]["team_a"]["score"] == 13
        assert sanitized["teams"]["team_b"]["score"] == 10

    def test_list_items_game_only_fields_removed(self):
        """Test GAME_ONLY_FIELDS are removed from items in lists."""
        data = {
            "players": [
                {
                    "player_id": "p001",
                    "visionConeData": "secret",  # Should be removed
                    "name": "Player1",
                },
                {
                    "player_id": "p002",
                    "smokeTickData": [],  # Should be removed
                    "name": "Player2",
                },
                {
                    "player_id": "p003",
                    "recoilPattern": [[0, 0]],  # Should be removed
                    "name": "Player3",
                },
            ]
        }

        sanitized = FantasyDataFilter.sanitize_for_web(data)

        assert "visionConeData" not in sanitized["players"][0]
        assert "smokeTickData" not in sanitized["players"][1]
        assert "recoilPattern" not in sanitized["players"][2]

        assert sanitized["players"][0]["name"] == "Player1"
        assert sanitized["players"][1]["name"] == "Player2"
        assert sanitized["players"][2]["name"] == "Player3"

    def test_deeply_nested_structure(self):
        """Test GAME_ONLY_FIELDS are removed from deeply nested structures."""
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "detailedReplayFrameData": [1, 2, 3],  # Deep nested
                            "public": "value",
                        }
                    }
                },
                "radarData": "shallow",  # Shallow nested
            }
        }

        sanitized = FantasyDataFilter.sanitize_for_web(data)

        assert "radarData" not in sanitized["level1"]
        assert "detailedReplayFrameData" not in sanitized["level1"]["level2"]["level3"]["level4"]
        assert sanitized["level1"]["level2"]["level3"]["level4"]["public"] == "value"


@pytest.mark.skipif(not FIREWALL_AVAILABLE, reason="Firewall module not available")
class TestAPIFirewallRequestValidation:
    """Test that the API validates incoming requests for GAME_ONLY_FIELDS."""

    @pytest.mark.parametrize("field_name", GAME_ONLY_FIELDS)
    def test_validation_raises_error_for_game_only_field(self, field_name: str):
        """Test that validation raises an error for each GAME_ONLY_FIELD."""
        data = {
            "player_id": "p001",
            "name": "TestPlayer",
            field_name: "attempted_injection",
        }

        with pytest.raises(ValueError, match=field_name):
            FantasyDataFilter.validate_web_input(data)

    def test_validation_passes_for_valid_data(self):
        """Test that validation passes for data without GAME_ONLY_FIELDS."""
        data = {
            "player_id": "p001",
            "name": "TestPlayer",
            "team": "TestTeam",
            "acs": 250.0,
            "kills": 200,
            "deaths": 150,
        }

        # Should not raise
        result = FantasyDataFilter.validate_web_input(data)
        assert result is True

    def test_validation_checks_nested_data(self):
        """Test that validation checks nested structures."""
        data = {
            "match_id": "m001",
            "teams": {
                "team_a": {
                    "score": 13,
                    "seedValue": 12345,  # Forbidden
                }
            }
        }

        with pytest.raises(ValueError, match="seedValue"):
            FantasyDataFilter.validate_web_input(data)

    def test_validation_checks_list_items(self):
        """Test that validation checks items in lists."""
        data = {
            "players": [
                {"player_id": "p001", "name": "Player1"},
                {"player_id": "p002", "radarData": "secret"},  # Forbidden
            ]
        }

        with pytest.raises(ValueError, match="radarData"):
            FantasyDataFilter.validate_web_input(data)


@pytest.mark.skipif(not FIREWALL_AVAILABLE, reason="Firewall module not available")
class TestFirewallMiddlewareIntegration:
    """Test the FirewallMiddleware integrates correctly with FastAPI."""

    def test_middleware_sanitizes_json_responses(self):
        """Test middleware automatically sanitizes JSON responses."""
        app = FastAPI()
        app.add_middleware(FirewallMiddleware)

        @app.get("/test/player")
        def get_player():
            return {
                "player_id": "p001",
                "name": "TestPlayer",
                "simulationTick": 9999,
                "seedValue": 12345,
                "radarData": [{"x": 100, "y": 200}],
            }

        client = TestClient(app)
        response = client.get("/test/player")

        assert response.status_code == 200
        data = response.json()

        # Verify GAME_ONLY_FIELDS stripped
        assert "simulationTick" not in data
        assert "seedValue" not in data
        assert "radarData" not in data

        # Verify public fields remain
        assert data["player_id"] == "p001"
        assert data["name"] == "TestPlayer"

    def test_middleware_preserves_non_json_responses(self):
        """Test middleware doesn't interfere with non-JSON responses."""
        app = FastAPI()
        app.add_middleware(FirewallMiddleware)

        @app.get("/test/text")
        def get_text():
            return "Plain text response"

        client = TestClient(app)
        response = client.get("/test/text")

        assert response.status_code == 200
        # FastAPI converts string to JSON, so we check it worked
        assert "Plain text response" in response.text

    def test_middleware_skips_health_endpoints(self):
        """Test middleware skips health check endpoints."""
        app = FastAPI()
        app.add_middleware(FirewallMiddleware)

        @app.get("/health")
        def health():
            return {"status": "healthy", "internalAgentState": "should_remain"}

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Health endpoint should not be sanitized
        assert data["status"] == "healthy"
        assert "internalAgentState" in data  # This would normally be stripped

    def test_middleware_skips_docs_endpoints(self):
        """Test middleware skips documentation endpoints."""
        app = FastAPI()
        app.add_middleware(FirewallMiddleware)

        # FastAPI auto-generates /docs and /redoc
        client = TestClient(app)

        # These should work without issues
        response = client.get("/docs")
        assert response.status_code == 200

        response = client.get("/redoc")
        assert response.status_code == 200

    def test_middleware_handles_complex_response(self):
        """Test middleware handles complex nested response structures."""
        app = FastAPI()
        app.add_middleware(FirewallMiddleware)

        @app.get("/test/match")
        def get_match():
            return {
                "match_id": "m001",
                "teams": {
                    "team_a": {
                        "players": [
                            {"name": "Player1", "visionConeData": "secret"},
                            {"name": "Player2", "smokeTickData": []},
                        ],
                        "seedValue": 123,
                    },
                    "team_b": {
                        "players": [
                            {"name": "Player3", "recoilPattern": []},
                        ],
                    },
                },
                "rounds": [
                    {"round": 1, "detailedReplayFrameData": []},
                    {"round": 2, "simulationTick": 999},
                ],
                "internalAgentState": {"ai": "data"},
            }

        client = TestClient(app)
        response = client.get("/test/match")

        assert response.status_code == 200
        data = response.json()

        # Verify all GAME_ONLY_FIELDS stripped at all levels
        assert "internalAgentState" not in data
        assert "seedValue" not in data["teams"]["team_a"]
        assert "visionConeData" not in data["teams"]["team_a"]["players"][0]
        assert "smokeTickData" not in data["teams"]["team_a"]["players"][1]
        assert "recoilPattern" not in data["teams"]["team_b"]["players"][0]
        assert "detailedReplayFrameData" not in data["rounds"][0]
        assert "simulationTick" not in data["rounds"][1]

        # Verify public fields remain
        assert data["match_id"] == "m001"
        assert data["teams"]["team_a"]["players"][0]["name"] == "Player1"


@pytest.mark.skipif(not FIREWALL_AVAILABLE, reason="Firewall module not available")
class TestFirewallEdgeCases:
    """Test edge cases for the firewall."""

    def test_empty_data_passes_through(self):
        """Test empty data structures pass through unchanged."""
        assert FantasyDataFilter.sanitize_for_web({}) == {}
        assert FantasyDataFilter.sanitize_for_web([]) == []
        assert FantasyDataFilter.sanitize_for_web(None) is None

    def test_primitives_pass_through(self):
        """Test primitive values pass through unchanged."""
        assert FantasyDataFilter.sanitize_for_web("string") == "string"
        assert FantasyDataFilter.sanitize_for_web(123) == 123
        assert FantasyDataFilter.sanitize_for_web(45.67) == 45.67
        assert FantasyDataFilter.sanitize_for_web(True) is True
        assert FantasyDataFilter.sanitize_for_web(False) is False

    def test_field_names_similar_to_game_only_fields(self):
        """Test that similar field names are not accidentally removed."""
        data = {
            "internalAgentState_backup": "should_remain",  # Different name
            "radarData_v2": "should_remain",  # Different name
            "my_seedValue": "should_remain",  # Different name
            "simulationTick": "should_be_removed",  # Exact match
        }

        sanitized = FantasyDataFilter.sanitize_for_web(data)

        assert "internalAgentState_backup" in sanitized
        assert "radarData_v2" in sanitized
        assert "my_seedValue" in sanitized
        assert "simulationTick" not in sanitized

    def test_unicode_in_game_only_field_values(self):
        """Test unicode content in GAME_ONLY_FIELD values."""
        data = {
            "player_id": "p001",
            "internalAgentState": "unicode: 你好世界 🎮",  # Should be removed with key
        }

        sanitized = FantasyDataFilter.sanitize_for_web(data)

        assert "internalAgentState" not in sanitized
        assert sanitized["player_id"] == "p001"

    def test_large_nested_structure_performance(self):
        """Test firewall handles large nested structures efficiently."""
        # Create a large nested structure
        data = {
            "players": [
                {
                    "player_id": f"p{i:03d}",
                    "name": f"Player{i}",
                    "radarData": [{"x": j, "y": j} for j in range(100)],
                }
                for i in range(100)
            ]
        }

        import time

        start = time.time()
        sanitized = FantasyDataFilter.sanitize_for_web(data)
        duration = time.time() - start

        # Should complete in reasonable time (< 1 second for this size)
        assert duration < 1.0, f"Sanitization took too long: {duration:.2f}s"

        # Verify all game-only fields removed
        for player in sanitized["players"]:
            assert "radarData" not in player
            assert "player_id" in player
