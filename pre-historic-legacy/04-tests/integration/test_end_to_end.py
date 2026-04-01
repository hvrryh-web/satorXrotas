"""
End-to-End Integration Tests
============================

Full flow tests that verify the entire stack works together:
- API returns correct format
- React app builds successfully
- Types are consistent between schema and API
- Data flows correctly from source to API response

These tests validate the complete integration of all system components.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import requests

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
REACT_APP_PATH = PROJECT_ROOT / "shared" / "apps" / "sator-web"
WEBSITE_DATA_PATH = PROJECT_ROOT / "website" / "data"
SCHEMA_PATH = PROJECT_ROOT / "website" / "config" / "schema.json"
API_PATH = PROJECT_ROOT / "shared" / "axiom-esports-data" / "api"

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class TestReactAppBuild:
    """Test that the React application builds successfully."""

    @pytest.fixture(scope="class")
    def react_app_exists(self):
        """Check if React app exists."""
        if not REACT_APP_PATH.exists():
            pytest.skip(f"React app not found at {REACT_APP_PATH}")
        return True

    def test_react_app_package_json_exists(self, react_app_exists):
        """Test that package.json exists in React app."""
        package_json = REACT_APP_PATH / "package.json"
        assert package_json.exists(), "package.json not found"

        with open(package_json) as f:
            package = json.load(f)

        assert "name" in package
        assert "scripts" in package
        assert "build" in package["scripts"]

    def test_react_app_typescript_config_exists(self, react_app_exists):
        """Test that TypeScript configuration exists."""
        tsconfig = REACT_APP_PATH / "tsconfig.json"
        assert tsconfig.exists(), "tsconfig.json not found"

    def test_react_app_source_files_exist(self, react_app_exists):
        """Test that React app source files exist."""
        src_path = REACT_APP_PATH / "src"
        assert src_path.exists(), "src directory not found"

        # Check for key files
        assert (src_path / "App.tsx").exists() or (src_path / "App.jsx").exists(), "App component not found"
        assert (src_path / "main.tsx").exists() or (src_path / "main.jsx").exists(), "Main entry not found"

    def test_react_app_api_service_exists(self, react_app_exists):
        """Test that API service file exists."""
        api_service = REACT_APP_PATH / "src" / "services" / "api.ts"
        if api_service.exists():
            with open(api_service) as f:
                content = f.read()
            # Should contain API client configuration
            assert "axios" in content or "fetch" in content

    def test_react_app_types_exist(self, react_app_exists):
        """Test that TypeScript types are defined."""
        types_file = REACT_APP_PATH / "src" / "types" / "index.ts"
        assert types_file.exists(), "Types file not found"

        with open(types_file) as f:
            content = f.read()

        # Should contain type definitions
        assert "export" in content
        assert "interface" in content or "type" in content

    @pytest.mark.slow
    def test_react_app_typecheck(self, react_app_exists):
        """Test that React app passes TypeScript type checking."""
        package_json = REACT_APP_PATH / "package.json"

        with open(package_json) as f:
            package = json.load(f)

        if "typecheck" not in package.get("scripts", {}):
            pytest.skip("No typecheck script defined")

        # Run type checking
        result = subprocess.run(
            ["npm", "run", "typecheck"],
            cwd=REACT_APP_PATH,
            capture_output=True,
            text=True,
            timeout=120,
        )

        assert result.returncode == 0, f"TypeScript errors:\n{result.stdout}\n{result.stderr}"

    @pytest.mark.slow
    def test_react_app_builds_successfully(self, react_app_exists):
        """Test that React app builds without errors."""
        # Check if node_modules exists
        node_modules = REACT_APP_PATH / "node_modules"
        if not node_modules.exists():
            pytest.skip("node_modules not installed - run npm install first")

        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=REACT_APP_PATH,
            capture_output=True,
            text=True,
            timeout=300,
        )

        assert result.returncode == 0, f"Build failed:\n{result.stdout}\n{result.stderr}"

        # Check that dist folder was created
        dist_path = REACT_APP_PATH / "dist"
        assert dist_path.exists(), "dist folder not created"
        assert any(dist_path.iterdir()), "dist folder is empty"


class TestSchemaConsistency:
    """Test that types are consistent between schema and API."""

    @pytest.fixture(scope="class")
    def schema(self) -> dict[str, Any]:
        """Load the schema.json file."""
        if not SCHEMA_PATH.exists():
            pytest.skip(f"Schema file not found at {SCHEMA_PATH}")

        with open(SCHEMA_PATH) as f:
            return json.load(f)

    @pytest.fixture(scope="class")
    def player_schema(self) -> dict[str, Any]:
        """Load the player schema from API."""
        schema_file = API_PATH / "src" / "schemas" / "player_schema.py"
        if not schema_file.exists():
            pytest.skip(f"Player schema not found at {schema_file}")

        with open(schema_file) as f:
            return {"content": f.read()}

    @pytest.fixture(scope="class")
    def react_types(self) -> str:
        """Load React app types."""
        types_file = REACT_APP_PATH / "src" / "types" / "index.ts"
        if not types_file.exists():
            pytest.skip(f"Types file not found at {types_file}")

        with open(types_file) as f:
            return f.read()

    def test_schema_json_valid(self, schema: dict[str, Any]):
        """Test that schema.json is valid JSON with required structure."""
        assert "fields" in schema, "Schema missing 'fields' section"
        assert "version" in schema, "Schema missing version"

        # Check field categories
        fields = schema["fields"]
        assert "identity" in fields, "Schema missing identity fields"
        assert "raw_performance" in fields, "Schema missing raw_performance fields"

    def test_schema_identity_fields(self, schema: dict[str, Any]):
        """Test that identity fields are defined in schema."""
        identity = schema["fields"]["identity"]

        required_fields = ["player_id", "name", "team", "region", "role"]
        for field in required_fields:
            assert field in identity, f"Missing identity field: {field}"
            assert "type" in identity[field], f"Field {field} missing type"

    def test_schema_performance_fields(self, schema: dict[str, Any]):
        """Test that performance fields are defined in schema."""
        performance = schema["fields"]["raw_performance"]

        required_fields = ["acs", "kills", "deaths", "adr", "kast_pct"]
        for field in required_fields:
            assert field in performance, f"Missing performance field: {field}"

    def test_api_schema_matches_json_schema(self, schema: dict[str, Any], player_schema: dict[str, Any]):
        """Test that API Pydantic schema aligns with JSON schema."""
        content = player_schema["content"]

        # Check that key fields from schema are in Pydantic model
        identity_fields = schema["fields"]["identity"]
        for field_name in ["player_id", "name", "team"]:
            if field_name in identity_fields:
                assert field_name in content, f"Field {field_name} not in Pydantic schema"

        # Check performance fields
        perf_fields = schema["fields"]["raw_performance"]
        for field_name in ["acs", "kills", "deaths"]:
            if field_name in perf_fields:
                assert field_name in content, f"Field {field_name} not in Pydantic schema"

    def test_react_types_match_schema(self, schema: dict[str, Any], react_types: str):
        """Test that React types align with schema."""
        # Check identity fields
        identity_fields = schema["fields"]["identity"]
        for field_name in ["player_id", "name", "team", "region", "role"]:
            if field_name in identity_fields:
                assert field_name in react_types, f"Field {field_name} not in React types"

        # Check performance fields
        perf_fields = schema["fields"]["raw_performance"]
        for field_name in ["acs", "kills", "deaths", "adr", "kast_pct"]:
            if field_name in perf_fields:
                assert field_name in react_types, f"Field {field_name} not in React types"

    def test_field_types_consistent(self, schema: dict[str, Any], react_types: str):
        """Test that field types are consistent across schema and React types."""
        # Check that numeric fields are typed as numbers in React
        perf_fields = schema["fields"]["raw_performance"]

        for field_name, field_def in perf_fields.items():
            if field_name in react_types:
                field_type = field_def.get("type", "")
                if field_type == "number":
                    # In React types, should be 'number'
                    assert f"{field_name}?: number" in react_types or f"{field_name}: number" in react_types, \
                        f"Field {field_name} should be number type in React"


class TestAPIResponseFormat:
    """Test that API returns correct format matching schema."""

    @pytest.fixture
    def api_available(self):
        """Check if API is available."""
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    @pytest.mark.skipif(
        os.getenv("SKIP_API_TESTS", "false").lower() == "true",
        reason="API tests disabled via SKIP_API_TESTS env var",
    )
    def test_health_endpoint_format(self, api_available):
        """Test health endpoint returns expected format."""
        if not api_available:
            pytest.skip("API not available")

        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        assert response.status_code == 200

        data = response.json()

        # Check expected fields
        assert "status" in data, "Health check missing 'status'"
        assert data["status"] in ["healthy", "degraded"], f"Unexpected status: {data['status']}"

        # Should have service info
        assert "service" in data or "version" in data, "Missing service info"

    @pytest.mark.skipif(
        os.getenv("SKIP_API_TESTS", "false").lower() == "true",
        reason="API tests disabled via SKIP_API_TESTS env var",
    )
    def test_players_list_format(self, api_available):
        """Test players list endpoint returns correct format."""
        if not api_available:
            pytest.skip("API not available")

        response = requests.get(f"{API_BASE_URL}/api/players/", timeout=10)

        # May return 200 or 404 depending on data availability
        if response.status_code == 404:
            pytest.skip("No players data available")

        assert response.status_code == 200, f"Unexpected status: {response.status_code}"

        data = response.json()

        # Check list response structure
        assert "players" in data, "Response missing 'players' field"
        assert isinstance(data["players"], list), "'players' should be a list"
        assert "total" in data, "Response missing 'total' field"
        assert "offset" in data, "Response missing 'offset' field"
        assert "limit" in data, "Response missing 'limit' field"

    @pytest.mark.skipif(
        os.getenv("SKIP_API_TESTS", "false").lower() == "true",
        reason="API tests disabled via SKIP_API_TESTS env var",
    )
    def test_player_detail_format(self, api_available):
        """Test player detail endpoint returns correct format."""
        if not api_available:
            pytest.skip("API not available")

        # Use a test player ID
        test_player_id = "00000000-0000-0000-0000-000000000001"
        response = requests.get(f"{API_BASE_URL}/api/players/{test_player_id}", timeout=10)

        # May return 404 if player doesn't exist
        if response.status_code == 404:
            pytest.skip("Test player not found")

        assert response.status_code == 200

        data = response.json()

        # Check player structure
        assert "player_id" in data, "Player missing 'player_id'"
        assert "name" in data, "Player missing 'name'"


class TestDataFlow:
    """Test that data flows correctly from source to API."""

    @pytest.fixture(scope="class")
    def mock_players(self) -> list[dict[str, Any]]:
        """Load mock player data."""
        players_file = WEBSITE_DATA_PATH / "players.json"
        if players_file.exists():
            with open(players_file) as f:
                return json.load(f)
        return []

    def test_mock_players_data_exists(self, mock_players: list[dict[str, Any]]):
        """Test that mock player data exists and is valid."""
        assert len(mock_players) > 0, "No mock player data found"

        # Check first player has required fields
        first_player = mock_players[0]
        required_fields = ["player_id", "name", "team", "region", "role"]
        for field in required_fields:
            assert field in first_player, f"Mock player missing field: {field}"

    def test_mock_players_performance_fields(self, mock_players: list[dict[str, Any]]):
        """Test that mock players have performance fields."""
        if not mock_players:
            pytest.skip("No mock player data")

        player = mock_players[0]
        perf_fields = ["acs", "kills", "deaths", "adr", "kast_pct"]

        # At least some performance fields should exist
        has_perf_fields = any(field in player for field in perf_fields)
        assert has_perf_fields, "Mock player missing performance fields"

    def test_mock_players_no_game_only_fields(self, mock_players: list[dict[str, Any]]):
        """Test that mock players don't contain game-only fields."""
        if not mock_players:
            pytest.skip("No mock player data")

        game_only_fields = {
            "internalAgentState",
            "radarData",
            "detailedReplayFrameData",
            "simulationTick",
            "seedValue",
            "visionConeData",
            "smokeTickData",
            "recoilPattern",
        }

        for player in mock_players:
            for field in game_only_fields:
                assert field not in player, f"Mock player contains game-only field: {field}"


