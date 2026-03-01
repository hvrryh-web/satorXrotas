"""
Investment Grader — A+/A/B/C/D classification for player investment decisions.
"""
from datetime import datetime
from typing import Optional

from analytics.src.rar.decomposer import RARDecomposer
from analytics.src.temporal.age_curves import compute_age_curve
from analytics.src.temporal.decay_weights import compute_decay_weight

_ROUND_PRECISION = 4  # Decimal places for proximity and decay_factor fields


class InvestmentGrader:
    """
    Combines RAR score, age curve position, and temporal decay
    to produce a final investment grade for scouting/signing decisions.
    """

    def __init__(self) -> None:
        self.rar = RARDecomposer()

    def grade(
        self,
        raw_rating: float,
        role: str,
        age: int,
        peak_age_range: Optional[tuple[int, int]] = None,
        record_date: Optional[datetime] = None,
    ) -> dict:
        """
        Compute investment grade.

        Args:
            raw_rating: SimRating or equivalent performance score.
            role: Player role (Entry, IGL, Controller, Initiator, Sentinel).
            age: Player age in years.
            peak_age_range: Override for peak age window; defaults to role-specific range.
            record_date: Date of the performance record for temporal decay weighting.
                         Defaults to None (no decay applied).
        """
        age_result = compute_age_curve(role, age)
        role_peak = age_result.peak_range
        if peak_age_range is None:
            peak_age_range = role_peak

        in_peak = peak_age_range[0] <= age <= peak_age_range[1]
        age_factor = 1.0 if in_peak else 0.85

        # Apply temporal decay if a record date is provided
        decay_factor = 1.0
        if record_date is not None:
            decay_factor = compute_decay_weight(record_date)

        adjusted_rating = raw_rating * decay_factor
        rar_result = self.rar.compute(adjusted_rating, role)

        adjusted_rar = rar_result.rar_score * age_factor
        final_grade = self.rar._grade(adjusted_rar)

        return {
            "rar_score": rar_result.rar_score,
            "age_factor": age_factor,
            "adjusted_rar": adjusted_rar,
            "investment_grade": final_grade,
            "in_peak_age": in_peak,
            "career_stage": age_result.career_stage,
            "peak_proximity": round(age_result.peak_proximity, _ROUND_PRECISION),
            "decay_factor": round(decay_factor, _ROUND_PRECISION),
        }
