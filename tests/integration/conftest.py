"""
Pytest fixtures for pipeline integration tests.

Provides comprehensive mocking and fixtures for testing the complete
pipeline flow without requiring external services (database, VLR.gg, etc.).
"""

import pytest
import asyncio
import hashlib
import tempfile
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

# Add shared path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared" / "axiom-esports-data"))

from pipeline import PipelineOrchestrator, PipelineMode, PipelineStage
from pipeline.models import RunInstance, RunStatus, TriggerType
from pipeline.scheduler import PipelineScheduler
from pipeline.runner import PipelineRunner
from pipeline.config import PipelineConfig
from pipeline.dead_letter import DeadLetterQueue
from pipeline.metrics import PipelineMetrics
from pipeline.stage_tracker import StageTracker
from extraction.src.storage.known_record_registry import KnownRecordRegistry
from extraction.src.storage.integrity_checker import compute_checksum
from extraction.src.parsers.match_parser import RawMatchData
from extraction.src.bridge.extraction_bridge import ExtractionBridge, KCRITRRecord


# ============================================================================
# Event Loop Fixture
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Temporary Directory Fixtures
# ============================================================================

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_storage_path(temp_data_dir):
    """Create temporary storage paths for pipeline components."""
    return {
        "raw": temp_data_dir / "raw_extractions",
        "dead_letter": temp_data_dir / "dead_letter",
        "metrics": temp_data_dir / "metrics",
        "checkpoints": temp_data_dir / "checkpoints",
    }


# ============================================================================
# Pipeline Configuration Fixtures
# ============================================================================

@pytest.fixture
def test_pipeline_config(temp_storage_path):
    """Create a test pipeline configuration."""
    config = PipelineConfig(
        mode="delta",
        epochs=[1, 2, 3],
        batch_size=10,
        max_workers=2,
        checkpoint_interval=5,
        rate_limit_seconds=0.1,
        max_retries=2,
        dead_letter_path=temp_storage_path["dead_letter"],
        metrics_path=temp_storage_path["metrics"],
        checkpoint_path=temp_storage_path["checkpoints"],
        raw_storage_path=temp_storage_path["raw"],
        database_url=None,  # Use in-memory mode
        skip_checksum_unchanged=True,
        enable_crossref=False,
        enable_metrics=True,
        log_level="DEBUG",
    )
    config.ensure_directories()
    return config


# ============================================================================
# Mock VLR Client Fixtures
# ============================================================================

@dataclass
class MockVLRResponse:
    """Mock response from VLR.gg client."""
    status: int = 200
    raw_html: str = ""
    checksum: str = ""
    url: str = ""


def generate_sample_match_html(match_id: str, tournament: str = "Test Tournament") -> str:
    """Generate sample VLR.gg match HTML for testing."""
    players_html = ""
    agents = ["Jett", "Viper", "Sova", "Killjoy", "Sage", 
              "Reyna", "Brimstone", "Breach", "Cypher", "Skye"]
    
    for i in range(10):
        team = "TeamA" if i < 5 else "TeamB"
        players_html += f'''
        <div class="vm-stats-game">
            <div class="mod-player" data-team-name="{team}">
                <div class="text-of">Player{i:03d}</div>
                <img alt="{agents[i]}" />
                <td class="mod-stat">{1.0 + i * 0.1:.2f}</td>
                <td class="mod-stat">{150 + i * 15}</td>
                <td class="mod-stat">{10 + i}</td>
                <td class="mod-stat">{15 - i % 8}</td>
                <td class="mod-stat">{5 + i % 5}</td>
                <td class="mod-stat">{60 + i * 2}%</td>
                <td class="mod-stat">{80 + i * 8}</td>
                <td class="mod-stat">{15 + i}%</td>
                <td class="mod-stat">{i % 5}</td>
                <td class="mod-stat">{i % 3}</td>
            </div>
        </div>
        '''
    
    html = f'''
    <html>
    <body>
        <div class="match-header-event">
            <div>{tournament}</div>
        </div>
        <div class="map"><span>Haven</span></div>
        <div data-utc-ts="1733011200">Date</div>
        <div>Patch 8.11</div>
        {players_html}
    </body>
    </html>
    '''
    return html


