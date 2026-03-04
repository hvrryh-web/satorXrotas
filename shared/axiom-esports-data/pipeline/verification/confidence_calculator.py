"""
Confidence Calculator — Calculate data confidence scores.

Calculates confidence tier (1-100) based on:
- Data source reliability
- Number of cross-references
- Recency
- Schema completeness
- Semantic consistency
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from pipeline.verification.models import (
    ConfidenceFactors,
    ConfidenceScore,
    ConfidenceTier,
)

logger = logging.getLogger(__name__)


class ConfidenceCalculator:
    """
    Calculate comprehensive confidence scores for esports data.
    
    Combines multiple factors to produce a 0-100 confidence score
    and tier classification. Factors include:
    - Source reliability (some sources more trusted than others)
    - Cross-reference count (more sources = higher confidence)
    - Recency (recent data more reliable)
    - Schema completeness (more fields present = higher confidence)
    - Semantic consistency (values make logical sense)
    
    Example:
        >>> calculator = ConfidenceCalculator()
        >>> context = {"source": "vlr_gg", "cross_refs": 2, "date": "2024-01-15"}
        >>> score = calculator.calculate_match_confidence(match_data, context)
        >>> print(f"Confidence: {score.score}/100 ({score.tier})")
    """
    
    # Source reliability scores (0-100)
    SOURCE_RELIABILITY = {
        "vlr_gg": 95,      # Primary source
        "hltv": 90,        # Well-established
        "liquipedia": 85,  # Community-maintained
        "grid": 80,        # Tournament organizer
        "manual": 70,      # Human-entered
        "unknown": 50,     # Unverified source
    }
    
    # Weight factors for overall confidence calculation
    WEIGHTS = {
        "source_reliability": 0.25,
        "cross_reference_count": 0.20,
        "recency": 0.20,
        "schema_completeness": 0.20,
        "semantic_consistency": 0.15,
    }
    
    # Recency thresholds
    FRESH_DAYS = 7       # Full score within 7 days
    RECENT_DAYS = 30     # Slight decay after 30 days
    OLD_DAYS = 90        # Significant decay after 90 days
    MAX_AGE_DAYS = 365   # Minimum score after 1 year
    
    # Cross-reference scoring
    MAX_CROSS_REFS = 5   # Maximum cross-references that count
    POINTS_PER_CROSS_REF = 20  # Points per cross-reference
    
    def __init__(self, custom_weights: Optional[dict[str, float]] = None) -> None:
        """
        Initialize confidence calculator.
        
        Args:
            custom_weights: Optional custom weights for confidence factors
        """
        self.weights = custom_weights or self.WEIGHTS
        self._validate_weights()
        logger.debug("ConfidenceCalculator initialized with weights: %s", self.weights)
    
    def calculate_match_confidence(
        self,
        match_data: dict[str, Any],
        context: dict[str, Any]
    ) -> ConfidenceScore:
        """
        Calculate 0-100 confidence score for match data.
        
        Args:
            match_data: The match/player data to score
            context: Context including source, cross_refs, date, etc.
            
        Returns:
            ConfidenceScore with detailed breakdown
            
        Example:
            >>> calculator = ConfidenceCalculator()
            >>> context = {
            ...     "source": "vlr_gg",
            ...     "cross_refs": ["hltv"],
            ...     "date": "2024-01-15",
            ...     "schema_completeness": 95
            ... }
            >>> score = calculator.calculate_match_confidence(data, context)
        """
        factors = ConfidenceFactors()
        
        # 1. Source reliability (0-100)
        factors.source_reliability = self._calculate_source_reliability(context.get("source", "unknown"))
        
        # 2. Cross-reference count (0-100)
        factors.cross_reference_count = self._calculate_cross_ref_score(context.get("cross_refs", []))
        
        # 3. Recency (0-100)
        factors.recency = self._calculate_recency_score(context.get("date"))
        
        # 4. Schema completeness (0-100)
        factors.schema_completeness = context.get("schema_completeness", 0)
        if not factors.schema_completeness and match_data:
            factors.schema_completeness = self._calculate_completeness(match_data)
        
        # 5. Semantic consistency (0-100)
        factors.semantic_consistency = context.get("semantic_consistency", 100)
        
        # Calculate weighted total
        total_score = (
            factors.source_reliability * self.weights["source_reliability"] +
            factors.cross_reference_count * self.weights["cross_reference_count"] +
            factors.recency * self.weights["recency"] +
            factors.schema_completeness * self.weights["schema_completeness"] +
            factors.semantic_consistency * self.weights["semantic_consistency"]
        )
        
        # Ensure bounds
        total_score = max(0.0, min(100.0, total_score))
        
        # Determine tier
        tier = self.get_confidence_tier(total_score)
        
        logger.info(
            "Confidence score calculated: %.1f (%s) for source=%s",
            total_score,
            tier.value,
            context.get("source", "unknown")
        )
        
        return ConfidenceScore(
            score=round(total_score, 1),
            tier=tier,
            factors=factors
        )
    
    def get_confidence_tier(self, score: float) -> ConfidenceTier:
        """
        Map score to tier.
        
        Args:
            score: 0-100 confidence score
            
        Returns:
            ConfidenceTier classification
            
        Tiers:
            - CRITICAL: 90-100 (Highest confidence)
            - HIGH: 75-89 (Very good confidence)
            - MEDIUM: 50-74 (Acceptable confidence)
            - LOW: 0-49 (Low confidence, verify before use)
        """
        if score >= 90:
            return ConfidenceTier.CRITICAL
        elif score >= 75:
            return ConfidenceTier.HIGH
        elif score >= 50:
            return ConfidenceTier.MEDIUM
        else:
            return ConfidenceTier.LOW
    
    def calculate_player_confidence(
        self,
        player_data: dict[str, Any],
        match_history: list[dict[str, Any]]
    ) -> ConfidenceScore:
        """
        Calculate confidence score for a player's stats.
        
        Takes into account consistency across matches.
        
        Args:
            player_data: Current player statistics
            match_history: Historical matches for consistency analysis
            
        Returns:
            ConfidenceScore for player data
        """
        # Start with base match confidence
        base_context = {
            "source": player_data.get("source", "unknown"),
            "cross_refs": player_data.get("cross_references", []),
            "date": player_data.get("match_date"),
            "schema_completeness": self._calculate_completeness(player_data),
        }
        
        base_score = self.calculate_match_confidence(player_data, base_context)
        
        # Adjust for consistency if we have history
        if len(match_history) >= 3:
            consistency = self._calculate_consistency(player_data, match_history)
            # Blend base score with consistency
            adjusted_score = (base_score.score * 0.7) + (consistency * 0.3)
            base_score.score = round(adjusted_score, 1)
            base_score.tier = self.get_confidence_tier(base_score.score)
            base_score.factors.semantic_consistency = round(consistency, 1)
        
        return base_score
    
    def _calculate_source_reliability(self, source: str) -> float:
        """Get reliability score for data source."""
        source_lower = source.lower().replace(".", "_").replace(" ", "_")
        
        # Try direct match
        if source_lower in self.SOURCE_RELIABILITY:
            return float(self.SOURCE_RELIABILITY[source_lower])
        
        # Try fuzzy match
        for known_source, score in self.SOURCE_RELIABILITY.items():
            if known_source in source_lower or source_lower in known_source:
                return float(score)
        
        return float(self.SOURCE_RELIABILITY["unknown"])
    
    def _calculate_cross_ref_score(self, cross_refs: list[str]) -> float:
        """Calculate score based on number of cross-references."""
        if not cross_refs:
            return 0.0
        
        # Count unique cross-references
        unique_refs = len(set(str(ref).lower() for ref in cross_refs))
        
        # Score based on count (diminishing returns after MAX_CROSS_REFS)
        effective_refs = min(unique_refs, self.MAX_CROSS_REFS)
        score = (effective_refs / self.MAX_CROSS_REFS) * 100
        
        return score
    
    def _calculate_recency_score(self, date: Optional[str | datetime]) -> float:
        """Calculate score based on data recency."""
        if not date:
            return 50.0  # Neutral if no date
        
        try:
            if isinstance(date, str):
                # Try parsing ISO format
                try:
                    match_date = datetime.fromisoformat(date.replace("Z", "+00:00"))
                except ValueError:
                    # Try date only format
                    match_date = datetime.strptime(date, "%Y-%m-%d")
            else:
                match_date = date
            
            # Ensure timezone-naive for comparison
            if match_date.tzinfo:
                match_date = match_date.replace(tzinfo=None)
            
            now = datetime.utcnow()
            age_days = (now - match_date).days
            
            if age_days <= self.FRESH_DAYS:
                return 100.0
            elif age_days <= self.RECENT_DAYS:
                # Linear decay from 100 to 80
                return 100 - ((age_days - self.FRESH_DAYS) / (self.RECENT_DAYS - self.FRESH_DAYS) * 20)
            elif age_days <= self.OLD_DAYS:
                # Linear decay from 80 to 50
                return 80 - ((age_days - self.RECENT_DAYS) / (self.OLD_DAYS - self.RECENT_DAYS) * 30)
            elif age_days <= self.MAX_AGE_DAYS:
                # Linear decay from 50 to 25
                return 50 - ((age_days - self.OLD_DAYS) / (self.MAX_AGE_DAYS - self.OLD_DAYS) * 25)
            else:
                return 25.0  # Minimum score for very old data
                
        except (ValueError, TypeError) as e:
            logger.warning("Could not parse date for recency: %s (%s)", date, e)
            return 50.0
    
    def _calculate_completeness(self, data: dict[str, Any]) -> float:
        """Calculate schema completeness percentage."""
        # Define expected fields for a complete record
        expected_fields = [
            "player_id", "player_name", "team", "kills", "deaths",
            "assists", "acs", "adr", "kast_pct", "hs_pct"
        ]
        
        if not data:
            return 0.0
        
        present = sum(1 for f in expected_fields if f in data and data[f] is not None)
        return (present / len(expected_fields)) * 100
    
    def _calculate_consistency(
        self,
        player_data: dict[str, Any],
        match_history: list[dict[str, Any]]
    ) -> float:
        """Calculate consistency score from match history."""
        if len(match_history) < 2:
            return 100.0
        
        # Compare current stats to historical average
        stats_to_check = ["acs", "adr", "kast_pct", "hs_pct"]
        deviations = []
        
        for stat in stats_to_check:
            current = player_data.get(stat)
            if current is None:
                continue
            
            try:
                current_val = float(current)
                historical = [float(m.get(stat)) for m in match_history 
                             if m.get(stat) is not None]
                
                if historical:
                    avg = sum(historical) / len(historical)
                    std_dev = (sum((x - avg) ** 2 for x in historical) / len(historical)) ** 0.5
                    
                    if std_dev > 0:
                        # Z-score of current value
                        z_score = abs(current_val - avg) / std_dev
                        # Convert to 0-100 score (lower z-score = higher consistency)
                        consistency = max(0, 100 - (z_score * 20))
                        deviations.append(consistency)
                    else:
                        deviations.append(100.0)  # No variation = perfect consistency
                        
            except (TypeError, ValueError):
                continue
        
        if deviations:
            return sum(deviations) / len(deviations)
        return 100.0
    
    def _validate_weights(self) -> None:
        """Ensure weights sum to approximately 1.0."""
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.001:
            logger.warning("Confidence weights sum to %f, not 1.0", total)
    
    def should_accept_data(self, score: ConfidenceScore, min_tier: ConfidenceTier = ConfidenceTier.MEDIUM) -> bool:
        """
        Determine if data should be accepted based on confidence.
        
        Args:
            score: Confidence score to evaluate
            min_tier: Minimum acceptable tier
            
        Returns:
            True if data meets confidence threshold
        """
        tier_order = [
            ConfidenceTier.LOW,
            ConfidenceTier.MEDIUM,
            ConfidenceTier.HIGH,
            ConfidenceTier.CRITICAL
        ]
        
        score_rank = tier_order.index(score.tier)
        min_rank = tier_order.index(min_tier)
        
        return score_rank >= min_rank
