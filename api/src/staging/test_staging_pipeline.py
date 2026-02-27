#!/usr/bin/env python3
"""
Staging System Test — Verifies the full data collection and export pipeline.

Run from repo root:
    pip install pyyaml
    python api/src/staging/test_staging_pipeline.py

Expected: All data collected, exported to game and web stores, firewall verified.
"""
import json
import logging
import sys
import os

# Ensure repo root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("test_staging")


def test_ingest_service():
    """Test the staging ingest service."""
    from api.src.staging.ingest_service import StagingIngestService, check_firewall

    service = StagingIngestService()

    # Test 1: Valid game definition ingest
    record = service.ingest(
        source_system="game",
        payload_type="game_definition",
        payload={"id": "weapon.ak", "data_domain": "weapons", "damage": 36},
        ingested_by="test_script",
        target_project="game",
    )
    assert record.status == "validated", f"Expected validated, got {record.status}"
    logger.info("PASS: Valid game definition ingest")

    # Test 2: Duplicate detection
    dup = service.ingest(
        source_system="game",
        payload_type="game_definition",
        payload={"id": "weapon.ak", "data_domain": "weapons", "damage": 36},
        ingested_by="test_script",
    )
    assert dup.ingest_id == record.ingest_id, "Duplicate should return existing record"
    logger.info("PASS: Duplicate detection")

    # Test 3: Rejected payload (missing required fields)
    bad = service.ingest(
        source_system="game",
        payload_type="player_stat",
        payload={"name": "test"},
        ingested_by="test_script",
    )
    assert bad.status == "rejected", f"Expected rejected, got {bad.status}"
    logger.info("PASS: Rejection of invalid payload")

    # Test 4: Firewall violation on web-bound data
    fw_record = service.ingest(
        source_system="game",
        payload_type="player_stat",
        payload={"player_id": "p1", "match_id": "m1", "simulationTick": 500},
        ingested_by="test_script",
        target_project="web",
    )
    assert fw_record.status == "rejected", f"Expected rejected for firewall violation, got {fw_record.status}"
    assert any("FIREWALL" in e for e in fw_record.validation_errors), "Should have firewall violation"
    logger.info("PASS: Firewall violation detection")

    # Test 5: Firewall check function
    violations = check_firewall({"kills": 10, "seedValue": 12345, "nested": {"radarData": [1,2,3]}})
    assert len(violations) == 2, f"Expected 2 firewall violations, got {len(violations)}"
    logger.info("PASS: Recursive firewall check")

    stats = service.get_stats()
    logger.info("Queue stats: %s", stats)
    return True


def test_game_export():
    """Test the game export form."""
    from api.src.staging.game_export_form import GameExportForm

    form = GameExportForm()

    # Export agent definitions
    agents = [
        {"id": "agent.rifler.elite", "displayName": "Elite Rifler", "baseHp": 100},
        {"id": "agent.awper.elite", "displayName": "Elite AWPer", "baseHp": 100},
    ]
    records = form.export_definitions("agents", agents)
    assert len(records) == 2, f"Expected 2 records, got {len(records)}"
    logger.info("PASS: Game agent definitions export (%d records)", len(records))

    # Export match events
    events = [{"tick": 1, "type": "kill"}, {"tick": 5, "type": "plant"}]
    record = form.export_match_events("match_001", events)
    assert record.data_type == "event_log"
    assert record.payload["event_count"] == 2
    logger.info("PASS: Game match events export")

    # Retrieve
    active = form.get_active_definitions("agent_def")
    assert len(active) == 2
    logger.info("PASS: Active definitions retrieval")

    found = form.get_by_key("agent_def", "agent.rifler.elite")
    assert found is not None
    assert found.payload["displayName"] == "Elite Rifler"
    logger.info("PASS: Definition lookup by key")

    return True


