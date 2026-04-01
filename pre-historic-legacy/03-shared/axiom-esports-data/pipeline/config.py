"""
Pipeline Configuration Management
=================================

Environment-based configuration with sensible defaults.
All settings can be overridden via environment variables.

Example:
    export PIPELINE_MODE=delta
    export PIPELINE_BATCH_SIZE=100
    export PIPELINE_MAX_WORKERS=5
    export PIPELINE_CHECKPOINT_INTERVAL=50
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for the data pipeline orchestrator.
    
    Attributes:
        mode: Pipeline mode - "delta", "full", or "backfill"
        epochs: List of epochs to process (1=historic, 2=mature, 3=current)
        batch_size: Number of records to process in each batch
        max_workers: Maximum concurrent workers for parallel processing
        checkpoint_interval: Save progress every N records
        rate_limit_seconds: Seconds between requests to avoid rate limiting
        max_retries: Maximum retry attempts for failed records
        dead_letter_path: Path to store dead letter queue
        metrics_path: Path to store metrics export
        database_url: PostgreSQL connection string
        raw_storage_path: Path to raw extraction storage
        skip_checksum_unchanged: Skip records with unchanged checksums
        enable_crossref: Enable HLTV cross-reference validation
        correlation_target: Minimum correlation threshold for validation
    """
    
    # Pipeline operation mode
    mode: str = "delta"
    epochs: list[int] = field(default_factory=lambda: [1, 2, 3])
    
    # Performance tuning
    batch_size: int = 100
    max_workers: int = 3
    checkpoint_interval: int = 50
    rate_limit_seconds: float = 2.0
    
    # Retry configuration
    max_retries: int = 3
    retry_delay_seconds: float = 5.0
    
    # Storage paths
    dead_letter_path: Path = field(default_factory=lambda: Path("data/dead_letter"))
    metrics_path: Path = field(default_factory=lambda: Path("data/metrics"))
    checkpoint_path: Path = field(default_factory=lambda: Path("data/checkpoints"))
    raw_storage_path: Path = field(
        default_factory=lambda: Path(os.environ.get("RAW_STORAGE_PATH", "data/raw_extractions"))
    )
    
    # Database
    database_url: Optional[str] = None
    
    # Feature flags
    skip_checksum_unchanged: bool = True
    enable_crossref: bool = False
    enable_metrics: bool = True
    enable_dead_letter: bool = True
    
    # Validation thresholds
    correlation_target: float = 0.85
    min_confidence_tier: float = 50.0
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def from_env(cls) -> "PipelineConfig":
        """Create configuration from environment variables."""
        config = cls()
        
        # Mode and epochs
        config.mode = os.getenv("PIPELINE_MODE", config.mode)
        epochs_str = os.getenv("PIPELINE_EPOCHS", "")
        if epochs_str:
            config.epochs = [int(e.strip()) for e in epochs_str.split(",")]
        
        # Performance tuning
        config.batch_size = int(os.getenv("PIPELINE_BATCH_SIZE", config.batch_size))
        config.max_workers = int(os.getenv("PIPELINE_MAX_WORKERS", config.max_workers))
        config.checkpoint_interval = int(
            os.getenv("PIPELINE_CHECKPOINT_INTERVAL", config.checkpoint_interval)
        )
        config.rate_limit_seconds = float(
            os.getenv("PIPELINE_RATE_LIMIT", config.rate_limit_seconds)
        )
        
        # Retry configuration
        config.max_retries = int(os.getenv("PIPELINE_MAX_RETRIES", config.max_retries))
        config.retry_delay_seconds = float(
            os.getenv("PIPELINE_RETRY_DELAY", config.retry_delay_seconds)
        )
        
        # Storage paths
        if dl_path := os.getenv("PIPELINE_DEAD_LETTER_PATH"):
            config.dead_letter_path = Path(dl_path)
        if metrics_path := os.getenv("PIPELINE_METRICS_PATH"):
            config.metrics_path = Path(metrics_path)
        if checkpoint_path := os.getenv("PIPELINE_CHECKPOINT_PATH"):
            config.checkpoint_path = Path(checkpoint_path)
        
        # Database
        config.database_url = os.getenv("DATABASE_URL", config.database_url)
        
        # Feature flags
        config.skip_checksum_unchanged = (
            os.getenv("PIPELINE_SKIP_CHECKSUM", "true").lower() == "true"
        )
        config.enable_crossref = (
            os.getenv("PIPELINE_ENABLE_CROSSREF", "false").lower() == "true"
        )
        config.enable_metrics = (
            os.getenv("PIPELINE_ENABLE_METRICS", "true").lower() == "true"
        )
        config.enable_dead_letter = (
            os.getenv("PIPELINE_ENABLE_DEAD_LETTER", "true").lower() == "true"
        )
        
        # Validation thresholds
        config.correlation_target = float(
            os.getenv("PIPELINE_CORRELATION_TARGET", config.correlation_target)
        )
        config.min_confidence_tier = float(
            os.getenv("PIPELINE_MIN_CONFIDENCE", config.min_confidence_tier)
        )
        
        # Logging
        config.log_level = os.getenv("PIPELINE_LOG_LEVEL", config.log_level)
        config.log_format = os.getenv("PIPELINE_LOG_FORMAT", config.log_format)
        
        return config
    
    def validate(self) -> None:
        """Validate configuration settings."""
        valid_modes = {"delta", "full", "backfill"}
        if self.mode not in valid_modes:
            raise ValueError(f"Invalid mode '{self.mode}'. Must be one of: {valid_modes}")
        
        valid_epochs = {1, 2, 3}
        invalid_epochs = set(self.epochs) - valid_epochs
        if invalid_epochs:
            raise ValueError(f"Invalid epochs: {invalid_epochs}. Must be subset of: {valid_epochs}")
        
        if self.batch_size < 1:
            raise ValueError("batch_size must be >= 1")
        if self.max_workers < 1:
            raise ValueError("max_workers must be >= 1")
        if self.checkpoint_interval < 1:
            raise ValueError("checkpoint_interval must be >= 1")
        
        logger.info("Pipeline configuration validated: mode=%s, epochs=%s, workers=%d",
                   self.mode, self.epochs, self.max_workers)
    
    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.dead_letter_path.mkdir(parents=True, exist_ok=True)
        self.metrics_path.mkdir(parents=True, exist_ok=True)
        self.checkpoint_path.mkdir(parents=True, exist_ok=True)
        self.raw_storage_path.mkdir(parents=True, exist_ok=True)


# Global configuration instance
_config: Optional[PipelineConfig] = None


def get_config() -> PipelineConfig:
    """Get the global pipeline configuration.
    
    Creates and caches the configuration on first call.
    """
    global _config
    if _config is None:
        _config = PipelineConfig.from_env()
        _config.validate()
        _config.ensure_directories()
    return _config


def reset_config() -> None:
    """Reset the global configuration (useful for testing)."""
    global _config
    _config = None
