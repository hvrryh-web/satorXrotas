"""
SimRating Calculator — Equal-weight 5-component performance rating.
Uses adjusted_kill_value (economy-normalized), never raw ACS.
"""
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

COMPONENT_WEIGHT = 0.20  # Equal weighting across 5 components


@dataclass
class SimRatingResult:
    sim_rating: float
    components: dict[str, float]
    z_scores: dict[str, float]
    notes: str = ""


class SimRatingCalculator:
    """
    SimRating = 0.20 * kills_z
               + 0.20 * deaths_z (inverse — lower is better)
               + 0.20 * acs_z  (uses adjusted_kill_value, NOT raw ACS)
               + 0.20 * adr_z
               + 0.20 * kast_z

    All z-scores computed within the same season/role cohort.
    """

    def calculate(
        self,
        kills_z: float,
        deaths_z: float,   # Negative z-score for deaths (inverse)
        adjusted_kill_value_z: float,  # NOT raw ACS
        adr_z: float,
        kast_pct_z: float,
    ) -> SimRatingResult:
        z_scores = {
            "kills":                kills_z,
            "deaths_inverse":       -deaths_z,
            "adjusted_kill_value":  adjusted_kill_value_z,
            "adr":                  adr_z,
            "kast_pct":             kast_pct_z,
        }

        components = {k: COMPONENT_WEIGHT * v for k, v in z_scores.items()}
        sim_rating = sum(components.values())

        return SimRatingResult(
            sim_rating=sim_rating,
            components=components,
            z_scores=z_scores,
        )

    def validate_range(self, sim_rating: float) -> bool:
        """
        Typical range is -3.0 to +3.0 (z-score based).
        Values outside ±5 indicate normalization error.
        """
        if abs(sim_rating) > 5.0:
            logger.warning(
                "SimRating %.3f outside expected range ±5.0 — check normalization",
                sim_rating,
            )
            return False
        return True
