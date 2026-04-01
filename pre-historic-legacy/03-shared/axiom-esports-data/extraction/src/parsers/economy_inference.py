"""
Economy Inference — ACS differential model for economy-normalized kill values.
Addresses ACS bias toward Duelists (kill multipliers inflate raw ACS).
"""
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# Role-based ACS adjustment factors
ROLE_ACS_ADJUSTMENT = {
    "Entry":      1.00,  # No adjustment — baseline
    "IGL":        1.12,  # IGLs sacrifice ACS for leadership; normalize up
    "Controller": 1.08,
    "Initiator":  1.05,
    "Sentinel":   1.10,
}


@dataclass
class EconomyInferenceResult:
    raw_acs: float
    adjusted_kill_value: float
    economy_rating: float
    role: Optional[str]
    adjustment_factor: float


class EconomyInferenceEngine:
    """
    Computes economy-normalized kill values from ACS differentials.
    Always use adjusted_kill_value in SimRating — NEVER raw ACS.
    """

    def infer(
        self,
        raw_acs: float,
        role: Optional[str],
        team_avg_acs: Optional[float] = None,
        map_avg_acs: Optional[float] = None,
    ) -> EconomyInferenceResult:
        """
        Compute economy-normalized kill value.

        Formula:
          base = raw_acs / map_avg_acs (if available) else raw_acs / 200 (global baseline)
          adjusted = base * role_adjustment_factor
          economy_rating = adjusted * 100 (normalized 0-200 scale)
        """
        map_baseline = map_avg_acs if map_avg_acs and map_avg_acs > 0 else 200.0
        adjustment = ROLE_ACS_ADJUSTMENT.get(role, 1.0) if role else 1.0

        base_ratio = raw_acs / map_baseline
        adjusted_kill_value = base_ratio * adjustment
        economy_rating = adjusted_kill_value * 100.0

        return EconomyInferenceResult(
            raw_acs=raw_acs,
            adjusted_kill_value=adjusted_kill_value,
            economy_rating=economy_rating,
            role=role,
            adjustment_factor=adjustment,
        )
