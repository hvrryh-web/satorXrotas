"""
Duplicate Detector — Sophisticated duplicate detection beyond checksums.

Detects duplicates at multiple levels:
1. Exact duplicate (same checksum)
2. Content duplicate (same match, same stats, different source)
3. Near-duplicate (same match, slightly different stats - content drift)
4. Logical duplicate (same teams, same date, different match_id)
"""
import hashlib
import logging
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Any, Optional, Protocol

from pipeline.verification.models import (
    DuplicateResult,
    DuplicateType,
)

logger = logging.getLogger(__name__)


class StorageBackend(Protocol):
    """Protocol for storage backend (database, cache, etc.)."""
    
    def get_by_checksum(self, checksum: str) -> Optional[dict]:
        """Get record by checksum."""
        ...
    
    def find_by_composite_key(
        self,
        tournament: str,
        team_a: str,
        team_b: str,
        date: str,
        map_name: Optional[str] = None
    ) -> list[dict]:
        """Find records by composite match key."""
        ...
    
    def get_by_match_id(self, match_id: str) -> Optional[dict]:
        """Get record by match ID."""
        ...


class DuplicateDetector:
    """
    Sophisticated duplicate detection for esports data.
    
    Detects duplicates across multiple dimensions:
    - Exact: Same content checksum
    - Content: Same match details, different source
    - Near: Same match, slightly different stats (drift detection)
    - Logical: Same teams/date, different IDs
    
    Example:
        >>> detector = DuplicateDetector(storage_backend)
        >>> 
        >>> # Check for exact duplicate
        >>> if detector.check_exact_duplicate(checksum):
        ...     print("Exact duplicate found")
        >>> 
        >>> # Check for content duplicates
        >>> result = detector.check_content_duplicate(match_data)
        >>> if result.is_duplicate:
        ...     print(f"Duplicate type: {result.duplicate_type}")
    """
    
    # Similarity thresholds
    EXACT_THRESHOLD = 1.0
    CONTENT_THRESHOLD = 0.95
    NEAR_DUPLICATE_THRESHOLD = 0.85
    LOGICAL_THRESHOLD = 0.70
    
    # Fields to ignore when comparing stats (metadata)
    IGNORE_FIELDS = {
        "match_id", "player_id", "checksum", "source", "ingested_at",
        "updated_at", "_id", "id"
    }
    
    # Core fields for content comparison
    CONTENT_KEY_FIELDS = [
        "tournament", "team_a", "team_b", "match_date", "map_name", "score"
    ]
    
    # Stats fields for near-duplicate detection
    STATS_FIELDS = [
        "kills", "deaths", "assists", "acs", "adr", "kast_pct", "hs_pct"
    ]
    
    def __init__(self, storage: Optional[StorageBackend] = None) -> None:
        """
        Initialize duplicate detector.
        
        Args:
            storage: Storage backend for lookups (optional for stateless mode)
        """
        self.storage = storage
        self._checksum_cache: set[str] = set()
        self._content_cache: dict[str, str] = {}  # content_key -> match_id
        logger.debug("DuplicateDetector initialized")
    
    def compute_checksum(self, data: dict[str, Any]) -> str:
        """
        Compute normalized checksum for data.
        
        Args:
            data: Dictionary to checksum
            
        Returns:
            SHA-256 hex digest of normalized data
        """
        # Normalize: sort keys, consistent formatting
        normalized = self._normalize_for_comparison(data)
        content = str(sorted(normalized.items()))
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
    
    def check_exact_duplicate(self, checksum: str) -> bool:
        """
        Check if exact content already exists.
        
        Args:
            checksum: SHA-256 checksum to check
            
        Returns:
            True if exact duplicate exists
        """
        # Check in-memory cache first
        if checksum in self._checksum_cache:
            logger.debug("Exact duplicate found in cache: %s", checksum[:12])
            return True
        
        # Check storage if available
        if self.storage:
            existing = self.storage.get_by_checksum(checksum)
            if existing:
                logger.info("Exact duplicate found in storage: %s", checksum[:12])
                return True
        
        return False
    
    def check_content_duplicate(self, match_data: dict[str, Any]) -> DuplicateResult:
        """
        Check if this match data already exists under different match_id.
        
        Compares: tournament, teams, date, map, score
        
        Args:
            match_data: Match data to check
            
        Returns:
            DuplicateResult with detection details
        """
        result = DuplicateResult(is_duplicate=False, duplicate_type=DuplicateType.CONTENT)
        
        # Build content key
        content_key = self._build_content_key(match_data)
        if not content_key:
            result.details["error"] = "Cannot build content key from data"
            return result
        
        # Check cache
        if content_key in self._content_cache:
            result.is_duplicate = True
            result.existing_ids = [self._content_cache[content_key]]
            result.similarity_score = 1.0
            result.confidence = 100
            logger.info("Content duplicate found in cache: %s", content_key)
            return result
        
        # Check storage
        if self.storage:
            tournament = match_data.get("tournament", "")
            team_a = match_data.get("team_a", "") or match_data.get("team", "")
            team_b = match_data.get("team_b", "") or match_data.get("opponent", "")
            date = match_data.get("match_date", "")
            map_name = match_data.get("map_name")
            
            existing = self.storage.find_by_composite_key(
                tournament, team_a, team_b, date, map_name
            )
            
            if existing:
                result.is_duplicate = True
                result.existing_ids = [e.get("match_id") for e in existing if e.get("match_id")]
                result.similarity_score = 1.0
                result.confidence = 95
                logger.info(
                    "Content duplicate found: %d existing record(s)",
                    len(result.existing_ids)
                )
        
        return result
    
    def check_near_duplicate(
        self,
        new_stats: dict[str, Any],
        existing_stats: dict[str, Any]
    ) -> float:
        """
        Calculate similarity score (0-1) between stat sets.
        
        High similarity may indicate content drift (same match, 
        slightly different reported stats from different sources).
        
        Args:
            new_stats: New statistics
            existing_stats: Existing statistics to compare against
            
        Returns:
            Similarity score between 0 and 1
        """
        # Extract comparable fields
        new_values = self._extract_stats(new_stats)
        existing_values = self._extract_stats(existing_stats)
        
        if not new_values or not existing_values:
            return 0.0
        
        # Calculate per-field similarity
        similarities = []
        for field in self.STATS_FIELDS:
            if field in new_values and field in existing_values:
                sim = self._calculate_field_similarity(
                    new_values[field],
                    existing_values[field]
                )
                similarities.append(sim)
        
        if not similarities:
            return 0.0
        
        # Overall similarity is average of field similarities
        overall_similarity = sum(similarities) / len(similarities)
        
        logger.debug(
            "Near-duplicate similarity: %.3f (%d fields compared)",
            overall_similarity,
            len(similarities)
        )
        
        return overall_similarity
    
    def find_logical_duplicates(
        self,
        tournament: str,
        team_a: str,
        team_b: str,
        date: str,
        tolerance_days: int = 1
    ) -> list[str]:
        """
        Find matches that look like the same game but different IDs.
        
        Searches within a date tolerance window to account for timezone
        differences and reporting delays.
        
        Args:
            tournament: Tournament name
            team_a: First team name
            team_b: Second team name
            date: Match date (ISO format)
            tolerance_days: Days to search around date
            
        Returns:
            List of match IDs that may be logical duplicates
        """
        duplicate_ids: list[str] = []
        
        if not self.storage:
            return duplicate_ids
        
        try:
            base_date = datetime.fromisoformat(date.replace("Z", "+00:00"))
        except ValueError:
            logger.warning("Cannot parse date for logical duplicate search: %s", date)
            return duplicate_ids
        
        # Search date range
        for offset in range(-tolerance_days, tolerance_days + 1):
            search_date = (base_date + timedelta(days=offset)).isoformat()[:10]
            
            matches = self.storage.find_by_composite_key(
                tournament, team_a, team_b, search_date
            )
            
            for match in matches:
                match_id = match.get("match_id")
                if match_id:
                    duplicate_ids.append(match_id)
        
        logger.info(
            "Found %d potential logical duplicates for %s vs %s on %s",
            len(duplicate_ids),
            team_a,
            team_b,
            date
        )
        
        return duplicate_ids
    
    def detect_all_duplicates(
        self,
        match_data: dict[str, Any],
        existing_records: Optional[list[dict]] = None
    ) -> DuplicateResult:
        """
        Run all duplicate detection methods.
        
        Args:
            match_data: New match data to check
            existing_records: Optional list of records to compare against
            
        Returns:
            DuplicateResult with comprehensive detection results
        """
        # 1. Check exact duplicate
        checksum = self.compute_checksum(match_data)
        if self.check_exact_duplicate(checksum):
            return DuplicateResult(
                is_duplicate=True,
                duplicate_type=DuplicateType.EXACT,
                similarity_score=1.0,
                confidence=100
            )
        
        # 2. Check content duplicate
        content_result = self.check_content_duplicate(match_data)
        if content_result.is_duplicate:
            return content_result
        
        # 3. Check near-duplicates against provided records
        if existing_records:
            for existing in existing_records:
                similarity = self.check_near_duplicate(match_data, existing)
                
                if similarity >= self.NEAR_DUPLICATE_THRESHOLD:
                    return DuplicateResult(
                        is_duplicate=True,
                        duplicate_type=DuplicateType.NEAR,
                        existing_ids=[existing.get("match_id", "unknown")],
                        similarity_score=similarity,
                        confidence=similarity * 100
                    )
        
        # 4. Check logical duplicates
        tournament = match_data.get("tournament", "")
        team_a = match_data.get("team_a", "") or match_data.get("team", "")
        team_b = match_data.get("team_b", "") or match_data.get("opponent", "")
        date = match_data.get("match_date", "")
        
        if tournament and team_a and team_b and date:
            logical_ids = self.find_logical_duplicates(tournament, team_a, team_b, date)
            if logical_ids:
                return DuplicateResult(
                    is_duplicate=True,
                    duplicate_type=DuplicateType.LOGICAL,
                    existing_ids=logical_ids,
                    similarity_score=self.LOGICAL_THRESHOLD,
                    confidence=70
                )
        
        # No duplicates found
        return DuplicateResult(is_duplicate=False)
    
    def register_checksum(self, checksum: str) -> None:
        """Register a checksum as seen (for in-memory tracking)."""
        self._checksum_cache.add(checksum)
    
    def register_content(self, content_key: str, match_id: str) -> None:
        """Register a content key as seen."""
        self._content_cache[content_key] = match_id
    
    def _normalize_for_comparison(self, data: dict[str, Any]) -> dict[str, Any]:
        """Normalize data for consistent comparison."""
        normalized = {}
        for key, value in data.items():
            if key in self.IGNORE_FIELDS:
                continue
            # Normalize strings (lowercase, strip)
            if isinstance(value, str):
                normalized[key] = value.lower().strip()
            # Round floats for comparison
            elif isinstance(value, float):
                normalized[key] = round(value, 2)
            else:
                normalized[key] = value
        return normalized
    
    def _build_content_key(self, match_data: dict[str, Any]) -> Optional[str]:
        """Build a unique content key from match data."""
        parts = []
        for field in self.CONTENT_KEY_FIELDS:
            value = match_data.get(field)
            if value:
                parts.append(str(value).lower().strip())
        
        if len(parts) < 4:  # Need at least tournament, 2 teams, and date
            return None
        
        return "|".join(parts)
    
    def _extract_stats(self, data: dict[str, Any]) -> dict[str, float]:
        """Extract numeric stats for comparison."""
        stats = {}
        for field in self.STATS_FIELDS:
            value = data.get(field)
            if value is not None:
                try:
                    stats[field] = float(value)
                except (TypeError, ValueError):
                    pass
        return stats
    
    def _calculate_field_similarity(self, val1: float, val2: float) -> float:
        """Calculate similarity between two numeric values."""
        if val1 == val2:
            return 1.0
        
        # Handle zeros
        if val1 == 0 and val2 == 0:
            return 1.0
        if val1 == 0 or val2 == 0:
            return 0.0
        
        # Use relative difference
        max_val = max(abs(val1), abs(val2))
        diff = abs(val1 - val2)
        similarity = 1.0 - (diff / max_val)
        
        return max(0.0, min(1.0, similarity))
    
    def clear_cache(self) -> None:
        """Clear in-memory caches."""
        self._checksum_cache.clear()
        self._content_cache.clear()
