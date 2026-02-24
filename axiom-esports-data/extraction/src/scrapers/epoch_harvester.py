"""
Epoch Harvester — Async VLR.gg extraction across three temporal epochs.

Epoch I:   2020-12-03 → 2022-12-31  (historic, lower confidence)
Epoch II:  2023-01-01 → 2025-12-31  (mature dataset, high confidence)
Epoch III: 2026-01-01 → present      (current, incremental updates)
"""
import argparse
import asyncio
import logging
from datetime import date, datetime
from typing import Optional

import aiohttp

from extraction.src.scrapers.vlr_resilient_client import ResilientVLRClient
from extraction.src.storage.raw_repository import RawRepository
from extraction.src.storage.integrity_checker import IntegrityChecker

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
    """

    def __init__(
        self,
        mode: str = "delta",
        epochs: Optional[list[int]] = None,
        max_concurrent: int = 3,
    ) -> None:
        self.mode = mode
        self.target_epochs = epochs or [1, 2, 3]
        self.max_concurrent = max_concurrent
        self.repo = RawRepository()
        self.checker = IntegrityChecker()

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

        # In delta mode, only fetch matches not yet in extraction_log
        # In full mode, re-scrape entire epoch range
        match_ids = await self._get_target_match_ids(epoch_num, config)
        logger.info("Epoch %d: %d matches to process", epoch_num, len(match_ids))

        for match_id in match_ids:
            url = f"https://www.vlr.gg/{match_id}"
            try:
                response = await client.ethical_fetch(url)
                if response.status == 200:
                    await self.repo.store_raw(
                        raw_html=response.raw_html,
                        checksum=response.checksum,
                        source_url=url,
                        epoch=epoch_num,
                        vlr_match_id=str(match_id),
                        http_status=response.status,
                    )
                    records_processed += 1
            except Exception as exc:
                logger.error("Failed to harvest match %s: %s", match_id, exc)

        logger.info("Epoch %d complete: %d records stored", epoch_num, records_processed)
        return records_processed

    async def _get_target_match_ids(self, epoch_num: int, config: dict) -> list[str]:
        """Return list of match IDs for this epoch (delta or full)."""
        # Stub: in production, queries extraction_log for unprocessed IDs
        # or fetches from VLR match list pages within date range
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
