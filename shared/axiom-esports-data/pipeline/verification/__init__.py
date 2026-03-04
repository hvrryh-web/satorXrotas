"""
Axiom Esports Data Verification Framework
=========================================

Comprehensive multi-layer data verification system for the esports pipeline.

This framework provides validation at every pipeline stage to ensure data quality
and catch duplicates/errors early in the processing lifecycle.

Main Components:
    - IntegrityVerifier: Multi-layer integrity checks (transport, schema, semantic, temporal, crossref)
    - DuplicateDetector: Sophisticated duplicate detection (exact, content, near, logical)
    - ConfidenceCalculator: Data confidence scoring with tier classification
    - KCRITRValidator: Strict 37-field schema validation
    - Models: Pydantic models for validation results and confidence scores

Quick Start:
    >>> from pipeline.verification import (
    ...     IntegrityVerifier,
    ...     DuplicateDetector,
    ...     ConfidenceCalculator,
    ...     KCRITRValidator,
    ... )
    >>> 
    >>> # Verify data integrity
    >>> verifier = IntegrityVerifier()
    >>> result = verifier.verify_all(match_data, context={
    ...     "content": raw_content,
    ...     "expected_checksum": expected_hash,
    ...     "hltv_data": hltv_reference
    ... })
    >>> 
    >>> # Check for duplicates
    >>> detector = DuplicateDetector(storage_backend)
    >>> dup_result = detector.detect_all_duplicates(match_data)
    >>> 
    >>> # Calculate confidence
    >>> calculator = ConfidenceCalculator()
    >>> score = calculator.calculate_match_confidence(match_data, context={
    ...     "source": "vlr_gg",
    ...     "cross_refs": ["hltv"],
    ...     "date": "2024-01-15"
    ... })
    >>> print(f"Confidence: {score.score}/100 ({score.tier.value})")

Pipeline Integration:
    The verification framework integrates with the PipelineOrchestrator at stages:
    - VERIFY: Transport integrity checks
    - PARSE: Schema validation
    - TRANSFORM: Semantic validation
    - CROSSREF: Cross-reference validation
    - STORE: Duplicate detection and confidence scoring

Example Pipeline Usage:
    >>> from pipeline import PipelineOrchestrator
    >>> from pipeline.verification import VerificationPipeline
    >>> 
    >>> orchestrator = PipelineOrchestrator()
    >>> verification = VerificationPipeline(orchestrator)
    >>> 
    >>> # Run verification as part of pipeline
    >>> result = await verification.verify_match(match_id, match_data)
    >>> if result.passed_all_checks:
    ...     await orchestrator.store(match_data)
"""

from pipeline.verification.confidence_calculator import ConfidenceCalculator
from pipeline.verification.duplicate_detector import DuplicateDetector
from pipeline.verification.integrity_verifier import IntegrityVerifier
from pipeline.verification.models import (
    ConfidenceFactors,
    ConfidenceScore,
    ConfidenceTier,
    CrossReferenceMatch,
    CrossReferenceResult,
    DuplicateResult,
    DuplicateType,
    SchemaValidationReport,
    ValidationError,
    ValidationResult,
    ValidationSeverity,
    ValidationSummary,
    ValidationWarning,
)
from pipeline.verification.schema_validator import KCRITRValidator

__all__ = [
    # Main classes
    "IntegrityVerifier",
    "DuplicateDetector",
    "ConfidenceCalculator",
    "KCRITRValidator",
    # Result models
    "ValidationResult",
    "ValidationError",
    "ValidationWarning",
    "ValidationSeverity",
    "DuplicateResult",
    "DuplicateType",
    "ConfidenceScore",
    "ConfidenceTier",
    "ConfidenceFactors",
    "CrossReferenceResult",
    "CrossReferenceMatch",
    "SchemaValidationReport",
    "ValidationSummary",
]

__version__ = "1.0.0"


