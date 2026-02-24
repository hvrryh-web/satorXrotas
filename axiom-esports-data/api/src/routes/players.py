"""
Players API — Player query endpoints.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from api.src.schemas.player_schema import PlayerSchema, PlayerListResponse

router = APIRouter(prefix="/api/players", tags=["players"])


@router.get("/{player_id}", response_model=PlayerSchema)
async def get_player(player_id: UUID) -> PlayerSchema:
    """Fetch a single player's current stats and investment grade."""
    raise HTTPException(status_code=501, detail="Not yet implemented")


@router.get("/", response_model=PlayerListResponse)
async def list_players(
    region: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    min_maps: int = Query(default=50, ge=1),
    grade: Optional[str] = Query(None, regex="^(A\+|A|B|C|D)$"),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
) -> PlayerListResponse:
    """
    List players with optional filters.
    min_maps defaults to 50 (minimum for statistical confidence).
    """
    raise HTTPException(status_code=501, detail="Not yet implemented")
