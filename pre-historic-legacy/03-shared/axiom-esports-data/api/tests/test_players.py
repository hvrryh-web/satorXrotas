"""Tests for players API endpoints."""
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.src.routes.players import router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


PLAYER_RECORD = {
    "player_id": str(uuid4()),
    "name": "TestPlayer",
    "team": "TeamX",
    "region": "NA",
    "role": "Entry",
    "kills": 15,
    "deaths": 12,
    "acs": 250.0,
    "adr": 130.0,
    "kast_pct": 72.0,
    "sim_rating": 0.5,
    "rar_score": 1.1,
    "investment_grade": "B",
    "confidence_tier": 75.0,
    "map_count": 80,
}


class TestGetPlayer:
    def test_returns_404_for_unknown_player(self, client):
        player_id = str(uuid4())
        with patch("api.src.routes.players.get_player_record", new=AsyncMock(return_value=None)):
            resp = client.get(f"/api/players/{player_id}")
        assert resp.status_code == 404

    def test_returns_player_schema(self, client):
        player_id = str(uuid4())
        record = {**PLAYER_RECORD, "player_id": player_id}
        with patch("api.src.routes.players.get_player_record", new=AsyncMock(return_value=record)):
            resp = client.get(f"/api/players/{player_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "TestPlayer"
        assert data["investment_grade"] == "B"


class TestListPlayers:
    def test_returns_empty_list_when_no_data(self, client):
        with patch("api.src.routes.players.get_player_list", new=AsyncMock(return_value=([], 0))):
            resp = client.get("/api/players/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["players"] == []
        assert data["total"] == 0

    def test_min_maps_default_is_50(self, client):
        with patch("api.src.routes.players.get_player_list", new=AsyncMock(return_value=([], 0))) as mock:
            client.get("/api/players/")
        mock.assert_called_once()
        _, kwargs = mock.call_args
        assert kwargs.get("min_maps", 50) == 50

    def test_grade_pattern_validation(self, client):
        with patch("api.src.routes.players.get_player_list", new=AsyncMock(return_value=([], 0))):
            resp = client.get("/api/players/?grade=INVALID")
        assert resp.status_code == 422

    def test_pagination_defaults(self, client):
        with patch("api.src.routes.players.get_player_list", new=AsyncMock(return_value=([], 0))):
            resp = client.get("/api/players/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["offset"] == 0
        assert data["limit"] == 50
