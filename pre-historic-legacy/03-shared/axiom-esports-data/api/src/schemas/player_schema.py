"""
Player Schema — Static field definitions for the player API.
Mirrors the *Def pattern from RadiantX: static definitions separate from runtime computation.
"""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PlayerSchema(BaseModel):
    """37-field KCRITR player record (read model for API)."""
    # Identity
    player_id: UUID
    name: str
    team: Optional[str] = None
    region: Optional[str] = None
    role: Optional[str] = None

    # Performance (range validated)
    kills: Optional[int] = Field(None, ge=0, le=100)
    deaths: Optional[int] = Field(None, ge=0, le=100)
    acs: Optional[float] = Field(None, ge=0.0, le=800.0)
    adr: Optional[float] = Field(None, ge=0.0, le=500.0)
    kast_pct: Optional[float] = Field(None, ge=0.0, le=100.0)

    # Analytics
    sim_rating: Optional[float] = Field(None, ge=-5.0, le=5.0)
    rar_score: Optional[float] = Field(None, ge=0.0, le=3.0)
    investment_grade: Optional[str] = Field(None, pattern=r"^(A\+|A|B|C|D)$")

    # Data quality
    confidence_tier: Optional[float] = Field(None, ge=0.0, le=100.0)
    map_count: Optional[int] = Field(None, ge=0)


class PlayerListResponse(BaseModel):
    players: list[PlayerSchema]
    total: int
    offset: int
    limit: int
