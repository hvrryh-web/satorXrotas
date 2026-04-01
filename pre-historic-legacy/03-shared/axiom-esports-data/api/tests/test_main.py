"""Tests for main FastAPI application."""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import create_application, check_database_health


class TestHealthEndpoint:
    """Tests for the /health endpoint."""
    
    def test_health_returns_status(self):
        """Health endpoint should return API status."""
        app = create_application()
        client = TestClient(app)
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "environment" in data
        assert "database" in data
    
    def test_health_with_disabled_database(self):
        """Health should report disabled when DATABASE_URL not set."""
        app = create_application()
        client = TestClient(app)
        
        with patch("api.main.DATABASE_URL", None):
            response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["database"]["status"] == "disabled"


class TestRootEndpoint:
    """Tests for the root / endpoint."""
    
    def test_root_returns_api_info(self):
        """Root should redirect to health or provide API info."""
        app = create_application()
        client = TestClient(app)
        
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "Axiom Esports" in data["message"]
        assert "/health" in data["health"]


class TestCORSHeaders:
    """Tests for CORS middleware."""
    
    def test_cors_headers_present(self):
        """CORS headers should be present on responses."""
        app = create_application()
        client = TestClient(app)
        
        response = client.options("/health", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        })
        
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers


class TestDatabaseHealth:
    """Tests for database health check function."""
    
    def test_health_check_disabled_without_url(self):
        """Health check should report disabled when no DATABASE_URL."""
        with patch("api.main.DATABASE_URL", None):
            result = check_database_health()
        
        assert result["status"] == "disabled"
        assert result["connected"] is False
    
    @pytest.mark.asyncio
    async def test_health_check_error_on_connection_failure(self):
        """Health check should report error on connection failure."""
        with patch("api.main.DATABASE_URL", "postgresql://invalid"):
            with patch("api.main.asyncpg") as mock_asyncpg:
                mock_asyncpg.connect = AsyncMock(side_effect=Exception("Connection failed"))
                result = await check_database_health()
        
        assert result["status"] == "error"
        assert result["connected"] is False


class TestRouteRegistration:
    """Tests that all routes are properly registered."""
    
    def test_players_routes_registered(self):
        """Players routes should be accessible."""
        app = create_application()
        
        routes = [r.path for r in app.routes]
        assert any("/api/players" in r for r in routes)
    
    def test_matches_routes_registered(self):
        """Matches routes should be accessible."""
        app = create_application()
        
        routes = [r.path for r in app.routes]
        assert any("/api/matches" in r for r in routes)
    
    def test_analytics_routes_registered(self):
        """Analytics routes should be accessible."""
        app = create_application()
        
        routes = [r.path for r in app.routes]
        assert any("/api/analytics" in r for r in routes)
