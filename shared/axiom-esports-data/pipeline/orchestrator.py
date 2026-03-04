"""
Pipeline Orchestrator — Main Entry Point
========================================

Coordinates the full data pipeline flow:
    Discover → Fetch → Verify → Parse → Transform → CrossRef → Store → Index

Features:
    - Stage-by-stage resumption (restart from any stage)
    - Checkpointing (save progress every N records)
    - Batch processing with configurable size
    - Parallel workers with rate limiting
    - Dead letter queue for failed records
    - Prometheus-compatible metrics

CLI Usage:
    python -m pipeline.orchestrator \\
        --mode=delta|full|backfill \\
        --epochs=1,2,3 \\
        --stage=all|discover|fetch|parse|transform|store \\
        --batch-size=100 \\
        --max-workers=3 \\
        --checkpoint-interval=50

Example:
    # Run delta update for current epoch
    python -m pipeline.orchestrator --mode=delta --epochs=3
    
    # Full reprocessing from fetch stage
    python -m pipeline.orchestrator --mode=full --stage=fetch --max-workers=5
"""

import argparse
import asyncio
import logging
import sys
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from extraction.src.scrapers.epoch_harvester import EpochHarvester, EPOCHS
from extraction.src.scrapers.vlr_resilient_client import ResilientVLRClient
from extraction.src.scrapers.validation_crossref import ValidationCrossRef
from extraction.src.storage.known_record_registry import KnownRecordRegistry
from extraction.src.storage.raw_repository import RawRepository
from extraction.src.storage.integrity_checker import IntegrityChecker
from extraction.src.parsers.match_parser import MatchParser, RawMatchData
from extraction.src.bridge.extraction_bridge import ExtractionBridge, KCRITRRecord
from pipeline.config import PipelineConfig, get_config
from pipeline.stage_tracker import StageTracker
from pipeline.metrics import PipelineMetrics
from pipeline.dead_letter import DeadLetterQueue

logger = logging.getLogger(__name__)


class PipelineMode(Enum):
    """Pipeline operation modes."""
    DELTA = "delta"       # Process only new/changed records
    FULL = "full"         # Process all records
    BACKFILL = "backfill" # Fill gaps in historical data


class PipelineStage(Enum):
    """Pipeline processing stages."""
    ALL = "all"
    DISCOVER = "discover"
    FETCH = "fetch"
    VERIFY = "verify"
    PARSE = "parse"
    TRANSFORM = "transform"
    CROSSREF = "crossref"
    STORE = "store"
    INDEX = "index"


@dataclass
class PipelineResult:
    """Result of a pipeline run."""
    mode: str
    epochs: list[int]
    records_discovered: int = 0
    records_fetched: int = 0
    records_verified: int = 0
    records_parsed: int = 0
    records_transformed: int = 0
    records_stored: int = 0
    records_indexed: int = 0
    records_failed: int = 0
    duration_seconds: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "epochs": self.epochs,
            "records_discovered": self.records_discovered,
            "records_fetched": self.records_fetched,
            "records_verified": self.records_verified,
            "records_parsed": self.records_parsed,
            "records_transformed": self.records_transformed,
            "records_stored": self.records_stored,
            "records_indexed": self.records_indexed,
            "records_failed": self.records_failed,
            "duration_seconds": round(self.duration_seconds, 2),
        }


