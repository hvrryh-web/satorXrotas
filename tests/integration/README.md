# Pipeline Integration Tests

Comprehensive end-to-end integration tests for the Axiom Esports Data Pipeline.

## Overview

These tests verify the complete data pipeline flow:

1. **Discovery** - Find match IDs from data sources
2. **Fetch** - Download raw HTML (respects registry skip check)
3. **Verify** - Checksum validation, integrity checks
4. **Parse** - Extract structured data from HTML
5. **Transform** - Map to KCRITR schema via extraction_bridge
6. **Crossref** - Validate against external sources (HLTV)
7. **Store** - Write to PostgreSQL
8. **Index** - Update extraction_log

## Test Structure

```
tests/integration/
├── conftest.py              # Shared fixtures and test utilities
├── test_pipeline_e2e.py     # Complete pipeline flow tests
├── test_dedup_redundancy.py # Deduplication and redundancy tests
└── README.md                # This file
```

## Running the Tests

### Prerequisites

```bash
# Install dependencies
pip install pytest pytest-asyncio

# Set up test paths
export PYTHONPATH="${PYTHONPATH}:$(pwd)/shared/axiom-esports-data"
```

### Run All Integration Tests

```bash
# From project root
python -m pytest tests/integration/ -v

# With coverage
python -m pytest tests/integration/ --cov=pipeline --cov=extraction --cov-report=html
```

### Run Specific Test Files

```bash
# End-to-end tests only
python -m pytest tests/integration/test_pipeline_e2e.py -v

# Deduplication tests only
python -m pytest tests/integration/test_dedup_redundancy.py -v
```

### Run Specific Test Classes

```bash
# Test pipeline end-to-end flow
python -m pytest tests/integration/test_pipeline_e2e.py::TestPipelineEndToEnd -v

# Test deduplication system
python -m pytest tests/integration/test_dedup_redundancy.py::TestRedundancyPrevention -v
```

### Debug Mode

```bash
# Run with debug logging
python -m pytest tests/integration/ -v --log-cli-level=DEBUG

# Run single test with pdb on failure
python -m pytest tests/integration/test_pipeline_e2e.py::TestPipelineEndToEnd::test_full_pipeline_run -v --pdb
```

## Test Coverage

### End-to-End Tests (`test_pipeline_e2e.py`)

| Test Class | Description |
|------------|-------------|
| `TestPipelineEndToEnd` | Complete pipeline flow from discovery to storage |
| `TestDeduplicationSystem` | Checksum and content-level duplicate detection |
| `TestVerificationFramework` | Transport integrity and semantic validation |
| `TestStageByStageProcessing` | Individual pipeline stage testing |
| `TestPipelineModes` | Delta, full, and backfill modes |
| `TestErrorHandling` | Failure handling and retry mechanisms |

### Deduplication Tests (`test_dedup_redundancy.py`)

| Test Class | Description |
|------------|-------------|
| `TestRedundancyPrevention` | Registry-based fetch prevention |
| `TestContentDeduplication` | Cross-source player deduplication |
| `TestBridgeDeduplication` | ExtractionBridge consistency |
| `TestRegistryStatistics` | Stats calculation and monitoring |
| `TestIntegrityBasedDeduplication` | Checksum-based deduplication |
| `TestConcurrentAccess` | Concurrent deduplication scenarios |
| `TestDeduplicationEdgeCases` | Edge cases and special characters |
| `TestDeduplicationPipelineIntegration` | Full pipeline integration |

## Fixtures

### Core Fixtures

- `temp_data_dir` - Temporary directory for test data
- `test_pipeline_config` - Pre-configured PipelineConfig for testing
- `mock_vlr_client` - Mock VLR.gg client with sample HTML responses
- `mock_vlr_client_with_failures` - Mock client that simulates failures

### Component Fixtures

- `test_registry` - In-memory KnownRecordRegistry
- `test_tracker` - StageTracker with temp state file
- `test_dlq` - DeadLetterQueue in temp directory
- `test_metrics` - PipelineMetrics with temp export path
- `patched_orchestrator` - PipelineOrchestrator with mocked dependencies

### Data Fixtures

- `sample_raw_match_data` - Sample RawMatchData instance
- `sample_kcritr_records` - Transformed KCRITR records
- `valid_player_stats` - Valid player statistics for verification
- `invalid_player_stats` - Invalid stats for error testing

## Expected Coverage

| Component | Expected Coverage |
|-----------|-------------------|
| `PipelineOrchestrator` | 90%+ |
| `KnownRecordRegistry` | 95%+ |
| `StageTracker` | 85%+ |
| `DeadLetterQueue` | 90%+ |
| `PipelineMetrics` | 80%+ |
| `ExtractionBridge` | 85%+ |

## Integration with CI/CD

```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      
      - name: Run integration tests
        run: |
          python -m pytest tests/integration/ \
            --cov=pipeline --cov=extraction \
            --cov-report=xml --cov-report=html
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

## Troubleshooting

### Common Issues

**Import Errors**
```bash
# Ensure PYTHONPATH includes the shared module
export PYTHONPATH="${PYTHONPATH}:$(pwd)/shared/axiom-esports-data"
```

**Async Test Failures**
```bash
# Ensure pytest-asyncio is installed
pip install pytest-asyncio

# Run with asyncio mode explicitly
python -m pytest tests/integration/ --asyncio-mode=auto
```

**Permission Errors on Windows**
```powershell
# Run with proper permissions or use temp directories
# The tests use tempfile.TemporaryDirectory which handles cleanup
```

### Debug Output

Enable verbose logging to diagnose issues:

```python
# In test file or conftest.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Writing New Tests

### Test Template

```python
import pytest
from pathlib import Path

class TestMyFeature:
    """Description of feature being tested."""
    
    @pytest.mark.asyncio
    async def test_my_async_feature(self, patched_orchestrator):
        """Test description."""
        orchestrator = patched_orchestrator
        
        # Act
        result = await orchestrator.run(
            mode=PipelineMode.DELTA,
            match_ids=["test_match"],
        )
        
        # Assert
        assert result.records_discovered == 1
        assert result.errors == 0
```

### Best Practices

1. **Use fixtures** - Leverage existing fixtures from `conftest.py`
2. **Mock external calls** - Use `patched_orchestrator` to avoid network calls
3. **Clean up resources** - Use temp directories for file operations
4. **Test edge cases** - Include empty inputs, special characters, boundary values
5. **Document behavior** - Clear docstrings explain what is being tested

## Maintenance

### Updating Tests

When modifying pipeline code:

1. Run tests to identify broken assertions
2. Update test expectations to match new behavior
3. Add tests for new features
4. Ensure coverage remains above thresholds

### Adding New Fixtures

Add new fixtures to `conftest.py` if they will be used across multiple test files:

```python
@pytest.fixture
def my_new_fixture():
    """Description of fixture."""
    return SomeTestData()
```

## Contact

For questions about these tests, refer to:
- Pipeline documentation: `shared/axiom-esports-data/pipeline/__init__.py`
- Extraction docs: `shared/axiom-esports-data/extraction/`
- Main project: `AGENTS.md`
