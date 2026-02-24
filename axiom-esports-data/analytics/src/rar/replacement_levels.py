"""
Replacement Levels — Role baseline constants and temporal adjustment.
"""
from analytics.src.rar.decomposer import REPLACEMENT_LEVELS


def get_replacement_level(role: str) -> float:
    return REPLACEMENT_LEVELS.get(role, 1.00)