class TestSystemIntegration:
    """Test overall system integration."""

    def test_project_structure_complete(self):
        """Test that all expected project directories exist."""
        required_paths = [
            PROJECT_ROOT / "website",
            PROJECT_ROOT / "shared" / "axiom-esports-data",
            PROJECT_ROOT / "shared" / "apps" / "sator-web",
        ]

        for path in required_paths:
            assert path.exists(), f"Required path does not exist: {path}"

    def test_api_files_exist(self):
        """Test that required API files exist."""
        required_files = [
            API_PATH / "main.py",
            API_PATH / "requirements.txt",
            API_PATH / "src" / "middleware" / "firewall.py",
            API_PATH / "src" / "schemas" / "player_schema.py",
        ]

        for file_path in required_files:
            assert file_path.exists(), f"Required API file missing: {file_path}"

    def test_firewall_importable(self):
        """Test that firewall module can be imported."""
        try:
            sys.path.insert(0, str(API_PATH))
            from api.src.middleware.firewall import FantasyDataFilter, FirewallMiddleware

            assert FantasyDataFilter is not None
            assert FirewallMiddleware is not None
            assert len(FantasyDataFilter.GAME_ONLY_FIELDS) == 8
        except ImportError as e:
            pytest.skip(f"Cannot import firewall: {e}")

    def test_schema_json_validates(self):
        """Test that schema.json is valid and complete."""
        if not SCHEMA_PATH.exists():
            pytest.skip("Schema file not found")

        with open(SCHEMA_PATH) as f:
            schema = json.load(f)

        # Validate structure
        assert "version" in schema
        assert "fields" in schema
        assert "primary_key" in schema

        # Check all field categories
        fields = schema["fields"]
        categories = [
            "identity",
            "raw_performance",
            "extended_performance",
            "derived_metrics",
            "rar_metrics",
            "temporal",
            "match_context",
            "provenance",
        ]

        for category in categories:
            assert category in fields, f"Missing field category: {category}"

    def test_environment_variables_documented(self):
        """Test that required environment variables are documented."""
        env_example = API_PATH / ".env.example"
        if not env_example.exists():
            pytest.skip(".env.example not found")

        with open(env_example) as f:
            content = f.read()

        # Should contain key variables
        assert "DATABASE_URL" in content