class VerificationPipeline:
    """
    High-level verification pipeline that orchestrates all verification components.
    
    Provides a unified interface for running complete verification workflows
    with configurable validation levels and duplicate detection.
    
    Example:
        >>> pipeline = VerificationPipeline()
        >>> summary = await pipeline.verify_complete(match_data, context={
        ...     "source": "vlr_gg",
        ...     "expected_checksum": "abc123..."
        ... })
        >>> 
        >>> if summary.passed_all_checks:
        ...     print(f"✅ Verified with {summary.confidence_score}/100 confidence")
        ... else:
        ...     print(f"❌ Failed: {[e.message for e in summary.validation_result.errors]}")
    """
    
    def __init__(
        self,
        integrity_verifier: IntegrityVerifier | None = None,
        duplicate_detector: DuplicateDetector | None = None,
        confidence_calculator: ConfidenceCalculator | None = None,
        schema_validator: KCRITRValidator | None = None,
    ) -> None:
        """
        Initialize verification pipeline with optional custom components.
        
        Args:
            integrity_verifier: Custom integrity verifier (creates default if None)
            duplicate_detector: Custom duplicate detector (creates default if None)
            confidence_calculator: Custom confidence calculator (creates default if None)
            schema_validator: Custom schema validator (creates default if None)
        """
        self.integrity = integrity_verifier or IntegrityVerifier()
        self.duplicates = duplicate_detector or DuplicateDetector()
        self.confidence = confidence_calculator or ConfidenceCalculator()
        self.schema = schema_validator or KCRITRValidator()
    
    async def verify_complete(
        self,
        match_data: dict,
        context: dict | None = None
    ) -> ValidationSummary:
        """
        Run complete verification workflow on match data.
        
        Executes all verification layers in sequence:
        1. Transport integrity (if checksum provided)
        2. Schema validation
        3. Semantic validation
        4. Temporal validation
        5. Duplicate detection
        6. Confidence calculation
        
        Args:
            match_data: The match/player data to verify
            context: Optional context including source, checksum, references, etc.
            
        Returns:
            ValidationSummary with complete verification results
        """
        import time
        start_time = time.time()
        
        context = context or {}
        record_id = match_data.get("match_id", match_data.get("player_id", "unknown"))
        
        # Run integrity verification (all layers)
        validation_result = self.integrity.verify_all(match_data, context)
        
        # Run duplicate detection
        duplicate_result = self.duplicates.detect_all_duplicates(match_data)
        
        # Calculate confidence
        confidence = self.confidence.calculate_match_confidence(match_data, context)
        
        # Build schema report
        schema_report = self.schema.validate(match_data)
        
        # Determine overall pass/fail
        passed = (
            validation_result.is_valid and
            not duplicate_result.is_duplicate and
            confidence.tier in (ConfidenceTier.CRITICAL, ConfidenceTier.HIGH, ConfidenceTier.MEDIUM)
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        summary = ValidationSummary(
            record_id=str(record_id),
            passed_all_checks=passed,
            transport_valid=validation_result.is_valid,
            schema_valid=schema_report.is_valid,
            semantic_valid=validation_result.is_valid,
            temporal_valid=validation_result.is_valid,
            crossref_valid=context.get("hltv_data") is not None,
            is_duplicate=duplicate_result.is_duplicate,
            confidence_score=confidence.score,
            confidence_tier=confidence.tier,
            validation_result=validation_result,
            duplicate_result=duplicate_result,
            schema_report=schema_report,
            processing_time_ms=processing_time
        )
        
        return summary
    
    def verify_batch(
        self,
        records: list[dict],
        contexts: list[dict] | None = None
    ) -> list[ValidationSummary]:
        """
        Verify multiple records efficiently.
        
        Args:
            records: List of match/player records to verify
            contexts: Optional list of contexts (one per record)
            
        Returns:
            List of ValidationSummary objects
        """
        contexts = contexts or [{}] * len(records)
        results = []
        
        for record, context in zip(records, contexts):
            # Note: In production, this should be async
            import asyncio
            try:
                result = asyncio.run(self.verify_complete(record, context))
            except RuntimeError:
                # If already in async context, use sync version
                result = self._verify_sync(record, context)
            results.append(result)
        
        return results
    
    def _verify_sync(
        self,
        match_data: dict,
        context: dict | None = None
    ) -> ValidationSummary:
        """Synchronous version of verify_complete for batch processing."""
        import time
        start_time = time.time()
        
        context = context or {}
        record_id = match_data.get("match_id", match_data.get("player_id", "unknown"))
        
        validation_result = self.integrity.verify_all(match_data, context)
        duplicate_result = self.duplicates.detect_all_duplicates(match_data)
        confidence = self.confidence.calculate_match_confidence(match_data, context)
        schema_report = self.schema.validate(match_data)
        
        passed = (
            validation_result.is_valid and
            not duplicate_result.is_duplicate and
            confidence.tier in (ConfidenceTier.CRITICAL, ConfidenceTier.HIGH, ConfidenceTier.MEDIUM)
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return ValidationSummary(
            record_id=str(record_id),
            passed_all_checks=passed,
            transport_valid=validation_result.is_valid,
            schema_valid=schema_report.is_valid,
            semantic_valid=validation_result.is_valid,
            temporal_valid=validation_result.is_valid,
            is_duplicate=duplicate_result.is_duplicate,
            confidence_score=confidence.score,
            confidence_tier=confidence.tier,
            validation_result=validation_result,
            duplicate_result=duplicate_result,
            schema_report=schema_report,
            processing_time_ms=processing_time
        )