class PipelineOrchestrator:
    """Main pipeline orchestrator coordinating all extraction stages.
    
    The orchestrator manages the flow of data through the pipeline,
    handling stage-by-stage resumption, checkpointing, parallel
    processing, and error handling.
    
    Example:
        orchestrator = PipelineOrchestrator()
        
        # Run full pipeline in delta mode
        result = await orchestrator.run(
            mode=PipelineMode.DELTA,
            epochs=[1, 2, 3],
            start_stage=PipelineStage.FETCH
        )
        
        print(f"Processed {result.records_stored} records")
    """
    
    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        registry: Optional[KnownRecordRegistry] = None,
        tracker: Optional[StageTracker] = None,
        metrics: Optional[PipelineMetrics] = None,
        dlq: Optional[DeadLetterQueue] = None,
    ) -> None:
        """Initialize the pipeline orchestrator.
        
        Args:
            config: Pipeline configuration
            registry: Known record registry for deduplication
            tracker: Stage tracker for resumption
            metrics: Metrics collector
            dlq: Dead letter queue for failed records
        """
        self.config = config or get_config()
        self.registry = registry or KnownRecordRegistry()
        self.tracker = tracker or StageTracker()
        self.metrics = metrics or PipelineMetrics(self.config.metrics_path)
        self.dlq = dlq or DeadLetterQueue(self.config.dead_letter_path)
        
        # Initialize components
        self.raw_repo = RawRepository(self.config.raw_storage_path)
        self.integrity_checker = IntegrityChecker(self.config.raw_storage_path)
        self.match_parser = MatchParser()
        self.extraction_bridge = ExtractionBridge()
        self.crossref = ValidationCrossRef(self.config.database_url)
        
        # Processing state
        self._stop_requested = False
        self._checkpoint_counter = 0
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Configure logging for the pipeline."""
        level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=level,
            format=self.config.log_format,
        )
    
    async def run(
        self,
        mode: PipelineMode = PipelineMode.DELTA,
        epochs: Optional[list[int]] = None,
        start_stage: PipelineStage = PipelineStage.ALL,
        match_ids: Optional[list[str]] = None,
    ) -> PipelineResult:
        """Run the complete pipeline.
        
        Args:
            mode: Pipeline operation mode
            epochs: Epochs to process (defaults to config)
            start_stage: Stage to start from (ALL runs all stages)
            match_ids: Optional specific match IDs to process
            
        Returns:
            PipelineResult with processing statistics
        """
        import time
        start_time = time.perf_counter()
        
        target_epochs = epochs or self.config.epochs
        result = PipelineResult(
            mode=mode.value,
            epochs=target_epochs,
        )
        
        logger.info(
            "Starting pipeline: mode=%s, epochs=%s, start_stage=%s",
            mode.value, target_epochs, start_stage.value
        )
        
        # Phase 1: Discovery
        if start_stage in (PipelineStage.ALL, PipelineStage.DISCOVER):
            discovered = await self._discover_matches(mode, target_epochs, match_ids)
            result.records_discovered = len(discovered)
            logger.info("Discovered %d matches to process", len(discovered))
        else:
            # Load from tracker if not discovering
            discovered = self.tracker.list_incomplete() or []
            logger.info("Resuming with %d incomplete matches", len(discovered))
        
        if not discovered:
            logger.info("No matches to process")
            return result
        
        # Phase 2-8: Process in batches
        batches = self._create_batches(discovered, self.config.batch_size)
        logger.info("Processing %d batches", len(batches))
        
        for batch_num, batch in enumerate(batches, 1):
            if self._stop_requested:
                logger.warning("Stop requested - halting pipeline")
                break
            
            logger.debug("Processing batch %d/%d (%d matches)",
                        batch_num, len(batches), len(batch))
            
            batch_results = await self._process_batch(
                batch, mode, start_stage
            )
            
            result.records_fetched += batch_results.get("fetched", 0)
            result.records_verified += batch_results.get("verified", 0)
            result.records_parsed += batch_results.get("parsed", 0)
            result.records_transformed += batch_results.get("transformed", 0)
            result.records_stored += batch_results.get("stored", 0)
            result.records_indexed += batch_results.get("indexed", 0)
            result.records_failed += batch_results.get("failed", 0)
            
            # Checkpoint
            self._checkpoint_counter += len(batch)
            if self._checkpoint_counter >= self.config.checkpoint_interval:
                await self._save_checkpoint()
                self._checkpoint_counter = 0
        
        # Final checkpoint
        await self._save_checkpoint()
        
        result.duration_seconds = time.perf_counter() - start_time
        
        # Log summary
        logger.info(
            "Pipeline complete: discovered=%d, stored=%d, failed=%d, duration=%.1fs",
            result.records_discovered,
            result.records_stored,
            result.records_failed,
            result.duration_seconds,
        )
        
        self.metrics.log_summary()
        self.metrics.save_to_file()
        
        return result
    
    async def _discover_matches(
        self,
        mode: PipelineMode,
        epochs: list[int],
        match_ids: Optional[list[str]] = None,
    ) -> list[str]:
        """Discover matches to process.
        
        Args:
            mode: Pipeline operation mode
            epochs: Epochs to search
            match_ids: Optional specific IDs to process
            
        Returns:
            List of match IDs to process
        """
        if match_ids:
            # Use provided IDs
            for match_id in match_ids:
                self.tracker._get_state(match_id)  # Ensure state exists
            return match_ids
        
        discovered: list[str] = []
        
        for epoch_num in epochs:
            epoch_config = EPOCHS.get(epoch_num)
            if not epoch_config:
                continue
            
            # Use harvester's discovery logic
            harvester = EpochHarvester(
                mode=mode.value,
                epochs=[epoch_num],
                registry=self.registry,
            )
            
            # Get match IDs from DB or discovery
            epoch_matches = await self._get_epoch_matches(epoch_num, mode)
            
            for match_id in epoch_matches:
                # Check if we should skip
                if mode == PipelineMode.DELTA and self.registry.should_skip(match_id):
                    self.metrics.record_registry_skip()
                    continue
                
                self.metrics.record_registry_check()
                
                # Mark as discovered in tracker
                self.tracker.mark_stage_complete(match_id, "discovered")
                discovered.append(match_id)
        
        return discovered
    
    async def _get_epoch_matches(
        self,
        epoch_num: int,
        mode: PipelineMode,
    ) -> list[str]:
        """Get match IDs for an epoch from database."""
        import os
        
        db_url = self.config.database_url or os.environ.get("DATABASE_URL")
        if not db_url:
            return []
        
        try:
            import asyncpg
            
            conn = await asyncpg.connect(db_url)
            try:
                epoch_config = EPOCHS[epoch_num]
                start = epoch_config["start"]
                end = epoch_config["end"]
                
                if mode == PipelineMode.DELTA:
                    rows = await conn.fetch(
                        """
                        SELECT entity_id
                        FROM extraction_log
                        WHERE source = 'vlr_gg'
                          AND entity_type = 'match'
                          AND is_complete = FALSE
                          AND first_extracted_at >= $1
                          AND first_extracted_at < $2
                        ORDER BY first_extracted_at ASC
                        """,
                        datetime.combine(start, datetime.min.time()),
                        datetime.combine(end, datetime.max.time()),
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT entity_id
                        FROM extraction_log
                        WHERE source = 'vlr_gg'
                          AND entity_type = 'match'
                          AND first_extracted_at >= $1
                          AND first_extracted_at < $2
                        ORDER BY first_extracted_at ASC
                        """,
                        datetime.combine(start, datetime.min.time()),
                        datetime.combine(end, datetime.max.time()),
                    )
                
                return [row["entity_id"] for row in rows]
            finally:
                await conn.close()
        
        except Exception as exc:
            logger.error("Failed to get epoch %d matches: %s", epoch_num, exc)
            return []
    
    def _create_batches(self, items: list[str], batch_size: int) -> list[list[str]]:
        """Split items into batches."""
        return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
    
    async def _process_batch(
        self,
        match_ids: list[str],
        mode: PipelineMode,
        start_stage: PipelineStage,
    ) -> dict[str, int]:
        """Process a batch of matches through the pipeline.
        
        Returns:
            Dictionary with counts for each stage
        """
        results = {
            "fetched": 0,
            "verified": 0,
            "parsed": 0,
            "transformed": 0,
            "stored": 0,
            "indexed": 0,
            "failed": 0,
        }
        
        # Use semaphore for rate limiting
        semaphore = asyncio.Semaphore(self.config.max_workers)
        
        async def process_one(match_id: str) -> None:
            async with semaphore:
                try:
                    await self._process_match(
                        match_id, mode, start_stage, results
                    )
                except Exception as exc:
                    logger.error("Failed to process match %s: %s", match_id, exc)
                    results["failed"] += 1
                    self.dlq.enqueue(match_id, exc, "unknown", {})
        
        # Process batch concurrently
        await asyncio.gather(*[process_one(mid) for mid in match_ids])
        
        return results
    
    async def _process_match(
        self,
        match_id: str,
        mode: PipelineMode,
        start_stage: PipelineStage,
        results: dict[str, int],
    ) -> None:
        """Process a single match through all applicable stages."""
        
        # Determine which stages to run
        stages_to_run = self._get_stages_to_run(start_stage)
        
        # Get pending stages from tracker
        pending = self.tracker.get_pending_stages(match_id)
        stages_to_run = [s for s in stages_to_run if s in pending]
        
        if not stages_to_run:
            logger.debug("Match %s - all stages complete", match_id)
            return
        
        logger.debug("Match %s - running stages: %s", match_id, stages_to_run)
        
        raw_html: Optional[str] = None
        checksum: Optional[str] = None
        parsed_data: Optional[RawMatchData] = None
        transformed_records: list[KCRITRRecord] = []
        
        for stage in stages_to_run:
            try:
                if stage == "fetched":
                    raw_html, checksum = await self._stage_fetch(match_id, results)
                    if raw_html is None:
                        return  # Failed or skipped
                
                elif stage == "verified":
                    if not await self._stage_verify(match_id, raw_html, checksum, results):
                        return
                
                elif stage == "parsed":
                    parsed_data = await self._stage_parse(match_id, raw_html, results)
                    if parsed_data is None:
                        return
                
                elif stage == "transformed":
                    transformed_records = await self._stage_transform(
                        match_id, parsed_data, checksum or "", results
                    )
                
                elif stage == "crossref":
                    await self._stage_crossref(match_id, transformed_records, results)
                
                elif stage == "stored":
                    await self._stage_store(match_id, transformed_records, results)
                
                elif stage == "indexed":
                    await self._stage_index(match_id, checksum or "", results)
                
                # Mark stage complete
                self.tracker.mark_stage_complete(match_id, stage)
                
            except Exception as exc:
                logger.error("Stage %s failed for match %s: %s", stage, match_id, exc)
                self.tracker.mark_stage_failed(match_id, stage, str(exc))
                self.dlq.enqueue(match_id, exc, stage, {"match_id": match_id})
                results["failed"] += 1
                return
    
    def _get_stages_to_run(self, start_stage: PipelineStage) -> list[str]:
        """Get list of stages to run based on starting point."""
        all_stages = StageTracker.STAGES
        
        if start_stage == PipelineStage.ALL:
            return all_stages
        
        stage_map = {
            PipelineStage.DISCOVER: [],
            PipelineStage.FETCH: ["fetched"],
            PipelineStage.VERIFY: ["fetched", "verified"],
            PipelineStage.PARSE: ["fetched", "verified", "parsed"],
            PipelineStage.TRANSFORM: ["fetched", "verified", "parsed", "transformed"],
            PipelineStage.CROSSREF: ["fetched", "verified", "parsed", "transformed", "crossref"],
            PipelineStage.STORE: ["fetched", "verified", "parsed", "transformed", "crossref", "stored"],
            PipelineStage.INDEX: all_stages,
        }
        
        return stage_map.get(start_stage, all_stages)
    
    async def _stage_fetch(
        self,
        match_id: str,
        results: dict[str, int],
    ) -> tuple[Optional[str], Optional[str]]:
        """Fetch raw HTML for a match."""
        with self.metrics.measure("fetch"):
            # Check if already in raw repository
            existing = self._find_existing_raw(match_id)
            if existing:
                logger.debug("Match %s - found in raw storage", match_id)
                raw_html = self.raw_repo.get_raw(existing)
                if raw_html:
                    results["fetched"] += 1
                    return raw_html, existing
            
            # Fetch from source
            url = f"https://www.vlr.gg/{match_id}"
            
            async with ResilientVLRClient(
                rate_limit_seconds=self.config.rate_limit_seconds
            ) as client:
                response = await client.ethical_fetch(url)
                
                if response.status != 200:
                    raise RuntimeError(f"HTTP {response.status}")
                
                # Store raw
                await self.raw_repo.store_raw(
                    raw_html=response.raw_html,
                    checksum=response.checksum,
                    source_url=url,
                    epoch=self._get_epoch_for_match(match_id),
                    vlr_match_id=match_id,
                    http_status=response.status,
                )
                
                results["fetched"] += 1
                return response.raw_html, response.checksum
    
    def _find_existing_raw(self, match_id: str) -> Optional[str]:
        """Find existing raw record for match ID."""
        # This is a simplified lookup - in production, index by match_id
        return None
    
    async def _stage_verify(
        self,
        match_id: str,
        raw_html: Optional[str],
        checksum: Optional[str],
        results: dict[str, int],
    ) -> bool:
        """Verify integrity of fetched data."""
        with self.metrics.measure("verify"):
            if not raw_html or not checksum:
                raise ValueError("Missing raw_html or checksum for verification")
            
            from extraction.src.storage.integrity_checker import compute_checksum
            
            computed = compute_checksum(raw_html.encode())
            if computed != checksum:
                raise ValueError(f"Checksum mismatch for match {match_id}")
            
            results["verified"] += 1
            return True
    
    async def _stage_parse(
        self,
        match_id: str,
        raw_html: Optional[str],
        results: dict[str, int],
    ) -> Optional[RawMatchData]:
        """Parse raw HTML into structured data."""
        with self.metrics.measure("parse"):
            if not raw_html:
                raise ValueError("Missing raw_html for parsing")
            
            parsed = self.match_parser.parse(raw_html, match_id)
            if parsed is None:
                raise ValueError(f"Failed to parse match {match_id}")
            
            results["parsed"] += 1
            return parsed
    
    async def _stage_transform(
        self,
        match_id: str,
        parsed_data: Optional[RawMatchData],
        checksum: str,
        results: dict[str, int],
    ) -> list[KCRITRRecord]:
        """Transform parsed data to KCRITR schema."""
        with self.metrics.measure("transform"):
            if not parsed_data:
                raise ValueError("Missing parsed_data for transformation")
            
            records = self.extraction_bridge.transform(parsed_data)
            results["transformed"] += 1
            return records
    
    async def _stage_crossref(
        self,
        match_id: str,
        records: list[KCRITRRecord],
        results: dict[str, int],
    ) -> None:
        """Cross-reference against external sources."""
        with self.metrics.measure("crossref"):
            if not self.config.enable_crossref:
                return
            
            # Sample validation
            result = self.crossref.validate_vs_hltv(sample_size=min(len(records), 10))
            if not result.passed:
                logger.warning(
                    "Cross-reference validation below threshold for match %s: %s",
                    match_id, result.notes
                )
    
    async def _stage_store(
        self,
        match_id: str,
        records: list[KCRITRRecord],
        results: dict[str, int],
    ) -> None:
        """Store records to database."""
        with self.metrics.measure("store"):
            if not self.config.database_url:
                logger.debug("No database URL - skipping store")
                return
            
            try:
                import asyncpg
                
                conn = await asyncpg.connect(self.config.database_url)
                try:
                    for record in records:
                        await self._insert_record(conn, record)
                    
                    results["stored"] += 1
                finally:
                    await conn.close()
            
            except Exception as exc:
                logger.error("Failed to store match %s: %s", match_id, exc)
                raise
    
    async def _insert_record(
        self,
        conn: Any,
        record: KCRITRRecord,
    ) -> None:
        """Insert a single KCRITR record into database."""
        # Simplified insert - production would use proper schema
        await conn.execute(
            """
            INSERT INTO player_performance (
                player_id, name, team, region, role,
                kills, deaths, acs, adr, kast_pct,
                match_id, map_name, tournament, data_source,
                checksum_sha256, confidence_tier, separation_flag
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                     $11, $12, $13, $14, $15, $16, $17)
            ON CONFLICT (player_id, match_id) DO UPDATE SET
                kills = EXCLUDED.kills,
                deaths = EXCLUDED.deaths,
                acs = EXCLUDED.acs,
                checksum_sha256 = EXCLUDED.checksum_sha256
            """,
            str(record.player_id),
            record.name,
            record.team,
            record.region,
            record.role,
            record.kills,
            record.deaths,
            record.acs,
            record.adr,
            record.kast_pct,
            record.match_id,
            record.map_name,
            record.tournament,
            record.data_source,
            record.checksum_sha256,
            record.confidence_tier,
            record.separation_flag,
        )
    
    async def _stage_index(
        self,
        match_id: str,
        checksum: str,
        results: dict[str, int],
    ) -> None:
        """Update extraction log index."""
        with self.metrics.measure("index"):
            self.registry.mark_complete(match_id, checksum)
            results["indexed"] += 1
    
    async def _save_checkpoint(self) -> None:
        """Save pipeline checkpoint."""
        logger.info("Saving checkpoint...")
        
        # Save tracker state
        checkpoint_file = self.config.checkpoint_path / f"checkpoint_{datetime.now():%Y%m%d_%H%M%S}.json"
        self.tracker.save_to_file(checkpoint_file)
        
        # Save metrics
        self.metrics.record_checkpoint()
        self.metrics.save_to_file()
        
        # Save dead letter report
        self.dlq.save_report()
        
        logger.info("Checkpoint saved to %s", checkpoint_file)
    
    def _get_epoch_for_match(self, match_id: str) -> int:
        """Determine epoch for a match ID."""
        # Simplified - in production, look up from extraction_log
        return 2
    
    def stop(self) -> None:
        """Request graceful shutdown."""
        logger.info("Stop requested - will halt after current batch")
        self._stop_requested = True
    
    async def retry_dead_letter(self) -> dict:
        """Retry all dead letter queue entries."""
        logger.info("Retrying dead letter queue (%d items)...", self.dlq.size())
        
        results = self.dlq.retry_all(max_retries=self.config.max_retries)
        
        logger.info(
            "Dead letter retry complete: success=%d, failed=%d",
            results["success"], results["failed"]
        )
        
        return results


