"""
Analytics API — SimRating, RAR, and investment grade endpoints.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from analytics.src.simrating.calculator import SimRatingCalculator
from analytics.src.rar.decomposer import RARDecomposer
from analytics.src.investment.grader import InvestmentGrader
from api.src.db import get_player_record

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

_sim_calc = SimRatingCalculator()
_rar = RARDecomposer()
_grader = InvestmentGrader()


@router.get("/simrating/{player_id}")
async def get_simrating(
    player_id: UUID,
    season: Optional[str] = Query(None),
) -> dict:
    """Get SimRating breakdown for a player."""
    record = await get_player_record(str(player_id))
    if record is None:
        raise HTTPException(status_code=404, detail="Player not found")

    result = _sim_calc.calculate(
        kills_z=record.get("kills_z", 0.0),
        deaths_z=record.get("deaths_z", 0.0),
        adjusted_kill_value_z=record.get("adjusted_kill_value_z", 0.0),
        adr_z=record.get("adr_z", 0.0),
        kast_pct_z=record.get("kast_pct_z", 0.0),
    )
    return {
        "player_id": str(player_id),
        "season": season,
        "sim_rating": result.sim_rating,
        "components": result.components,
        "z_scores": result.z_scores,
    }


@router.get("/rar/{player_id}")
async def get_rar(player_id: UUID) -> dict:
    """Get Role-Adjusted value above Replacement for a player."""
    record = await get_player_record(str(player_id))
    if record is None:
        raise HTTPException(status_code=404, detail="Player not found")

    result = _rar.compute(
        raw_rating=record.get("sim_rating", 1.0),
        role=record.get("role", "Controller"),
    )
    return {
        "player_id": str(player_id),
        "role": result.role,
        "raw_rating": result.raw_rating,
        "replacement_level": result.replacement_level,
        "rar_score": result.rar_score,
        "investment_grade": result.investment_grade,
    }


@router.get("/investment/{player_id}")
async def get_investment_grade(player_id: UUID) -> dict:
    """Get investment grade with age curve and temporal decay factors."""
    record = await get_player_record(str(player_id))
    if record is None:
        raise HTTPException(status_code=404, detail="Player not found")

    grade_result = _grader.grade(
        raw_rating=record.get("sim_rating", 1.0),
        role=record.get("role", "Controller"),
        age=record.get("age", 23),
    )
    return {"player_id": str(player_id), **grade_result}
