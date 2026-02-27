"""Tests for EpochHarvester epoch boundary enforcement."""
import asyncio
from datetime import date

import pytest

from extraction.src.scrapers.epoch_harvester import EpochHarvester, EPOCHS


class TestEpochHarvesterBoundaries:
    def test_epochs_defined(self):
        """All three epochs must be registered with start/end/confidence_floor."""
        for num in (1, 2, 3):
            assert num in EPOCHS
            cfg = EPOCHS[num]
            assert "start" in cfg and "end" in cfg and "confidence_floor" in cfg

    def test_epoch_date_order(self):
        """Each epoch's start must be before its end."""
        for num, cfg in EPOCHS.items():
            assert cfg["start"] <= cfg["end"], (
                f"Epoch {num}: start {cfg['start']} is after end {cfg['end']}"
            )

    def test_epoch_1_confidence_floor_lower_than_epoch_2(self):
        """Historic epoch has lower confidence than mature dataset epoch."""
        assert EPOCHS[1]["confidence_floor"] < EPOCHS[2]["confidence_floor"]

    def test_epoch_2_ends_before_epoch_3_starts(self):
        """Epoch II and Epoch III must not overlap."""
        assert EPOCHS[2]["end"] < EPOCHS[3]["start"]

    def test_default_mode_is_delta(self):
        harvester = EpochHarvester()
        assert harvester.mode == "delta"

    def test_target_epochs_default_all(self):
        harvester = EpochHarvester()
        assert set(harvester.target_epochs) == {1, 2, 3}

    def test_custom_epoch_list(self):
        harvester = EpochHarvester(epochs=[2])
        assert harvester.target_epochs == [2]

    @pytest.mark.asyncio
    async def test_get_target_match_ids_no_db_returns_empty(self):
        """Without DATABASE_URL configured, should return empty list (no error)."""
        import os
        os.environ.pop("DATABASE_URL", None)
        harvester = EpochHarvester(mode="delta")
        result = await harvester._get_target_match_ids(1, EPOCHS[1])
        assert result == []

    @pytest.mark.asyncio
    async def test_harvest_epoch_handles_empty_match_list(self):
        """When no match IDs are returned, harvest should complete with 0 records."""
        import aiohttp
        from extraction.src.scrapers.vlr_resilient_client import ResilientVLRClient

        async with aiohttp.ClientSession() as session:
            client = ResilientVLRClient(session=session)
            harvester = EpochHarvester(mode="delta")
            # _get_target_match_ids returns [] without DB; harvest should return 0
            count = await harvester.harvest_epoch(1, client)
        assert count == 0