def parse_stage(value: str) -> PipelineStage:
    """Parse stage string to enum."""
    try:
        return PipelineStage(value.lower())
    except ValueError:
        valid = [s.value for s in PipelineStage]
        raise argparse.ArgumentTypeError(f"Invalid stage '{value}'. Valid: {valid}")


def parse_epochs(value: str) -> list[int]:
    """Parse epochs string to list."""
    try:
        return [int(e.strip()) for e in value.split(",")]
    except ValueError:
        raise argparse.ArgumentTypeError("Epochs must be comma-separated integers (e.g., 1,2,3)")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Axiom Esports Data Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run delta update for current epoch
  python -m pipeline.orchestrator --mode=delta --epochs=3
  
  # Full reprocessing with more workers
  python -m pipeline.orchestrator --mode=full --max-workers=5
  
  # Retry failed records
  python -m pipeline.orchestrator --retry-dead-letter
        """
    )
    
    parser.add_argument(
        "--mode",
        choices=[m.value for m in PipelineMode],
        default="delta",
        help="Pipeline operation mode (default: delta)",
    )
    parser.add_argument(
        "--epochs",
        type=parse_epochs,
        default="1,2,3",
        help="Comma-separated epoch numbers (default: 1,2,3)",
    )
    parser.add_argument(
        "--stage",
        type=parse_stage,
        default="all",
        help="Stage to start from (default: all)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Records per batch (default: 100)",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=3,
        help="Concurrent workers (default: 3)",
    )
    parser.add_argument(
        "--checkpoint-interval",
        type=int,
        default=50,
        help="Save progress every N records (default: 50)",
    )
    parser.add_argument(
        "--retry-dead-letter",
        action="store_true",
        help="Retry failed records from dead letter queue",
    )
    parser.add_argument(
        "--metrics-path",
        type=Path,
        help="Path for metrics export",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Override config with CLI args
    config = PipelineConfig.from_env()
    config.batch_size = args.batch_size
    config.max_workers = args.max_workers
    config.checkpoint_interval = args.checkpoint_interval
    if args.metrics_path:
        config.metrics_path = args.metrics_path
    config.validate()
    
    orchestrator = PipelineOrchestrator(config)
    
    if args.retry_dead_letter:
        result = asyncio.run(orchestrator.retry_dead_letter())
        print(f"Retry complete: {result}")
    else:
        mode = PipelineMode(args.mode)
        start_stage = args.stage
        
        result = asyncio.run(orchestrator.run(
            mode=mode,
            epochs=args.epochs,
            start_stage=start_stage,
        ))
        
        print(f"\nPipeline Result: {result.to_dict()}")


if __name__ == "__main__":
    main()