@pytest.fixture
def mock_vlr_client():
    """Mock VLR.gg client for testing."""
    client = MagicMock()
    
    # Create a factory for responses
    def create_response(url: str, match_id: str = None) -> MockVLRResponse:
        if match_id is None:
            match_id = url.split("/")[-1] if "/" in url else "test_match"
        
        html = generate_sample_match_html(match_id)
        checksum = compute_checksum(html.encode())
        
        return MockVLRResponse(
            status=200,
            raw_html=html,
            checksum=checksum,
            url=url,
        )
    
    # Set up the ethical_fetch method
    async def ethical_fetch(url: str, **kwargs) -> MockVLRResponse:
        return create_response(url)
    
    client.ethical_fetch = AsyncMock(side_effect=ethical_fetch)
    client.create_response = create_response
    
    return client


@pytest.fixture
def mock_vlr_client_with_failures():
    """Mock VLR client that simulates various failure modes."""
    client = MagicMock()
    
    call_count = 0
    fail_match_ids = {"fail_match_001", "fail_match_002"}
    
    async def ethical_fetch(url: str, **kwargs) -> MockVLRResponse:
        nonlocal call_count
        call_count += 1
        match_id = url.split("/")[-1] if "/" in url else "test_match"
        
        if match_id in fail_match_ids:
            return MockVLRResponse(
                status=500,
                raw_html="",
                checksum="",
                url=url,
            )
        
        html = generate_sample_match_html(match_id)
        return MockVLRResponse(
            status=200,
            raw_html=html,
            checksum=compute_checksum(html.encode()),
            url=url,
        )
    
    client.ethical_fetch = AsyncMock(side_effect=ethical_fetch)
    client.call_count = lambda: call_count
    client.fail_match_ids = fail_match_ids
    
    return client


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_player_stats():
    """Sample valid player statistics."""
    return {
        'player_id': 'p001',
        'match_id': 'm001',
        'name': 'TestPlayer',
        'team': 'TestTeam',
        'kills': 20,
        'deaths': 15,
        'assists': 5,
        'acs': 245,
        'adr': 158,
        'kast_pct': 74.2,
        'hs_pct': 28.5,
        'first_bloods': 3,
        'clutch_wins': 1,
    }


@pytest.fixture
def sample_raw_match_data():
    """Create sample RawMatchData for testing."""
    return RawMatchData(
        vlr_match_id="test_match_001",
        tournament="VCT 2025 Masters Bangkok",
        map_name="Haven",
        match_date="1733011200",
        patch_version="8.11",
        players=[
            {
                "player": f"Player{i:03d}",
                "team": "TeamA" if i < 5 else "TeamB",
                "agent": ["Jett", "Viper", "Sova", "Killjoy", "Sage",
                         "Reyna", "Brimstone", "Breach", "Cypher", "Skye"][i],
                "acs": str(150 + i * 15),
                "kills": str(10 + i),
                "deaths": str(15 - i % 8),
                "assists": str(5 + i % 5),
                "kast": f"{60 + i * 2}%",
                "adr": str(80 + i * 8),
                "hs_pct": f"{15 + i}%",
                "first_blood": str(i % 5),
                "clutch_win": str(i % 3),
            }
            for i in range(10)
        ],
    )


@pytest.fixture
def sample_kcritr_records(sample_raw_match_data):
    """Generate sample KCRITR records from raw match data."""
    bridge = ExtractionBridge()
    return bridge.transform(sample_raw_match_data)


# ============================================================================
# Component Fixtures
# ============================================================================

@pytest.fixture
def test_registry():
    """Create a test KnownRecordRegistry (in-memory mode)."""
    return KnownRecordRegistry(db_url=None)


@pytest.fixture
def test_tracker(temp_data_dir):
    """Create a test StageTracker."""
    state_file = temp_data_dir / "tracker_state.json"
    return StageTracker(db_url=None, state_file=state_file)


@pytest.fixture
def test_dlq(temp_storage_path):
    """Create a test DeadLetterQueue."""
    return DeadLetterQueue(storage_path=temp_storage_path["dead_letter"])


@pytest.fixture
def test_metrics(temp_storage_path):
    """Create a test PipelineMetrics."""
    return PipelineMetrics(metrics_path=temp_storage_path["metrics"])


@pytest.fixture
def test_scheduler():
    """Create a test PipelineScheduler."""
    return PipelineScheduler()


@pytest.fixture
def test_runner():
    """Create a test PipelineRunner."""
    return PipelineRunner()


# ============================================================================
# Orchestrator Fixtures with Mocks
# ============================================================================

