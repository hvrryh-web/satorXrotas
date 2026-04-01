"""
KCRITR Schema Validator — Strict validation against 37-field schema.

Validates player performance records against the canonical KCRITR schema,
ensuring all required fields are present with correct types and values.
"""
import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import ValidationError as PydanticValidationError

from pipeline.verification.models import (
    SchemaValidationReport,
    ValidationError,
    ValidationSeverity,
)

logger = logging.getLogger(__name__)


class KCRITRValidator:
    """
    Validates against the 37-field KCRITR schema.
    
    Ensures all required fields present, correctly typed, and within
    reasonable value ranges for esports player statistics.
    
    Example:
        >>> validator = KCRITRValidator()
        >>> report = validator.validate(player_record)
        >>> if not report.is_valid:
        ...     print(f"Missing fields: {report.missing_fields}")
    """
    
    # Required fields for a complete KCRITR record
    REQUIRED_FIELDS = [
        # Identity (4 fields)
        "player_id",
        "player_name",
        "team_id",
        "team_name",
        
        # Match context (4 fields)
        "match_id",
        "map_name",
        "match_date",
        "tournament",
        
        # Core performance (8 fields)
        "kills",
        "deaths",
        "assists",
        "acs",
        "adr",
        "kast_pct",
        "hs_pct",
        "first_bloods",
        
        # Advanced metrics (8 fields)
        "first_deaths",
        "multi_kills",
        "clutches_won",
        "clutches_lost",
        "plants",
        "defuses",
        "damage_dealt",
        "rounds_played",
        
        # Economic (4 fields)
        "avg_spent",
        "avg_saved",
        "pistol_round_rating",
        "eco_round_rating",
        
        # Derived analytics (5 fields)
        "sim_rating",
        "rar_score",
        "investment_grade",
        "consistency_score",
        "peak_performance",
        
        # Metadata (4 fields)
        "confidence_tier",
        "map_count",
        "region",
        "role",
    ]
    
    # Field type specifications
    FIELD_TYPES = {
        # UUID fields
        "player_id": (str, UUID),
        "team_id": (str, UUID),
        "match_id": (str, UUID),
        
        # String fields
        "player_name": str,
        "team_name": str,
        "map_name": str,
        "tournament": str,
        "region": str,
        "role": str,
        "investment_grade": str,
        
        # Integer fields (counts)
        "kills": int,
        "deaths": int,
        "assists": int,
        "first_bloods": int,
        "first_deaths": int,
        "multi_kills": int,
        "clutches_won": int,
        "clutches_lost": int,
        "plants": int,
        "defuses": int,
        "damage_dealt": int,
        "rounds_played": int,
        "map_count": int,
        
        # Float fields (metrics)
        "acs": (int, float),
        "adr": (int, float),
        "kast_pct": (int, float),
        "hs_pct": (int, float),
        "avg_spent": (int, float),
        "avg_saved": (int, float),
        "pistol_round_rating": (int, float),
        "eco_round_rating": (int, float),
        "sim_rating": (int, float),
        "rar_score": (int, float),
        "consistency_score": (int, float),
        "peak_performance": (int, float),
        "confidence_tier": (int, float),
        
        # Date fields
        "match_date": (str, datetime),
    }
    
    # Value ranges for semantic validation
    FIELD_RANGES = {
        "kills": (0, 100),
        "deaths": (0, 100),
        "assists": (0, 100),
        "acs": (0, 800),
        "adr": (0, 500),
        "kast_pct": (0, 100),
        "hs_pct": (0, 100),
        "first_bloods": (0, 50),
        "first_deaths": (0, 50),
        "rounds_played": (0, 100),
        "sim_rating": (-5, 5),
        "rar_score": (0, 3),
        "confidence_tier": (0, 100),
        "map_count": (0, 1000),
    }
    
    # Valid investment grades
    VALID_GRADES = {"A+", "A", "B", "C", "D"}
    
    def __init__(self, strict_mode: bool = True) -> None:
        """
        Initialize validator.
        
        Args:
            strict_mode: If True, extra fields are flagged as warnings
        """
        self.strict_mode = strict_mode
        self.required_set = set(self.REQUIRED_FIELDS)
        logger.debug("KCRITRValidator initialized with %d required fields", len(self.REQUIRED_FIELDS))
    
    def validate(self, record: dict[str, Any]) -> SchemaValidationReport:
        """
        Validate a record against KCRITR schema.
        
        Args:
            record: Dictionary containing player performance data
            
        Returns:
            SchemaValidationReport with detailed validation results
        """
        report = SchemaValidationReport(is_valid=True)
        report.record_id = record.get("player_id") or record.get("match_id")
        report.field_count = len(record)
        
        # Check for missing required fields
        record_keys = set(record.keys())
        missing = self.required_set - record_keys
        if missing:
            report.missing_fields = sorted(list(missing))
            report.is_valid = False
            logger.debug("Missing required fields: %s", missing)
        
        # Check for extra fields (in strict mode)
        if self.strict_mode:
            extra = record_keys - self.required_set
            if extra:
                report.extra_fields = sorted(list(extra))
                logger.debug("Extra fields detected: %s", extra)
        
        # Validate field types and ranges
        for field_name, value in record.items():
            if field_name in self.FIELD_TYPES:
                self._validate_field_type(field_name, value, report)
                self._validate_field_range(field_name, value, report)
        
        # Validate investment grade
        if "investment_grade" in record and record["investment_grade"]:
            self._validate_investment_grade(record["investment_grade"], report)
        
        # Calculate completeness percentage
        present_required = len(self.required_set - set(report.missing_fields))
        report.completeness_pct = (present_required / len(self.REQUIRED_FIELDS)) * 100
        
        # Final validity check
        if report.invalid_fields or report.type_mismatches:
            report.is_valid = False
        
        logger.info(
            "Schema validation for %s: %s (%d/%d fields, %.1f%% complete)",
            report.record_id or "unknown",
            "PASSED" if report.is_valid else "FAILED",
            present_required,
            len(self.REQUIRED_FIELDS),
            report.completeness_pct
        )
        
        return report
    
    def _validate_field_type(
        self,
        field_name: str,
        value: Any,
        report: SchemaValidationReport
    ) -> None:
        """Validate a field's type against specification."""
        if value is None:
            return  # None values are allowed (Optional fields)
        
        expected_types = self.FIELD_TYPES[field_name]
        if not isinstance(expected_types, tuple):
            expected_types = (expected_types,)
        
        if not isinstance(value, expected_types):
            report.type_mismatches.append(ValidationError(
                field=field_name,
                code="TYPE_MISMATCH",
                message=f"Expected {expected_types}, got {type(value).__name__}",
                severity=ValidationSeverity.ERROR,
                value=value,
                expected=str(expected_types)
            ))
    
    def _validate_field_range(
        self,
        field_name: str,
        value: Any,
        report: SchemaValidationReport
    ) -> None:
        """Validate a numeric field is within acceptable range."""
        if field_name not in self.FIELD_RANGES or value is None:
            return
        
        try:
            num_value = float(value)
        except (TypeError, ValueError):
            return  # Type error already caught in type validation
        
        min_val, max_val = self.FIELD_RANGES[field_name]
        
        if num_value < min_val or num_value > max_val:
            report.invalid_fields.append(ValidationError(
                field=field_name,
                code="VALUE_OUT_OF_RANGE",
                message=f"Value {num_value} outside range [{min_val}, {max_val}]",
                severity=ValidationSeverity.ERROR,
                value=num_value,
                expected=f"[{min_val}, {max_val}]"
            ))
    
    def _validate_investment_grade(
        self,
        grade: str,
        report: SchemaValidationReport
    ) -> None:
        """Validate investment grade is one of allowed values."""
        if grade not in self.VALID_GRADES:
            report.invalid_fields.append(ValidationError(
                field="investment_grade",
                code="INVALID_GRADE",
                message=f"Invalid investment grade '{grade}'. Must be one of: {self.VALID_GRADES}",
                severity=ValidationSeverity.ERROR,
                value=grade,
                expected=str(self.VALID_GRADES)
            ))
    
    def validate_batch(
        self,
        records: list[dict[str, Any]]
    ) -> list[SchemaValidationReport]:
        """
        Validate multiple records efficiently.
        
        Args:
            records: List of player performance records
            
        Returns:
            List of validation reports (one per record)
        """
        return [self.validate(record) for record in records]
    
    def get_missing_fields(self, record: dict[str, Any]) -> list[str]:
        """
        Quick check for missing required fields.
        
        Args:
            record: Record to check
            
        Returns:
            List of missing field names
        """
        return sorted(list(self.required_set - set(record.keys())))
    
    def calculate_completeness(self, record: dict[str, Any]) -> float:
        """
        Calculate field completeness percentage.
        
        Args:
            record: Record to analyze
            
        Returns:
            Percentage of required fields present (0-100)
        """
        present = sum(1 for f in self.REQUIRED_FIELDS if f in record and record[f] is not None)
        return (present / len(self.REQUIRED_FIELDS)) * 100
