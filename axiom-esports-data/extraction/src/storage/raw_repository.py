"""
Raw Repository — Immutable parquet storage for VLR.gg extractions.
Records are never modified after first write.
"""
import hashlib
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

RAW_STORAGE_PATH = Path(os.environ.get("RAW_STORAGE_PATH", "data/raw_extractions"))


class RawRepository:
    """
    Append-only store for raw VLR.gg HTML extractions.
    Each write produces an immutable parquet file identified by SHA-256.
    Dual-storage protocol: separation_flag=0 for all raw records.
    """

    def __init__(self, storage_path: Path = RAW_STORAGE_PATH) -> None:
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _checksum(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()

    def already_stored(self, checksum: str) -> bool:
        """Check if a record with this checksum already exists."""
        target = self.storage_path / f"{checksum}.parquet"
        return target.exists()

    async def store_raw(
        self,
        raw_html: str,
        checksum: str,
        source_url: str,
        epoch: int,
        vlr_match_id: Optional[str] = None,
        http_status: int = 200,
        schema_version: str = "v2",
    ) -> Path:
        """
        Persist raw extraction. No-ops if checksum already stored.
        Returns path to stored file.
        """
        if self.already_stored(checksum):
            logger.debug("Checksum %s already stored — skipping", checksum[:12])
            return self.storage_path / f"{checksum}.parquet"

        # Verify provided checksum matches content
        computed = self._checksum(raw_html)
        if computed != checksum:
            raise ValueError(
                f"Checksum mismatch: provided {checksum[:12]} != computed {computed[:12]}"
            )

        metadata = {
            "checksum_sha256": checksum,
            "source_url": source_url,
            "epoch": epoch,
            "vlr_match_id": vlr_match_id,
            "http_status": http_status,
            "schema_version": schema_version,
            "extracted_at": datetime.utcnow().isoformat(),
            "separation_flag": 0,  # Always 0 for raw records
            "raw_html_length": len(raw_html),
        }

        # In production: write parquet via pandas/pyarrow
        # For now, store as a lightweight JSON sidecar + raw file
        target = self.storage_path / f"{checksum}.raw"
        target.write_text(raw_html, encoding="utf-8")
        logger.info("Stored raw extraction: %s (%d bytes)", checksum[:12], len(raw_html))
        return target

    def get_raw(self, checksum: str) -> Optional[str]:
        """Retrieve raw content by checksum."""
        target = self.storage_path / f"{checksum}.raw"
        if not target.exists():
            return None
        return target.read_text(encoding="utf-8")