@pytest.fixture
def mock_orchestrator_deps(test_pipeline_config, temp_storage_path):
    """Create mocked dependencies for PipelineOrchestrator."""
    
    # Create real components
    registry = KnownRecordRegistry(db_url=None)
    tracker = StageTracker(db_url=None)
    metrics = PipelineMetrics(metrics_path=temp_storage_path["metrics"])
    dlq = DeadLetterQueue(storage_path=temp_storage_path["dead_letter"])
    
    return {
        "config": test_pipeline_config,
        "registry": registry,
        "tracker": tracker,
        "metrics": metrics,
        "dlq": dlq,
    }


@pytest.fixture
def patched_orchestrator(mock_orchestrator_deps, mock_vlr_client):
    """Create a PipelineOrchestrator with mocked external dependencies."""
    deps = mock_orchestrator_deps
    
    # Patch the ResilientVLRClient to use our mock
    with patch("pipeline.orchestrator.ResilientVLRClient") as mock_client_class:
        # Create an async context manager mock
        mock_instance = MagicMock()
        mock_instance.ethical_fetch = mock_vlr_client.ethical_fetch
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Create orchestrator with real components but mocked client
        orchestrator = PipelineOrchestrator(
            config=deps["config"],
            registry=deps["registry"],
            tracker=deps["tracker"],
            metrics=deps["metrics"],
            dlq=deps["dlq"],
        )
        
        yield orchestrator


# ============================================================================
# Database Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_db_connection():
    """Create a mock database connection for testing."""
    conn = MagicMock()
    
    # Mock fetch results
    mock_rows = [
        {"entity_id": f"match_{i:03d}"} 
        for i in range(20)
    ]
    conn.fetch = AsyncMock(return_value=mock_rows)
    conn.execute = AsyncMock(return_value=None)
    conn.close = AsyncMock(return_value=None)
    
    return conn


@pytest.fixture
def mock_asyncpg():
    """Mock asyncpg module for database testing."""
    with patch("asyncpg.connect") as mock_connect:
        conn = MagicMock()
        conn.fetch = AsyncMock(return_value=[])
        conn.execute = AsyncMock(return_value=None)
        conn.close = AsyncMock(return_value=None)
        mock_connect.return_value = conn
        yield mock_connect


# ============================================================================
# Verification Fixtures
# ============================================================================

@pytest.fixture
def valid_player_stats():
    """Generate valid player statistics for verification testing."""
    return {
        'player_id': 'p001',
        'match_id': 'm001',
        'name': 'TestPlayer',
        'team': 'TestTeam',
        'kills': 20,
        'deaths': 15,
        'assists': 5,
        'acs': 245,
        'adr': 158,
        'kast_pct': 74.2,
        'hs_pct': 28.5,
        'first_bloods': 3,
        'clutch_wins': 1,
    }


@pytest.fixture
def invalid_player_stats():
    """Generate invalid player statistics for verification testing."""
    return {
        'player_id': 'p002',
        'match_id': 'm001',
        'name': 'InvalidPlayer',
        'team': 'TestTeam',
        'kills': -5,  # Invalid: negative kills
        'deaths': 15,
        'assists': 100,  # Invalid: too high
        'acs': 1000,  # Invalid: exceeds max
        'adr': -10,  # Invalid: negative
        'kast_pct': 150.0,  # Invalid: exceeds 100%
        'hs_pct': -5.0,  # Invalid: negative
        'first_bloods': -1,  # Invalid: negative
    }


# ============================================================================
# Checkpoint and State Fixtures
# ============================================================================

@pytest.fixture
def sample_checkpoint():
    """Create a sample checkpoint for testing resumption."""
    from pipeline.models import Checkpoint
    
    return Checkpoint(
        checkpoint_id="chk_001",
        run_id="run_001",
        stage="fetched",
        completed_match_ids=["match_001", "match_002", "match_003"],
        metadata={"batch_num": 2},
    )


@pytest.fixture
def partially_completed_tracker():
    """Create a tracker with some completed stages."""
    tracker = StageTracker(db_url=None)
    
    # Mark some stages complete for certain matches
    for i in range(5):
        match_id = f"match_{i:03d}"
        tracker.mark_stage_complete(match_id, "discovered")
        tracker.mark_stage_complete(match_id, "fetched")
        if i < 3:  # First 3 are fully verified
            tracker.mark_stage_complete(match_id, "verified")
            tracker.mark_stage_complete(match_id, "parsed")
    
    return tracker
