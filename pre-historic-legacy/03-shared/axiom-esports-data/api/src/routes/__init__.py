"""
API Routes Package

Exports all FastAPI route modules for the Axiom Esports Data API.
"""

from api.src.routes import players, matches, analytics

__all__ = [
    "players",
    "matches",
    "analytics",
]
