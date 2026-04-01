"""
Data Collection Service — Automated data gathering and staging population.

Reads game definitions from Defs/, analytics seed data, and compiles them
into the staging system. Serves as the automated pipeline that:
    1. Loads static game definitions (agents, weapons, utilities, rulesets, maps)
    2. Loads analytics reference data (role baselines, ground truth)
    3. Deposits all data into the staging ingest queue
    4. Triggers export forms to populate project-specific stores
    5. Awaits pings from game and web services for on-demand data

Safety Protocols:
    - All data is checksummed before staging
    - Duplicate detection prevents re-ingestion
    - Web-bound exports are firewall-verified
    - All operations are logged
"""
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from api.src.staging.ingest_service import StagingIngestService, SourceSystem, PayloadType
from api.src.staging.game_export_form import GameExportForm
from api.src.staging.web_export_form import WebExportForm

logger = logging.getLogger(__name__)

# Default paths relative to repo root
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFS_PATH = REPO_ROOT / "Defs"
MAPS_PATH = REPO_ROOT / "maps"
SEED_DATA_PATH = REPO_ROOT / "axiom-esports-data" / "infrastructure" / "seed_data"
CONFIG_PATH = REPO_ROOT / "axiom-esports-data" / "config"


def load_json(filepath: Path) -> Any:
    """Load a JSON file safely."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_yaml(filepath: Path) -> Any:
    """Load a YAML file safely."""
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class DataCollectionService:
    """
    Automated data collection that populates the staging system.

    Reads all static definitions, seed data, and configuration,
    then deposits into the staging ingest queue for distribution
    to game and web project stores.
    """

    def __init__(
        self,
        ingest_service: Optional[StagingIngestService] = None,
        game_export: Optional[GameExportForm] = None,
        web_export: Optional[WebExportForm] = None,
    ):
        self.ingest = ingest_service or StagingIngestService()
        self.game_export = game_export or GameExportForm(ingest_service=self.ingest)
        self.web_export = web_export or WebExportForm(ingest_service=self.ingest)
        self._collection_log: List[Dict[str, Any]] = []
        logger.info("DataCollectionService initialized")

    def collect_all(self) -> Dict[str, Any]:
        """
        Run full data collection pipeline.

        Steps:
            1. Collect game definitions
            2. Collect map data
            3. Collect analytics reference data
            4. Collect analytics config
            5. Export to game store
            6. Export to web store (with firewall)
            7. Return summary

        Returns:
            Summary dict with counts and status.
        """
        summary = {
            "game_definitions": 0,
            "maps": 0,
            "analytics_reference": 0,
            "analytics_config": 0,
            "game_exports": 0,
            "web_exports": 0,
            "errors": [],
        }

        # Step 1: Game definitions
        try:
            count = self._collect_game_definitions()
            summary["game_definitions"] = count
        except Exception as e:
            summary["errors"].append(f"Game definitions: {e}")
            logger.error("Failed to collect game definitions: %s", e)

        # Step 2: Maps
        try:
            count = self._collect_maps()
            summary["maps"] = count
        except Exception as e:
            summary["errors"].append(f"Maps: {e}")
            logger.error("Failed to collect maps: %s", e)

        # Step 3: Analytics reference data
        try:
            count = self._collect_analytics_reference()
            summary["analytics_reference"] = count
        except Exception as e:
            summary["errors"].append(f"Analytics reference: {e}")
            logger.error("Failed to collect analytics reference: %s", e)

        # Step 4: Analytics config
        try:
            count = self._collect_analytics_config()
            summary["analytics_config"] = count
        except Exception as e:
            summary["errors"].append(f"Analytics config: {e}")
            logger.error("Failed to collect analytics config: %s", e)

        # Step 5: Export to game store
        try:
            count = self._export_to_game()
            summary["game_exports"] = count
        except Exception as e:
            summary["errors"].append(f"Game export: {e}")
            logger.error("Failed to export to game: %s", e)

        # Step 6: Export to web store
        try:
            count = self._export_to_web()
            summary["web_exports"] = count
        except Exception as e:
            summary["errors"].append(f"Web export: {e}")
            logger.error("Failed to export to web: %s", e)

        logger.info("Data collection complete: %s", summary)
        return summary

    def _collect_game_definitions(self) -> int:
        """Collect all game definitions from Defs/."""
        count = 0

        # Agents
        agents_file = DEFS_PATH / "agents" / "agents.json"
        if agents_file.exists():
            agents = load_json(agents_file)
            for agent in agents:
                agent["data_domain"] = "agents"
                self.ingest.ingest(
                    source_system=SourceSystem.GAME,
                    payload_type=PayloadType.GAME_DEFINITION,
                    payload=agent,
                    ingested_by="data_collection_service",
                    target_project="game",
                )
                count += 1
            self._log("agents", len(agents))

        # Weapons
        weapons_file = DEFS_PATH / "weapons" / "weapons.json"
        if weapons_file.exists():
            weapons = load_json(weapons_file)
            for weapon in weapons:
                weapon["data_domain"] = "weapons"
                self.ingest.ingest(
                    source_system=SourceSystem.GAME,
                    payload_type=PayloadType.GAME_DEFINITION,
                    payload=weapon,
                    ingested_by="data_collection_service",
                    target_project="game",
                )
                count += 1
            self._log("weapons", len(weapons))

        # Utilities — CS grenades
        cs_grenades_file = DEFS_PATH / "utilities" / "cs_grenades.json"
        if cs_grenades_file.exists():
            grenades = load_json(cs_grenades_file)
            if isinstance(grenades, list):
                for grenade in grenades:
                    grenade["data_domain"] = "utilities"
                    self.ingest.ingest(
                        source_system=SourceSystem.GAME,
                        payload_type=PayloadType.GAME_DEFINITION,
                        payload=grenade,
                        ingested_by="data_collection_service",
                        target_project="game",
                    )
                    count += 1
            self._log("cs_grenades", count)

        # Utilities — VAL abilities
        val_abilities_file = DEFS_PATH / "utilities" / "val_abilities.json"
        if val_abilities_file.exists():
            abilities = load_json(val_abilities_file)
            if isinstance(abilities, list):
                for ability in abilities:
                    ability["data_domain"] = "utilities"
                    self.ingest.ingest(
                        source_system=SourceSystem.GAME,
                        payload_type=PayloadType.GAME_DEFINITION,
                        payload=ability,
                        ingested_by="data_collection_service",
                        target_project="game",
                    )
                    count += 1
            self._log("val_abilities", count)

        # Rulesets
        rulesets_file = DEFS_PATH / "rulesets" / "rulesets.json"
        if rulesets_file.exists():
            rulesets = load_json(rulesets_file)
            if isinstance(rulesets, list):
                for ruleset in rulesets:
                    ruleset["data_domain"] = "rulesets"
                    self.ingest.ingest(
                        source_system=SourceSystem.GAME,
                        payload_type=PayloadType.GAME_DEFINITION,
                        payload=ruleset,
                        ingested_by="data_collection_service",
                        target_project="game",
                    )
                    count += 1
            elif isinstance(rulesets, dict):
                rulesets["data_domain"] = "rulesets"
                self.ingest.ingest(
                    source_system=SourceSystem.GAME,
                    payload_type=PayloadType.GAME_DEFINITION,
                    payload=rulesets,
                    ingested_by="data_collection_service",
                    target_project="game",
                )
                count += 1
            self._log("rulesets", 1)

        return count

    def _collect_maps(self) -> int:
        """Collect all map definitions from maps/."""
        count = 0
        if MAPS_PATH.exists():
            for map_file in MAPS_PATH.glob("*.json"):
                map_data = load_json(map_file)
                map_data["data_domain"] = "maps"
                if "id" not in map_data:
                    map_data["id"] = map_file.stem
                self.ingest.ingest(
                    source_system=SourceSystem.GAME,
                    payload_type=PayloadType.GAME_DEFINITION,
                    payload=map_data,
                    ingested_by="data_collection_service",
                    target_project="game",
                )
                count += 1
            self._log("maps", count)
        return count

    def _collect_analytics_reference(self) -> int:
        """Collect analytics seed/reference data."""
        count = 0

        # Role baselines YAML
        baselines_file = SEED_DATA_PATH / "role_baselines.yaml"
        if baselines_file.exists():
            baselines = load_yaml(baselines_file)
            self.ingest.ingest(
                source_system=SourceSystem.ANALYTICS,
                payload_type=PayloadType.GAME_DEFINITION,
                payload={"id": "role_baselines", "data_domain": "role_baselines", **baselines},
                ingested_by="data_collection_service",
                target_project="both",
            )
            count += 1
            self._log("role_baselines", 1)

        return count

    def _collect_analytics_config(self) -> int:
        """Collect analytics configuration files."""
        count = 0
        if CONFIG_PATH.exists():
            for config_file in CONFIG_PATH.glob("*.json"):
                config_data = load_json(config_file)
                self.ingest.ingest(
                    source_system=SourceSystem.ANALYTICS,
                    payload_type=PayloadType.GAME_DEFINITION,
                    payload={"id": config_file.stem, "data_domain": "analytics_config", **config_data} if isinstance(config_data, dict) else {"id": config_file.stem, "data_domain": "analytics_config", "data": config_data},
                    ingested_by="data_collection_service",
                    target_project="both",
                )
                count += 1

            for config_file in CONFIG_PATH.glob("*.yaml"):
                config_data = load_yaml(config_file)
                self.ingest.ingest(
                    source_system=SourceSystem.ANALYTICS,
                    payload_type=PayloadType.GAME_DEFINITION,
                    payload={"id": config_file.stem, "data_domain": "analytics_config", **config_data} if isinstance(config_data, dict) else {"id": config_file.stem, "data_domain": "analytics_config", "data": config_data},
                    ingested_by="data_collection_service",
                    target_project="both",
                )
                count += 1

            self._log("analytics_config", count)
        return count

    def _export_to_game(self) -> int:
        """Export validated staging data to game data store."""
        pending = self.ingest.get_pending(target_project="game")
        count = 0
        for record in pending:
            if record.payload.get("data_domain") in ("agents", "weapons", "utilities", "rulesets", "maps"):
                self.game_export.export_definitions(
                    data_domain=record.payload["data_domain"],
                    definitions=[record.payload],
                    source_staging_id=record.ingest_id,
                )
                self.ingest.mark_exported(record.ingest_id, "game")
                count += 1
        return count

    def _export_to_web(self) -> int:
        """Export validated staging data to web data store (with firewall)."""
        pending = self.ingest.get_pending(target_project="web")
        count = 0
        player_records: List[Dict[str, Any]] = []

        for record in pending:
            if record.payload_type == PayloadType.PLAYER_STAT:
                player_records.append(record.payload)
                self.ingest.mark_exported(record.ingest_id, "web")
                count += 1

        if player_records:
            self.web_export.export_player_stats(player_records)

        return count

    def get_collection_log(self) -> List[Dict[str, Any]]:
        """Return the collection activity log."""
        return list(self._collection_log)

    def get_system_status(self) -> Dict[str, Any]:
        """Return overall system status."""
        return {
            "staging_queue": self.ingest.get_stats(),
            "game_store_count": len(self.game_export.get_active_definitions("agent_def"))
                + len(self.game_export.get_active_definitions("weapon_def"))
                + len(self.game_export.get_active_definitions("utility_def"))
                + len(self.game_export.get_active_definitions("map_def")),
            "web_store_count": len(self.web_export.get_verified_records()),
            "collection_log_entries": len(self._collection_log),
        }

    def _log(self, source: str, count: int) -> None:
        """Log a collection operation."""
        self._collection_log.append({
            "source": source,
            "records_collected": count,
            "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        })


# ============================================================================
# CLI entry point — run data collection from command line
# ============================================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    service = DataCollectionService()
    result = service.collect_all()
    print("\n=== DATA COLLECTION SUMMARY ===")
    for key, value in result.items():
        print(f"  {key}: {value}")
    print("\n=== SYSTEM STATUS ===")
    status = service.get_system_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
