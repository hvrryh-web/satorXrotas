"""
RAR Decomposer — Role-Adjusted value above Replacement calculation.
"""
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

REPLACEMENT_LEVELS = {
    "Entry":      1.15,
    "IGL":        0.95,
    "Controller": 1.00,
    "Initiator":  1.05,
    "Sentinel":   0.98,
}


@dataclass
class RARResult:
    role: str
    raw_rating: float
    replacement_level: float
    rar_score: float
    investment_grade: str


class RARDecomposer:
    """
    Computes role-adjusted value above replacement level.
    rar_score = role_adjusted_value / replacement_level
    """

    def get_replacement_mean(self) -> float:
        """Return mean replacement level across all roles."""
        values = list(REPLACEMENT_LEVELS.values())
        return sum(values) / len(values)

    def compute(self, raw_rating: float, role: str) -> RARResult:
        replacement = REPLACEMENT_LEVELS.get(role, 1.00)
        rar_score = raw_rating / replacement if replacement > 0 else 0.0

        return RARResult(
            role=role,
            raw_rating=raw_rating,
            replacement_level=replacement,
            rar_score=rar_score,
            investment_grade=self._grade(rar_score),
        )

    def _grade(self, rar_score: float) -> str:
        if rar_score >= 1.30:
            return "A+"
        if rar_score >= 1.15:
            return "A"
        if rar_score >= 1.00:
            return "B"
        if rar_score >= 0.85:
            return "C"
        return "D"
