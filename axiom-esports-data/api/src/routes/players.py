"""
Players API — Player query endpoints.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from api.src.schemas.player_schema import PlayerSchema, PlayerListResponse
from api.src.db import get_player_record, get_player_list

router = APIRouter(prefix="/api/players", tags=["players"])


@router.get("/{player_id}", response_model=PlayerSchema)
async def get_player(player_id: UUID) -> PlayerSchema:
    """Fetch a single player's current stats and investment grade."""
    record = await get_player_record(str(player_id))
    if record is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return PlayerSchema(**record)


@router.get("/", response_model=PlayerListResponse)
async def list_players(
    region: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    min_maps: int = Query(default=50, ge=1),
    grade: Optional[str] = Query(None, pattern=r"^(A\+|A|B|C|D)$"),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
) -> PlayerListResponse:
    """
    List players with optional filters.
    min_maps defaults to 50 (minimum for statistical confidence).
    """
    players_data, total = await get_player_list(
        region=region, role=role, min_maps=min_maps,
        grade=grade, limit=limit, offset=offset,
    )
    players = [PlayerSchema(**p) for p in players_data]
    return PlayerListResponse(players=players, total=total, offset=offset, limit=limit)