def test_web_export():
    """Test the web export form with firewall enforcement."""
    from api.src.staging.web_export_form import (
        WebExportForm, strip_game_only_fields, verify_firewall_compliance, map_to_public_schema
    )

    # Test field stripping
    raw = {
        "player_id": "p1",
        "kills": 25,
        "simulationTick": 500,
        "seedValue": 12345,
        "nested": {"radarData": [1, 2, 3], "clean": "data"},
    }
    stripped = strip_game_only_fields(raw)
    assert "simulationTick" not in stripped
    assert "seedValue" not in stripped
    assert "radarData" not in stripped["nested"]
    assert stripped["nested"]["clean"] == "data"
    logger.info("PASS: Field stripping (recursive)")

    # Test firewall compliance check
    violations = verify_firewall_compliance({"kills": 10, "deaths": 5})
    assert len(violations) == 0
    logger.info("PASS: Clean payload passes firewall")

    violations = verify_firewall_compliance({"kills": 10, "visionConeData": [1, 2]})
    assert len(violations) == 1
    logger.info("PASS: Dirty payload fails firewall")

    # Test schema mapping
    kcritr = {
        "player_id": "p1",
        "match_id": "m1",
        "kills": 25,
        "deaths": 10,
        "first_blood": 3,
        "sim_rating": 2.5,
    }
    public = map_to_public_schema(kcritr)
    assert public["playerId"] == "p1"
    assert public["kills"] == 25
    assert public["firstKills"] == 3
    assert "sim_rating" not in public  # Internal name should not appear
    assert "simRating" in public       # Public name should
    logger.info("PASS: KCRITR → public schema mapping")

    # Test full export
    form = WebExportForm()
    records = form.export_player_stats([
        {"player_id": "p1", "match_id": "m1", "kills": 25, "deaths": 10},
        {"player_id": "p2", "match_id": "m1", "kills": 18, "deaths": 15, "simulationTick": 100},
    ])
    assert len(records) == 2  # Both should export (firewall strips simulationTick)
    for r in records:
        assert r.firewall_verified is True
    logger.info("PASS: Web player stats export with firewall (%d records)", len(records))

    # Test leaderboard
    lb = form.export_leaderboard([
        {"player_id": "p1", "sim_rating": 2.5, "name": "Player1"},
        {"player_id": "p2", "sim_rating": 1.8, "name": "Player2"},
    ])
    assert len(lb) == 2
    logger.info("PASS: Leaderboard export")

    return True


def test_data_collection():
    """Test the full data collection pipeline."""
    from api.src.staging.data_collection_service import DataCollectionService

    service = DataCollectionService()
    result = service.collect_all()

    logger.info("Collection result: %s", json.dumps(result, indent=2))

    assert result["game_definitions"] > 0, "Should have collected game definitions"
    assert result["maps"] > 0, "Should have collected maps"
    assert len(result["errors"]) == 0, f"Should have no errors: {result['errors']}"

    status = service.get_system_status()
    logger.info("System status: %s", json.dumps(status, indent=2))

    assert status["game_store_count"] > 0, "Game store should have records"
    logger.info("PASS: Full data collection pipeline")

    return True


def main():
    """Run all staging system tests."""
    print("\n" + "=" * 60)
    print("  SATOR STAGING SYSTEM — PIPELINE TEST")
    print("=" * 60 + "\n")

    tests = [
        ("Ingest Service", test_ingest_service),
        ("Game Export Form", test_game_export),
        ("Web Export Form", test_web_export),
        ("Data Collection Pipeline", test_data_collection),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        print(f"\n--- {name} ---")
        try:
            result = test_fn()
            if result:
                passed += 1
                print(f"  ✓ {name}: ALL PASSED")
            else:
                failed += 1
                print(f"  ✗ {name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"  ✗ {name}: ERROR — {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'=' * 60}")
    print(f"  RESULTS: {passed} passed, {failed} failed")
    print(f"{'=' * 60}\n")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
