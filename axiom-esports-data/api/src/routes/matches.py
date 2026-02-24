"""
Matches API — Match data and SATOR spatial event endpoints.
"""
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/matches", tags=["matches"])


@router.get("/{match_id}")
async def get_match(match_id: str) -> dict:
    """Get match metadata and map."""
    raise HTTPException(status_code=501, detail="Not yet implemented")


@router.get("/{match_id}/rounds/{round_number}/sator-events")
async def get_sator_events(match_id: str, round_number: int) -> list:
    """Get SATOR Layer 1 events for a round (planters, MVPs, hotstreaks)."""
    raise HTTPException(status_code=501, detail="Not yet implemented")


@router.get("/{match_id}/rounds/{round_number}/arepo-markers")
async def get_arepo_markers(match_id: str, round_number: int) -> list:
    """Get AREPO Layer 4 death stain markers for a round."""
    raise HTTPException(status_code=501, detail="Not yet implemented")


@router.get("/{match_id}/rounds/{round_number}/rotas-trails")
async def get_rotas_trails(match_id: str, round_number: int) -> list:
    """Get ROTAS Layer 5 rotation trail data for a round."""
    raise HTTPException(status_code=501, detail="Not yet implemented")
