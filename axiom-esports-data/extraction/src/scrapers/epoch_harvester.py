"""
Epoch Harvester — Async VLR.gg extraction across three temporal epochs.

Epoch I:   2020-12-03 → 2022-12-31  (historic, lower confidence)
Epoch II:  2023-01-01 → 2025-12-31  (mature dataset, high confidence)
Epoch III: 2026-01-01 → present      (current, incremental updates)

Coordinated Harvest Protocol
-----------------------------
The harvester operates under a shared contract defined in
``config/harvest_protocol.json``.  Before fetching any URL it consults
``KnownRecordRegistry.should_skip(match_id)`` so that:

  - Fully-processed matches are never re-scraped.
  - Excluded matches (corrupted, schema-conflict, manual) are bypassed.
  - Content-unchanged matches (same checksum) are silently skipped.

This makes the harvester and the registry a **conjoined task**: the
registry pre-gates every fetch decision, and the harvester reports
outcomes back to the registry via ``mark_complete`` / ``mark_excluded``.
"""
import argparse
import asyncio
import logging
import os
from datetime import date, datetime
from typing import Optional

import aiohttp

from extraction.src.scrapers.vlr_resilient_client import ResilientVLRClient
from extraction.src.storage.raw_repository import RawRepository
from extraction.src.storage.integrity_checker import IntegrityChecker
from extraction.src.storage.known_record_registry import KnownRecordRegistry

logger = logging.getLogger(__name__)

EPOCHS = {
    1: {"start": date(2020, 12, 3), "end": date(2022, 12, 31), "confidence_floor": 50.0},
    2: {"start": date(2023, 1, 1),  "end": date(2025, 12, 31), "confidence_floor": 75.0},
    3: {"start": date(2026, 1, 1),  "end": date.today(),        "confidence_floor": 100.0},
}

VLR_MATCH_LIST_URL = "https://www.vlr.gg/matches/results"


