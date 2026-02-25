"""Tests for matches API endpoints."""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.src.routes.matches import router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


MATCH_RECORD = {
    "match_id": "match_001",
    "map_name": "Ascent",
    "tournament": "VCT 2024",
    "date": "2024-06-01",
}


class TestGetMatch:
    def test_returns_404_for_unknown_match(self, client):
        with patch("api.src.routes.matches.get_match_record", new=AsyncMock(return_value=None)):
            resp = client.get("/api/matches/nonexistent_match")
        assert resp.status_code == 404

    def test_returns_match_data(self, client):
        with patch("api.src.routes.matches.get_match_record", new=AsyncMock(return_value=MATCH_RECORD)):
            resp = client.get("/api/matches/match_001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["match_id"] == "match_001"
        assert data["map_name"] == "Ascent"


class TestSatorEvents:
    def test_returns_empty_list_when_no_data(self, client):
        with patch("api.src.routes.matches.get_sator_events", new=AsyncMock(return_value=[])):
            resp = client.get("/api/matches/m001/rounds/1/sator-events")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_events_list(self, client):
        events = [{"eventType": "plant", "playerId": "p1", "mapX": 100, "mapY": 200}]
        with patch("api.src.routes.matches.get_sator_events", new=AsyncMock(return_value=events)):
            resp = client.get("/api/matches/m001/rounds/1/sator-events")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["eventType"] == "plant"


class TestArepoMarkers:
    def test_returns_empty_list(self, client):
        with patch("api.src.routes.matches.get_arepo_markers", new=AsyncMock(return_value=[])):
            resp = client.get("/api/matches/m001/rounds/1/arepo-markers")
        assert resp.status_code == 200
        assert resp.json() == []


class TestRotasTrails:
    def test_returns_empty_list(self, client):
        with patch("api.src.routes.matches.get_rotas_trails", new=AsyncMock(return_value=[])):
            resp = client.get("/api/matches/m001/rounds/1/rotas-trails")
        assert resp.status_code == 200
        assert resp.json() == []
