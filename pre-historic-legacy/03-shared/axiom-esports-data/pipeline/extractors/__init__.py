"""
Game-specific data extractors for the Axiom e-sports data pipeline.

This module provides extractors for different games and sources:
- Counter-Strike (HLTV)
- Valorant (VLR.gg)
"""

from typing import Dict, Type, Optional
import logging

from .base import BaseExtractor, ExtractionResult

logger = logging.getLogger(__name__)

# Registry of available extractors
_EXTRACTOR_REGISTRY: Dict[str, Dict[str, Type[BaseExtractor]]] = {
    'cs': {},
    'valorant': {}
}


def register_extractor(game: str, source: str, extractor_class: Type[BaseExtractor]) -> None:
    """
    Register an extractor class for a game/source combination.
    
    Args:
        game: Game type (e.g., 'cs', 'valorant')
        source: Data source (e.g., 'hltv', 'vlr')
        extractor_class: The extractor class to register
    """
    if game not in _EXTRACTOR_REGISTRY:
        _EXTRACTOR_REGISTRY[game] = {}
    
    _EXTRACTOR_REGISTRY[game][source] = extractor_class
    logger.debug(f"Registered extractor: {game}/{source}")


def get_extractor(
    game: str,
    source: str,
    rate_limiter,
    db_pool,
    coordinator_url: str
) -> Optional[BaseExtractor]:
    """
    Factory function to create an extractor instance.
    
    Args:
        game: Game type (e.g., 'cs', 'valorant')
        source: Data source (e.g., 'hltv', 'vlr')
        rate_limiter: Rate limiter instance
        db_pool: Database pool for storage
        coordinator_url: URL of the job coordinator
    
    Returns:
        Configured extractor instance or None if not found
    
    Example:
        >>> extractor = get_extractor('cs', 'hltv', limiter, pool, 'http://coord:8080')
        >>> async with extractor:
        ...     data = await extractor.extract_match_detail('12345')
    """
    # Lazy import to avoid circular dependencies
    if game == 'cs' and source == 'hltv':
        from .cs.extractor import CSExtractor
        return CSExtractor(rate_limiter, db_pool, coordinator_url)
    
    elif game == 'valorant' and source == 'vlr':
        from .valorant.extractor import ValorantExtractor
        return ValorantExtractor(rate_limiter, db_pool, coordinator_url)
    
    # Check registry for dynamically registered extractors
    if game in _EXTRACTOR_REGISTRY and source in _EXTRACTOR_REGISTRY[game]:
        extractor_class = _EXTRACTOR_REGISTRY[game][source]
        return extractor_class(rate_limiter, db_pool, coordinator_url)
    
    logger.error(f"No extractor found for {game}/{source}")
    return None


def get_available_extractors() -> Dict[str, list]:
    """
    Get list of available extractor configurations.
    
    Returns:
        Dictionary mapping game types to lists of supported sources
    """
    return {
        game: list(sources.keys())
        for game, sources in _EXTRACTOR_REGISTRY.items()
    }


def list_supported_games() -> list:
    """List all supported game types."""
    return list(_EXTRACTOR_REGISTRY.keys())


def list_supported_sources(game: str) -> list:
    """List all supported sources for a game."""
    return list(_EXTRACTOR_REGISTRY.get(game, {}).keys())


# Auto-register built-in extractors
def _auto_register():
    """Automatically register built-in extractors."""
    try:
        from .cs.extractor import CSExtractor
        register_extractor('cs', 'hltv', CSExtractor)
    except ImportError as e:
        logger.warning(f"Could not register CS extractor: {e}")
    
    try:
        from .valorant.extractor import ValorantExtractor
        register_extractor('valorant', 'vlr', ValorantExtractor)
    except ImportError as e:
        logger.warning(f"Could not register Valorant extractor: {e}")


# Run auto-registration on import
_auto_register()


__all__ = [
    'BaseExtractor',
    'ExtractionResult',
    'get_extractor',
    'register_extractor',
    'get_available_extractors',
    'list_supported_games',
    'list_supported_sources',
]
