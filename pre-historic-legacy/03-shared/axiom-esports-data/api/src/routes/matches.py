"""
Matches API — Match data and SATOR spatial event endpoints.
"""
from fastapi import APIRouter, HTTPException

from api.src.db import get_match_record, get_sator_events, get_arepo_markers, get_rotas_trails

router = APIRouter(prefix="/api/matches", tags=["matches"])


@router.get("/{match_id}")
async def get_match(match_id: str) -> dict:
    """Get match metadata and map."""
    record = await get_match_record(match_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Match not found")
    return record


@router.get("/{match_id}/rounds/{round_number}/sator-events")
async def get_sator_events_route(match_id: str, round_number: int) -> list:
    """Get SATOR Layer 1 events for a round (planters, MVPs, hotstreaks)."""
    return await get_sator_events(match_id, round_number)


@router.get("/{match_id}/rounds/{round_number}/arepo-markers")
async def get_arepo_markers_route(match_id: str, round_number: int) -> list:
    """Get AREPO Layer 4 death stain markers for a round."""
    return await get_arepo_markers(match_id, round_number)


@router.get("/{match_id}/rounds/{round_number}/rotas-trails")
async def get_rotas_trails_route(match_id: str, round_number: int) -> list:
    """Get ROTAS Layer 5 rotation trail data for a round."""
    return await get_rotas_trails(match_id, round_number)
