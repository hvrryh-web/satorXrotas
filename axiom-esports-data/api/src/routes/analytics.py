"""
Analytics API — SimRating, RAR, and investment grade endpoints.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/simrating/{player_id}")
async def get_simrating(
    player_id: UUID,
    season: Optional[str] = Query(None),
) -> dict:
    """Get SimRating breakdown for a player."""
    raise HTTPException(status_code=501, detail="Not yet implemented")


@router.get("/rar/{player_id}")
async def get_rar(player_id: UUID) -> dict:
    """Get Role-Adjusted value above Replacement for a player."""
    raise HTTPException(status_code=501, detail="Not yet implemented")


@router.get("/investment/{player_id}")
async def get_investment_grade(player_id: UUID) -> dict:
    """Get investment grade with age curve and temporal decay factors."""
    raise HTTPException(status_code=501, detail="Not yet implemented")