class EpochHarvester:
    """
    Coordinates extraction across three epochs using async workers.
    Supports full and delta modes.

    Registry integration
    --------------------
    ``KnownRecordRegistry`` is consulted at the top of every match-level
    loop iteration via ``registry.should_skip(match_id)``.  This prevents
    any network I/O for records already in the database.

    Outcomes are reported back to the registry:
      - Successful store  → ``registry.mark_complete(match_id, checksum)``
      - Parse/fetch error → ``registry.mark_excluded(match_id, reason)``

    The registry in turn writes these outcomes to the DB extraction_log so
    that the next run's delta query returns an accurate pending set.
    """

    def __init__(
        self,
        mode: str = "delta",
        epochs: Optional[list[int]] = None,
        max_concurrent: int = 3,
        registry: Optional[KnownRecordRegistry] = None,
    ) -> None:
        self.mode = mode
        self.target_epochs = epochs or [1, 2, 3]
        self.max_concurrent = max_concurrent
        self.repo = RawRepository()
        self.checker = IntegrityChecker()
        # Registry is the single source of truth for what's already stored.
        # Injected for testability; defaults to a fresh instance using DATABASE_URL.
        self.registry = registry if registry is not None else KnownRecordRegistry()

    async def harvest_epoch(
        self,
        epoch_num: int,
        client: ResilientVLRClient,
    ) -> int:
        """Harvest a single epoch. Returns count of records processed."""
        config = EPOCHS[epoch_num]
        logger.info(
            "Starting Epoch %d extraction: %s → %s (mode=%s)",
            epoch_num, config["start"], config["end"], self.mode
        )
        records_processed = 0
        records_skipped = 0

        match_ids = await self._get_target_match_ids(epoch_num, config)
        logger.info("Epoch %d: %d matches to process", epoch_num, len(match_ids))

        for match_id in match_ids:
            # ── Registry pre-check: skip known-complete or excluded matches ──
            if self.registry.should_skip(match_id):
                records_skipped += 1
                continue

            url = f"https://www.vlr.gg/{match_id}"
            try:
                response = await client.ethical_fetch(url)

                # ── Checksum unchanged: skip writing, registry already current ──
                if self.registry.should_skip_checksum(match_id, response.checksum):
                    records_skipped += 1
                    continue

                if response.status == 200:
                    await self.repo.store_raw(
                        raw_html=response.raw_html,
                        checksum=response.checksum,
                        source_url=url,
                        epoch=epoch_num,
                        vlr_match_id=str(match_id),
                        http_status=response.status,
                    )
                    # Report successful write back to registry
                    self.registry.mark_complete(match_id, checksum=response.checksum)
                    records_processed += 1
                else:
                    logger.warning(
                        "Non-200 response (%d) for match %s — not stored",
                        response.status, match_id,
                    )

            except Exception as exc:
                logger.error("Failed to harvest match %s: %s", match_id, exc)
                # Repeated failures result in the harvester excluding the match
                # so it doesn't block future delta runs.  The reason code is
                # kept generic here; schema-drift exclusions are raised by the
                # parser and use SCHEMA_CONFLICT specifically.
                self.registry.mark_excluded(
                    match_id,
                    reason_code="MANUAL_EXCLUDE",
                    notes=f"Harvest exception: {exc!s:.200}",
                    excluded_by="epoch_harvester",
                )

        logger.info(
            "Epoch %d complete: %d stored, %d skipped (already known)",
            epoch_num, records_processed, records_skipped,
        )
        return records_processed

    async def _get_target_match_ids(self, epoch_num: int, config: dict) -> list[str]:
        """Return list of match IDs for this epoch (delta or full).

        Delta mode queries ``extraction_log`` for match-type rows whose
        ``first_extracted_at`` falls within the epoch date range and have
        not yet been fully processed (``is_complete = FALSE``).

        Full mode is a superset: it returns all IDs in the date range,
        regardless of completion status, allowing a complete re-scrape.

        When no database is available (e.g. during unit tests) both modes
        return an empty list — callers should handle this gracefully.
        """
        start: date = config["start"]
        end: date = config["end"]

        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            logger.warning(
                "DATABASE_URL not set — _get_target_match_ids returns [] for epoch %d",
                epoch_num,
            )
            return []

        try:
            import asyncpg  # type: ignore

            conn = await asyncpg.connect(db_url)
            try:
                if self.mode == "delta":
                    rows = await conn.fetch(
                        """
                        SELECT entity_id
                        FROM extraction_log
                        WHERE source = 'vlr_gg'
                          AND entity_type = 'match'
                          AND is_complete = FALSE
                          AND first_extracted_at >= $1
                          AND first_extracted_at <  $2
                        ORDER BY first_extracted_at ASC
                        """,
                        datetime.combine(start, datetime.min.time()),
                        datetime.combine(end,   datetime.max.time()),
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT entity_id
                        FROM extraction_log
                        WHERE source = 'vlr_gg'
                          AND entity_type = 'match'
                          AND first_extracted_at >= $1
                          AND first_extracted_at <  $2
                        ORDER BY first_extracted_at ASC
                        """,
                        datetime.combine(start, datetime.min.time()),
                        datetime.combine(end,   datetime.max.time()),
                    )
                return [row["entity_id"] for row in rows]
            finally:
                await conn.close()

        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Failed to fetch match IDs for epoch %d from DB: %s", epoch_num, exc
            )
            return []

    async def run(self) -> dict[int, int]:
        """Run harvest across all target epochs concurrently."""
        async with aiohttp.ClientSession() as session:
            client = ResilientVLRClient(
                rate_limit_seconds=2.0,
                max_concurrent=self.max_concurrent,
                session=session,
            )
            tasks = [
                self.harvest_epoch(epoch_num, client)
                for epoch_num in self.target_epochs
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        totals = {}
        for epoch_num, result in zip(self.target_epochs, results):
            if isinstance(result, Exception):
                logger.error("Epoch %d failed: %s", epoch_num, result)
                totals[epoch_num] = 0
            else:
                totals[epoch_num] = result
        return totals


def main() -> None:
    parser = argparse.ArgumentParser(description="Axiom Epoch Harvester")
    parser.add_argument("--mode", choices=["full", "delta"], default="delta")
    parser.add_argument("--epochs", nargs="+", type=int, default=[1, 2, 3])
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    harvester = EpochHarvester(mode=args.mode, epochs=args.epochs)
    totals = asyncio.run(harvester.run())
    for epoch_num, count in totals.items():
        logger.info("Epoch %d: %d records harvested", epoch_num, count)


if __name__ == "__main__":
    main()
