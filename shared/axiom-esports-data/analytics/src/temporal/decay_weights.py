"""
Decay Weights — Mono no aware temporal weighting.
Recent records carry more weight; older records decay exponentially.
"""
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

HALF_LIFE_DAYS = 365   # Records older than 1 year weighted at 0.5x
FLOOR_WEIGHT = 0.1     # Minimum weight for records older than ~3 years


def compute_decay_weight(record_date: datetime, reference_date: datetime = None) -> float:
    """
    Compute temporal decay weight using exponential decay.
    weight = max(FLOOR_WEIGHT, 2 ** (-days_elapsed / HALF_LIFE_DAYS))
    """
    if reference_date is None:
        reference_date = datetime.now(timezone.utc)

    if record_date.tzinfo is None:
        record_date = record_date.replace(tzinfo=timezone.utc)

    days_elapsed = (reference_date - record_date).days
    if days_elapsed < 0:
        return 1.0  # Future records get full weight (should not occur in training)

    weight = 2.0 ** (-days_elapsed / HALF_LIFE_DAYS)
    return max(FLOOR_WEIGHT, weight)
