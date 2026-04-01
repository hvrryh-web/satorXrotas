"""
Reconstruction Repository — Separated store for inferred/reconstructed data points.
Always references a parent raw extraction. separation_flag=1 enforced.
"""
import logging
from dataclasses import dataclass
from typing import Optional
from uuid import UUID, uuid4

from extraction.src.bridge.extraction_bridge import KCRITRRecord

logger = logging.getLogger(__name__)


@dataclass
class ReconstructedRecord:
    player_id: UUID
    match_id: str
    map_name: Optional[str]
    partner_raw_checksum: str  # SHA-256 of the parent raw record
    reconstruction_method: str  # acs_differential, role_inference, etc.
    confidence_tier: float
    reconstructed_fields: list[str]
    reconstructed_values: dict
    reconstruction_notes: Optional[str] = None
    separation_flag: int = 1  # Always 1 — enforced, not optional


class ReconstructionRepo:
    """
    Stores reconstructed records separately from raw extractions.
    Implements the dual-storage protocol: raw records (flag=0) and
    reconstructed records (flag=1) are never mixed.
    """

    def __init__(self) -> None:
        self._records: list[ReconstructedRecord] = []

    def store(self, record: ReconstructedRecord) -> None:
        if record.separation_flag != 1:
            raise ValueError(
                "separation_flag must be 1 for all reconstructed records. "
                f"Got {record.separation_flag} for match {record.match_id}."
            )
        if not record.partner_raw_checksum:
            raise ValueError(
                "Reconstructed records must reference a partner raw extraction. "
                f"match_id={record.match_id} has no partner_raw_checksum."
            )
        self._records.append(record)
        logger.debug(
            "Stored reconstruction for player %s, match %s (method=%s)",
            record.player_id, record.match_id, record.reconstruction_method,
        )

    def get_by_match(self, match_id: str) -> list[ReconstructedRecord]:
        return [r for r in self._records if r.match_id == match_id]

    def get_by_player(self, player_id: UUID) -> list[ReconstructedRecord]:
        return [r for r in self._records if r.player_id == player_id]


class KCRITRRepository:
    """
    Stores KCRITRRecord instances keyed by (player_id, match_id).
    Enforces separation_flag=1 for all reconstructed records.
    """

    def __init__(self) -> None:
        self._records: list[KCRITRRecord] = []

    def store_reconstruction(self, record: KCRITRRecord) -> None:
        """Store a reconstructed KCRITR record (separation_flag must be 1)."""
        if record.separation_flag != 1:
            raise ValueError(
                "separation_flag must be 1 for reconstructed records. "
                f"Got {record.separation_flag} for match {record.match_id}."
            )
        if not record.partner_datapoint_ref:
            raise ValueError(
                "Reconstructed KCRITRRecords must set partner_datapoint_ref. "
                f"match_id={record.match_id} is missing it."
            )
        self._records.append(record)
        logger.debug(
            "Stored KCRITR reconstruction for player %s, match %s",
            record.player_id, record.match_id,
        )

    def get_reconstruction(self, player_id: UUID, match_id: str) -> Optional[KCRITRRecord]:
        """Retrieve a single reconstructed record by player_id and match_id."""
        for r in self._records:
            if r.player_id == player_id and r.match_id == match_id:
                return r
        return None
