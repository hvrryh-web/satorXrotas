"""
Pydantic models for data verification framework.

Defines validation result structures, duplicate detection results,
and confidence scoring outputs used across the verification pipeline.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationError(BaseModel):
    """Single validation error with context."""
    field: str = Field(..., description="Field path where error occurred")
    code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    severity: ValidationSeverity = Field(default=ValidationSeverity.ERROR)
    value: Optional[Any] = Field(default=None, description="Actual value that failed")
    expected: Optional[Any] = Field(default=None, description="Expected value/range")


class ValidationWarning(BaseModel):
    """Non-critical validation warning."""
    field: str = Field(..., description="Field path where warning occurred")
    code: str = Field(..., description="Warning code")
    message: str = Field(..., description="Human-readable warning message")
    value: Optional[Any] = Field(default=None, description="Value that triggered warning")


class ValidationResult(BaseModel):
    """Complete validation result for a data record."""
    is_valid: bool = Field(..., description="Whether validation passed")
    errors: list[ValidationError] = Field(default_factory=list)
    warnings: list[ValidationWarning] = Field(default_factory=list)
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Confidence score (0-100)"
    )
    validated_at: datetime = Field(default_factory=datetime.utcnow)
    validator_version: str = Field(default="1.0.0")
    
    def add_error(
        self,
        field: str,
        code: str,
        message: str,
        value: Optional[Any] = None,
        expected: Optional[Any] = None,
        severity: ValidationSeverity = ValidationSeverity.ERROR
    ) -> None:
        """Add a validation error."""
        self.errors.append(ValidationError(
            field=field,
            code=code,
            message=message,
            value=value,
            expected=expected,
            severity=severity
        ))
        self.is_valid = False
    
    def add_warning(
        self,
        field: str,
        code: str,
        message: str,
        value: Optional[Any] = None
    ) -> None:
        """Add a validation warning."""
        self.warnings.append(ValidationWarning(
            field=field,
            code=code,
            message=message,
            value=value
        ))
    
    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """Merge another validation result into this one."""
        return ValidationResult(
            is_valid=self.is_valid and other.is_valid,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
            confidence=(self.confidence + other.confidence) / 2,
            validated_at=datetime.utcnow()
        )


class DuplicateType(str, Enum):
    """Types of duplicates that can be detected."""
    EXACT = "exact"           # Same checksum
    CONTENT = "content"       # Same match, same stats, different source
    NEAR = "near"             # Same match, slightly different stats (content drift)
    LOGICAL = "logical"       # Same teams, same date, different match_id


class DuplicateResult(BaseModel):
    """Result of duplicate detection check."""
    is_duplicate: bool = Field(..., description="Whether a duplicate was found")
    duplicate_type: DuplicateType = Field(
        default=DuplicateType.EXACT,
        description="Type of duplicate detected"
    )
    existing_ids: list[str] = Field(
        default_factory=list,
        description="IDs of existing duplicate records"
    )
    similarity_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Similarity score for near-duplicates (0-1)"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Confidence in duplicate detection"
    )
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional duplicate detection details"
    )


class ConfidenceTier(str, Enum):
    """Confidence tier classification."""
    CRITICAL = "CRITICAL"    # 90-100
    HIGH = "HIGH"            # 75-89
    MEDIUM = "MEDIUM"        # 50-74
    LOW = "LOW"              # 0-49


class ConfidenceFactors(BaseModel):
    """Individual factors contributing to confidence score."""
    source_reliability: float = Field(default=0.0, ge=0.0, le=100.0)
    cross_reference_count: float = Field(default=0.0, ge=0.0, le=100.0)
    recency: float = Field(default=0.0, ge=0.0, le=100.0)
    schema_completeness: float = Field(default=0.0, ge=0.0, le=100.0)
    semantic_consistency: float = Field(default=0.0, ge=0.0, le=100.0)
    temporal_validity: float = Field(default=0.0, ge=0.0, le=100.0)


class ConfidenceScore(BaseModel):
    """Complete confidence score with breakdown."""
    score: float = Field(..., ge=0.0, le=100.0)
    tier: ConfidenceTier = Field(...)
    factors: ConfidenceFactors = Field(default_factory=ConfidenceFactors)
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def get_tier(self) -> ConfidenceTier:
        """Determine tier from score."""
        if self.score >= 90:
            return ConfidenceTier.CRITICAL
        elif self.score >= 75:
            return ConfidenceTier.HIGH
        elif self.score >= 50:
            return ConfidenceTier.MEDIUM
        else:
            return ConfidenceTier.LOW


class SchemaValidationReport(BaseModel):
    """Detailed KCRITR schema validation report."""
    record_id: Optional[str] = Field(default=None)
    is_valid: bool = Field(...)
    missing_fields: list[str] = Field(default_factory=list)
    invalid_fields: list[ValidationError] = Field(default_factory=list)
    extra_fields: list[str] = Field(default_factory=list)
    type_mismatches: list[ValidationError] = Field(default_factory=list)
    field_count: int = Field(default=0)
    required_field_count: int = Field(default=37)
    completeness_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    validated_at: datetime = Field(default_factory=datetime.utcnow)


class CrossReferenceMatch(BaseModel):
    """Result of comparing against an external reference."""
    source: str = Field(..., description="External source name (e.g., 'hltv')")
    field: str = Field(..., description="Field being compared")
    our_value: Any = Field(...)
    their_value: Any = Field(...)
    difference: float = Field(..., description="Absolute difference")
    within_tolerance: bool = Field(...)
    tolerance_pct: float = Field(default=5.0)


class CrossReferenceResult(BaseModel):
    """Complete cross-reference validation result."""
    is_valid: bool = Field(...)
    matches: list[CrossReferenceMatch] = Field(default_factory=list)
    mismatches: list[CrossReferenceMatch] = Field(default_factory=list)
    missing_in_reference: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=100.0)


class VerificationSummary(BaseModel):
    """Summary of complete verification pipeline run."""
    record_id: str = Field(...)
    passed_all_checks: bool = Field(...)
    
    # Individual check results
    transport_valid: bool = Field(default=False)
    schema_valid: bool = Field(default=False)
    semantic_valid: bool = Field(default=False)
    temporal_valid: bool = Field(default=False)
    crossref_valid: Optional[bool] = Field(default=None)
    is_duplicate: bool = Field(default=False)
    
    # Scores
    confidence_score: float = Field(default=0.0, ge=0.0, le=100.0)
    confidence_tier: ConfidenceTier = Field(default=ConfidenceTier.LOW)
    
    # Details
    validation_result: ValidationResult = Field(default_factory=lambda: ValidationResult(is_valid=True))
    duplicate_result: Optional[DuplicateResult] = Field(default=None)
    schema_report: Optional[SchemaValidationReport] = Field(default=None)
    
    # Metadata
    verified_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: float = Field(default=0.0)
    
    def to_verdict(self) -> str:
        """Generate human-readable verification verdict."""
        if self.passed_all_checks and self.confidence_tier in (ConfidenceTier.CRITICAL, ConfidenceTier.HIGH):
            return "✅ VERIFIED"
        elif self.passed_all_checks and self.confidence_tier == ConfidenceTier.MEDIUM:
            return "⚠️  ACCEPTABLE"
        elif self.is_duplicate:
            return "🔄 DUPLICATE"
        else:
            return "❌ REJECTED"
