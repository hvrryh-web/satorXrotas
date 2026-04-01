"""
Age Curves — Career peak modeling for esports players.
Entry fraggers peak earlier; IGLs peak later.
"""
from dataclasses import dataclass

ROLE_PEAK_RANGES = {
    "Entry":      (20, 24),
    "IGL":        (26, 32),
    "Controller": (22, 28),
    "Initiator":  (21, 27),
    "Sentinel":   (23, 29),
}


@dataclass
class AgeCurveResult:
    role: str
    age: int
    peak_range: tuple[int, int]
    career_stage: str   # rising, peak, declining
    peak_proximity: float  # 0.0 to 1.0


def compute_age_curve(role: str, age: int) -> AgeCurveResult:
    peak_range = ROLE_PEAK_RANGES.get(role, (21, 27))
    peak_start, peak_end = peak_range
    peak_mid = (peak_start + peak_end) / 2

    if age < peak_start:
        stage = "rising"
        proximity = age / peak_start if peak_start > 0 else 0.0
    elif age <= peak_end:
        stage = "peak"
        proximity = 1.0 - abs(age - peak_mid) / ((peak_end - peak_start) / 2)
    else:
        stage = "declining"
        proximity = max(0.0, 1.0 - (age - peak_end) / 5.0)

    return AgeCurveResult(
        role=role,
        age=age,
        peak_range=peak_range,
        career_stage=stage,
        peak_proximity=proximity,
    )
