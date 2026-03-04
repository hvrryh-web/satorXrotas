"""
Integrity Verifier — Multi-layer data integrity checking.

Validates data integrity at multiple levels:
1. Transport integrity (checksums)
2. Schema integrity (field presence/types)
3. Semantic integrity (value ranges, relationships)
4. Temporal integrity (no future dates, reasonable sequences)
5. Cross-reference integrity (HLTV comparison)
"""
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from pipeline.verification.models import (
    CrossReferenceMatch,
    CrossReferenceResult,
    ValidationError,
    ValidationResult,
    ValidationSeverity,
    ValidationWarning,
)
from pipeline.verification.schema_validator import KCRITRValidator

logger = logging.getLogger(__name__)


class IntegrityVerifier:
    """
    Multi-layer integrity verification for esports data pipeline.
    
    Performs comprehensive validation across five integrity layers:
    - Transport: SHA-256 checksums
    - Schema: Field presence and type validation
    - Semantic: Value ranges and logical relationships
    - Temporal: Date validity and sequence
    - Cross-reference: External source comparison
    
    Example:
        >>> verifier = IntegrityVerifier()
        >>> 
        >>> # Transport check
        >>> is_valid = verifier.verify_transport(content, expected_checksum)
        >>> 
        >>> # Semantic validation
        >>> result = verifier.verify_semantic(player_stats)
        >>> 
        >>> # Full verification
        >>> result = verifier.verify_all(match_data, context)
    """
    
    # Reasonable date bounds for esports data
    MIN_DATE = datetime(2015, 1, 1)  # Early esports
    MAX_FUTURE_DAYS = 7  # Allow some future dates for scheduled matches
    
    # Semantic tolerance thresholds
    MAX_ADR = 500  # Maximum reasonable ADR
    MAX_KAST = 100  # Maximum KAST percentage
    MAX_HS_PCT = 100  # Maximum headshot percentage
    MAX_ROUNDS = 100  # Maximum rounds in a match
    MAX_KILLS_PER_ROUND = 5  # Can't kill more than 5 enemies per round
    
    # Cross-reference tolerance (5% variance allowed)
    CROSSREF_TOLERANCE_PCT = 5.0
    
    def __init__(self, schema_validator: Optional[KCRITRValidator] = None) -> None:
        """
        Initialize the integrity verifier.
        
        Args:
            schema_validator: Custom schema validator (uses default if None)
        """
        self.schema_validator = schema_validator or KCRITRValidator()
        self._validation_cache: dict[str, ValidationResult] = {}
        logger.debug("IntegrityVerifier initialized")
    
    def verify_transport(self, content: str | bytes, expected_checksum: str) -> bool:
        """
        Verify SHA-256 checksum of content.
        
        Args:
            content: String or bytes to verify
            expected_checksum: Expected SHA-256 hex digest
            
        Returns:
            True if checksum matches, False otherwise
            
        Example:
            >>> verifier = IntegrityVerifier()
            >>> content = "match_data_json"
            >>> checksum = "abc123..."
            >>> if not verifier.verify_transport(content, checksum):
            ...     raise ValueError("Transport integrity check failed")
        """
        if isinstance(content, str):
            content = content.encode("utf-8")
        
        actual_checksum = hashlib.sha256(content).hexdigest()
        matches = actual_checksum == expected_checksum
        
        if not matches:
            logger.error(
                "Transport integrity failed: expected %s, got %s",
                expected_checksum[:12],
                actual_checksum[:12]
            )
        else:
            logger.debug("Transport integrity verified: %s", expected_checksum[:12])
        
        return matches
    
    def verify_schema(self, data: dict, schema_name: str = "kcritr") -> ValidationResult:
        """
        Verify data against JSON schema.
        
        Args:
            data: Dictionary to validate
            schema_name: Schema to validate against (default: kcritr)
            
        Returns:
            ValidationResult with detailed validation info
        """
        result = ValidationResult(is_valid=True)
        
        if schema_name.lower() == "kcritr":
            report = self.schema_validator.validate(data)
            
            if not report.is_valid:
                result.is_valid = False
                
                # Add missing field errors
                for field in report.missing_fields:
                    result.add_error(
                        field=field,
                        code="MISSING_REQUIRED_FIELD",
                        message=f"Required field '{field}' is missing",
                        severity=ValidationSeverity.ERROR
                    )
                
                # Add type mismatch errors
                for error in report.type_mismatches:
                    result.errors.append(error)
                
                # Add range errors
                for error in report.invalid_fields:
                    result.errors.append(error)
            
            # Add warnings for extra fields
            if report.extra_fields:
                for field in report.extra_fields:
                    result.add_warning(
                        field=field,
                        code="EXTRA_FIELD",
                        message=f"Unexpected field '{field}' present in record"
                    )
            
            # Set confidence based on completeness
            result.confidence = report.completeness_pct
        else:
            result.add_error(
                field="schema",
                code="UNKNOWN_SCHEMA",
                message=f"Unknown schema: {schema_name}",
                severity=ValidationSeverity.ERROR
            )
        
        return result
    
    def verify_semantic(self, player_stats: dict[str, Any]) -> ValidationResult:
        """
        Check value ranges and logical relationships.
        
        Validates:
        - kills >= 0, deaths >= 0
        - hs_pct between 0-100
        - adr reasonable (0-500)
        - kast_pct between 0-100
        - kills + assists <= rounds * 5 (can't kill more than 5 enemies per round)
        
        Args:
            player_stats: Player statistics dictionary
            
        Returns:
            ValidationResult with semantic validation details
        """
        result = ValidationResult(is_valid=True)
        
        # Basic non-negative checks
        for field in ["kills", "deaths", "assists"]:
            value = player_stats.get(field)
            if value is not None:
                try:
                    if float(value) < 0:
                        result.add_error(
                            field=field,
                            code="NEGATIVE_VALUE",
                            message=f"{field} must be non-negative",
                            value=value,
                            expected=">= 0"
                        )
                except (TypeError, ValueError):
                    result.add_error(
                        field=field,
                        code="INVALID_NUMERIC",
                        message=f"{field} must be numeric",
                        value=value
                    )
        
        # Percentage field checks (0-100)
        pct_fields = {
            "hs_pct": "Headshot percentage",
            "kast_pct": "KAST percentage",
        }
        for field, description in pct_fields.items():
            value = player_stats.get(field)
            if value is not None:
                try:
                    pct = float(value)
                    if pct < 0 or pct > self.MAX_KAST:
                        result.add_error(
                            field=field,
                            code="PERCENTAGE_OUT_OF_RANGE",
                            message=f"{description} must be between 0 and {self.MAX_KAST}",
                            value=pct,
                            expected=f"0-{self.MAX_KAST}"
                        )
                except (TypeError, ValueError):
                    result.add_error(
                        field=field,
                        code="INVALID_PERCENTAGE",
                        message=f"{description} must be a valid number",
                        value=value
                    )
        
        # ADR check
        adr = player_stats.get("adr")
        if adr is not None:
            try:
                adr_val = float(adr)
                if adr_val < 0 or adr_val > self.MAX_ADR:
                    result.add_error(
                        field="adr",
                        code="ADR_OUT_OF_RANGE",
                        message=f"ADR must be between 0 and {self.MAX_ADR}",
                        value=adr_val,
                        expected=f"0-{self.MAX_ADR}"
                    )
            except (TypeError, ValueError):
                result.add_error(
                    field="adr",
                    code="INVALID_ADR",
                    message="ADR must be a valid number",
                    value=adr
                )
        
        # ACS check
        acs = player_stats.get("acs")
        if acs is not None:
            try:
                acs_val = float(acs)
                if acs_val < 0 or acs_val > 800:
                    result.add_error(
                        field="acs",
                        code="ACS_OUT_OF_RANGE",
                        message="ACS must be between 0 and 800",
                        value=acs_val,
                        expected="0-800"
                    )
            except (TypeError, ValueError):
                result.add_error(
                    field="acs",
                    code="INVALID_ACS",
                    message="ACS must be a valid number",
                    value=acs
                )
        
        # Logical relationship: kills + assists <= rounds * 5
        kills = player_stats.get("kills")
        assists = player_stats.get("assists")
        rounds = player_stats.get("rounds_played")
        
        if all(v is not None for v in [kills, assists, rounds]):
            try:
                total_killing_participation = float(kills) + float(assists)
                max_possible = float(rounds) * self.MAX_KILLS_PER_ROUND
                
                if total_killing_participation > max_possible:
                    result.add_error(
                        field="kills+assists",
                        code="IMPOSSIBLE_KILL_COUNT",
                        message=f"kills ({kills}) + assists ({assists}) exceeds maximum possible "
                                f"for {rounds} rounds (max: {max_possible})",
                        value=total_killing_participation,
                        expected=f"<= {max_possible}"
                    )
            except (TypeError, ValueError):
                result.add_warning(
                    field="kills+assists",
                    code="CANNOT_VALIDATE_LOGIC",
                    message="Cannot validate kill logic due to non-numeric values"
                )
        
        # K/D ratio check (should be reasonable, not infinity)
        if kills is not None and deaths is not None:
            try:
                k_val, d_val = float(kills), float(deaths)
                if d_val == 0 and k_val > 50:
                    result.add_warning(
                        field="kills/deaths",
                        code="SUSPICIOUS_KD",
                        message=f"Suspicious K/D: {k_val} kills with 0 deaths",
                        value=f"{k_val}/0"
                    )
            except (TypeError, ValueError):
                pass
        
        # Calculate confidence based on number of checks passed
        total_checks = 5  # Basic count of semantic checks
        error_count = len([e for e in result.errors if e.severity == ValidationSeverity.ERROR])
        result.confidence = max(0, 100 - (error_count * 20))
        
        return result
    
    def verify_temporal(
        self,
        match_date: str | datetime,
        stats: Optional[dict] = None
    ) -> ValidationResult:
        """
        Check dates are reasonable (not future, not too old).
        
        Args:
            match_date: Match date (ISO string or datetime)
            stats: Optional player stats for additional temporal checks
            
        Returns:
            ValidationResult with temporal validation details
        """
        result = ValidationResult(is_valid=True)
        now = datetime.utcnow()
        
        # Parse date if string
        if isinstance(match_date, str):
            try:
                # Try common ISO formats
                for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"]:
                    try:
                        parsed_date = datetime.strptime(match_date, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    raise ValueError(f"Cannot parse date: {match_date}")
            except ValueError as e:
                result.add_error(
                    field="match_date",
                    code="INVALID_DATE_FORMAT",
                    message=f"Cannot parse match_date: {e}",
                    value=match_date
                )
                return result
        else:
            parsed_date = match_date
        
        # Check not too old
        if parsed_date < self.MIN_DATE:
            result.add_error(
                field="match_date",
                code="DATE_TOO_OLD",
                message=f"Match date {parsed_date} is before minimum allowed date {self.MIN_DATE}",
                value=parsed_date.isoformat(),
                expected=f">= {self.MIN_DATE.isoformat()}"
            )
        
        # Check not too far in future
        max_future = now + timedelta(days=self.MAX_FUTURE_DAYS)
        if parsed_date > max_future:
            result.add_error(
                field="match_date",
                code="DATE_IN_FUTURE",
                message=f"Match date {parsed_date} is too far in the future",
                value=parsed_date.isoformat(),
                expected=f"<= {max_future.isoformat()}"
            )
        
        # Check for recently played matches (warning if very recent)
        if parsed_date > now:
            result.add_warning(
                field="match_date",
                code="FUTURE_DATE",
                message=f"Match date {parsed_date} is in the future (may be scheduled)",
                value=parsed_date.isoformat()
            )
        
        # Temporal consistency with stats if provided
        if stats:
            # Could add checks for stat dates vs match date here
            pass
        
        # Calculate confidence
        if result.errors:
            result.confidence = 0
        elif result.warnings:
            result.confidence = 75
        else:
            result.confidence = 100
        
        return result
    
    def verify_crossref(
        self,
        player_stats: dict[str, Any],
        hltv_data: Optional[dict[str, Any]] = None
    ) -> CrossReferenceResult:
        """
        Compare against HLTV data if available.
        
        Args:
            player_stats: Our player statistics
            hltv_data: Optional HLTV reference data
            
        Returns:
            CrossReferenceResult with comparison details
        """
        result = CrossReferenceResult(is_valid=True)
        
        if hltv_data is None:
            # No reference data available - valid but low confidence
            result.confidence = 50
            result.missing_in_reference = ["all_fields"]
            return result
        
        # Fields to compare
        comparable_fields = {
            "kills": "Kills",
            "deaths": "Deaths",
            "assists": "Assists",
            "adr": "ADR",
            "kast_pct": "KAST%",
            "hs_pct": "HS%",
        }
        
        matches = 0
        mismatches = 0
        
        for field, description in comparable_fields.items():
            our_val = player_stats.get(field)
            their_val = hltv_data.get(field)
            
            if our_val is None or their_val is None:
                result.missing_in_reference.append(field)
                continue
            
            try:
                our_num = float(our_val)
                their_num = float(their_val)
                
                # Calculate difference
                if their_num == 0:
                    diff_pct = abs(our_num - their_num) * 100
                else:
                    diff_pct = (abs(our_num - their_num) / their_num) * 100
                
                within_tolerance = diff_pct <= self.CROSSREF_TOLERANCE_PCT
                
                match = CrossReferenceMatch(
                    source="hltv",
                    field=field,
                    our_value=our_num,
                    their_value=their_num,
                    difference=diff_pct,
                    within_tolerance=within_tolerance,
                    tolerance_pct=self.CROSSREF_TOLERANCE_PCT
                )
                
                if within_tolerance:
                    result.matches.append(match)
                    matches += 1
                else:
                    result.mismatches.append(match)
                    mismatches += 1
                    
            except (TypeError, ValueError):
                result.missing_in_reference.append(field)
        
        # Calculate confidence based on match ratio
        total_compared = matches + mismatches
        if total_compared > 0:
            result.confidence = (matches / total_compared) * 100
        else:
            result.confidence = 0
        
        result.is_valid = len(result.mismatches) == 0
        
        return result
    
    def verify_all(
        self,
        data: dict[str, Any],
        context: Optional[dict] = None
    ) -> ValidationResult:
        """
        Run all integrity checks on data.
        
        Args:
            data: Complete match/player data
            context: Optional context with checksum, hltv_data, etc.
            
        Returns:
            Combined ValidationResult from all checks
        """
        context = context or {}
        result = ValidationResult(is_valid=True)
        
        # 1. Transport integrity
        if "content" in context and "expected_checksum" in context:
            if not self.verify_transport(context["content"], context["expected_checksum"]):
                result.add_error(
                    field="checksum",
                    code="TRANSPORT_INTEGRITY_FAILED",
                    message="SHA-256 checksum verification failed",
                    severity=ValidationSeverity.ERROR
                )
        
        # 2. Schema validation
        schema_result = self.verify_schema(data)
        result = result.merge(schema_result)
        
        # 3. Semantic validation
        if "player_stats" in data or any(k in data for k in ["kills", "deaths", "acs"]):
            semantic_result = self.verify_semantic(data)
            result = result.merge(semantic_result)
        
        # 4. Temporal validation
        if "match_date" in data:
            temporal_result = self.verify_temporal(data["match_date"], data)
            result = result.merge(temporal_result)
        
        # 5. Cross-reference validation
        if "hltv_data" in context:
            crossref_result = self.verify_crossref(data, context["hltv_data"])
            if not crossref_result.is_valid:
                for mismatch in crossref_result.mismatches:
                    result.add_warning(
                        field=f"crossref.{mismatch.field}",
                        code="CROSSREF_MISMATCH",
                        message=f"HLTV mismatch on {mismatch.field}: "
                                f"ours={mismatch.our_value}, theirs={mismatch.their_value} "
                                f"(diff: {mismatch.difference:.1f}%)",
                        value=mismatch.our_value
                    )
        
        return result
