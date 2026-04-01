"""Tests for analytics API endpoints."""
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.src.routes.analytics import router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


PLAYER_RECORD = {
    "kills_z": 1.0, "deaths_z": -0.5, "adjusted_kill_value_z": 1.2,
    "adr_z": 0.8, "kast_pct_z": 1.0,
    "sim_rating": 1.1, "role": "Entry", "age": 22,
}


class TestSimRatingEndpoint:
    def test_returns_404_for_unknown_player(self, client):
        player_id = str(uuid4())
        with patch("api.src.routes.analytics.get_player_record", new=AsyncMock(return_value=None)):
            resp = client.get(f"/api/analytics/simrating/{player_id}")
        assert resp.status_code == 404

    def test_returns_simrating_breakdown(self, client):
        player_id = str(uuid4())
        with patch("api.src.routes.analytics.get_player_record", new=AsyncMock(return_value=PLAYER_RECORD)):
            resp = client.get(f"/api/analytics/simrating/{player_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "sim_rating" in data
        assert "components" in data
        assert "z_scores" in data
        assert -5.0 <= data["sim_rating"] <= 5.0

    def test_season_query_param(self, client):
        player_id = str(uuid4())
        with patch("api.src.routes.analytics.get_player_record", new=AsyncMock(return_value=PLAYER_RECORD)):
            resp = client.get(f"/api/analytics/simrating/{player_id}?season=2024")
        assert resp.status_code == 200
        assert resp.json()["season"] == "2024"


class TestRAREndpoint:
    def test_returns_404_for_unknown_player(self, client):
        player_id = str(uuid4())
        with patch("api.src.routes.analytics.get_player_record", new=AsyncMock(return_value=None)):
            resp = client.get(f"/api/analytics/rar/{player_id}")
        assert resp.status_code == 404

    def test_returns_rar_data(self, client):
        player_id = str(uuid4())
        with patch("api.src.routes.analytics.get_player_record", new=AsyncMock(return_value=PLAYER_RECORD)):
            resp = client.get(f"/api/analytics/rar/{player_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "rar_score" in data
        assert "investment_grade" in data
        assert data["investment_grade"] in ("A+", "A", "B", "C", "D")


class TestInvestmentEndpoint:
    def test_returns_404_for_unknown_player(self, client):
        player_id = str(uuid4())
        with patch("api.src.routes.analytics.get_player_record", new=AsyncMock(return_value=None)):
            resp = client.get(f"/api/analytics/investment/{player_id}")
        assert resp.status_code == 404

    def test_returns_investment_grade(self, client):
        player_id = str(uuid4())
        with patch("api.src.routes.analytics.get_player_record", new=AsyncMock(return_value=PLAYER_RECORD)):
            resp = client.get(f"/api/analytics/investment/{player_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["investment_grade"] in ("A+", "A", "B", "C", "D")
        assert "age_factor" in data
        assert 0.8 < data["age_factor"] <= 1.0
