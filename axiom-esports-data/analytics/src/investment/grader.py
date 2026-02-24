"""
Investment Grader — A+/A/B/C/D classification for player investment decisions.
"""
from analytics.src.rar.decomposer import RARDecomposer, RARResult


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
        peak_age_range: tuple[int, int] = (21, 26),
    ) -> dict:
        rar_result = self.rar.compute(raw_rating, role)

        # Age factor: full credit in peak range, 0.85x outside
        in_peak = peak_age_range[0] <= age <= peak_age_range[1]
        age_factor = 1.0 if in_peak else 0.85

        adjusted_rar = rar_result.rar_score * age_factor
        final_grade = self.rar._grade(adjusted_rar)

        return {
            "rar_score": rar_result.rar_score,
            "age_factor": age_factor,
            "adjusted_rar": adjusted_rar,
            "investment_grade": final_grade,
            "in_peak_age": in_peak,
        }
