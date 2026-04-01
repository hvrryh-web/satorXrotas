#!/usr/bin/env python3
"""
Axiom Esports Database Seeder
=============================
Idempotent seeding script for players and matches data.
Respects the 37-field KCRITR schema and dual-storage protocol.

Usage:
    python seed_database.py [--reset] [--dry-run]

Environment:
    DATABASE_URL - PostgreSQL connection string (required for cloud)
    Or local defaults if running within Docker network
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid5

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / ".." / "api" / "src"))

try:
    import asyncpg
except ImportError:
    print("Error: asyncpg not installed. Run: pip install asyncpg")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
NAMESPACE_SEED = UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # DNS namespace for UUIDv5
DATA_DIR = Path(__file__).parent.parent.parent.parent / "website" / "data"
MAPS = ["Ascent", "Bind", "Haven", "Pearl", "Icebox", "Breeze", "Fracture", "Lotus", "Sunset"]


def generate_player_uuid(player_id: str) -> UUID:
    """Generate deterministic UUID from player_id."""
    return uuid5(NAMESPACE_SEED, f"player:{player_id}")


def load_json_data(filename: str) -> list[dict]:
    """Load JSON data from website/data directory."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        logger.error(f"Data file not found: {filepath}")
        return []
    
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def transform_player_to_performance(player: dict, match_idx: int = 0) -> dict:
    """
    Transform website player data to player_performance schema.
    Maps 13 fields from JSON to 37-field KCRITR schema.
    """
    # Generate deterministic UUID
    player_uuid = generate_player_uuid(player["player_id"])
    
    # Distribute players across maps for variety
    map_name = MAPS[hash(player["player_id"]) % len(MAPS)]
    
    # Generate a synthetic match_id for seed data
    match_id = f"seed_{match_idx % 10:03d}"
    
    # Current timestamp for realworld_time
    realworld_time = datetime.now(timezone.utc)
    
    # Transform fields
    return {
        # Identity (5 fields)
        "player_id": player_uuid,
        "name": player["name"],
        "team": player["team"],
        "region": player["region"],
        "role": player["role"],
        
        # Performance metrics (5 fields)
        "kills": player.get("kills"),
        "deaths": player.get("deaths"),
        "acs": player.get("acs"),
        "adr": player.get("adr"),
        "kast_pct": player.get("kast_pct"),
        
        # RAR Metrics (4 fields) - calculated defaults
        "role_adjusted_value": None,
        "replacement_level": None,
        "rar_score": None,
        "investment_grade": None,
        
        # Extended performance (10 fields)
        "headshot_pct": player.get("hs_pct"),
        "first_blood": player.get("first_bloods"),
        "clutch_wins": player.get("clutch_wins"),
        "agent": None,
        "economy_rating": None,
        "adjusted_kill_value": None,
        "sim_rating": player.get("rating"),
        "age": None,
        "peak_age_estimate": None,
        "career_stage": None,
        
        # Match context (5 fields)
        "match_id": match_id,
        "map_name": map_name,
        "tournament": "Seed Data Tournament",
        "patch_version": "v1.0",
        "realworld_time": realworld_time,
        
        # Data provenance (8 fields)
        "data_source": "manual_seed",
        "extraction_timestamp": realworld_time,
        "checksum_sha256": None,
        "confidence_tier": 100.00,
        "separation_flag": 0,  # Raw data
        "partner_datapoint_ref": None,
        "reconstruction_notes": "Initial seed data from website/data/players.json",
    }


def transform_match_to_web_store(match: dict) -> dict:
    """Transform website match data to web_data_store."""
    return {
        "data_type": "match_summary",
        "data_key": match["match_id"],
        "data_version": "v1",
        "payload": json.dumps(match),
        "source_staging_id": None,
        "firewall_verified": True,
    }


async def insert_player_performance(conn: asyncpg.Connection, player_data: dict) -> bool:
    """Insert or update player performance record (idempotent)."""
    query = """
        INSERT INTO player_performance (
            player_id, name, team, region, role,
            kills, deaths, acs, adr, kast_pct,
            role_adjusted_value, replacement_level, rar_score, investment_grade,
            headshot_pct, first_blood, clutch_wins, agent, economy_rating,
            adjusted_kill_value, sim_rating, age, peak_age_estimate, career_stage,
            match_id, map_name, tournament, patch_version, realworld_time,
            data_source, extraction_timestamp, checksum_sha256, confidence_tier,
            separation_flag, partner_datapoint_ref, reconstruction_notes
        ) VALUES (
            $1, $2, $3, $4, $5,
            $6, $7, $8, $9, $10,
            $11, $12, $13, $14,
            $15, $16, $17, $18, $19,
            $20, $21, $22, $23, $24,
            $25, $26, $27, $28, $29,
            $30, $31, $32, $33,
            $34, $35, $36
        )
        ON CONFLICT (player_id, match_id, map_name) 
        DO UPDATE SET
            name = EXCLUDED.name,
            team = EXCLUDED.team,
            region = EXCLUDED.region,
            role = EXCLUDED.role,
            kills = EXCLUDED.kills,
            deaths = EXCLUDED.deaths,
            acs = EXCLUDED.acs,
            adr = EXCLUDED.adr,
            kast_pct = EXCLUDED.kast_pct,
            sim_rating = EXCLUDED.sim_rating,
            headshot_pct = EXCLUDED.headshot_pct,
            first_blood = EXCLUDED.first_blood,
            clutch_wins = EXCLUDED.clutch_wins,
            extraction_timestamp = EXCLUDED.extraction_timestamp,
            reconstruction_notes = EXCLUDED.reconstruction_notes
        RETURNING record_id
    """
    
    try:
        record_id = await conn.fetchval(query, *[
            player_data["player_id"],
            player_data["name"],
            player_data["team"],
            player_data["region"],
            player_data["role"],
            player_data["kills"],
            player_data["deaths"],
            player_data["acs"],
            player_data["adr"],
            player_data["kast_pct"],
            player_data["role_adjusted_value"],
            player_data["replacement_level"],
            player_data["rar_score"],
            player_data["investment_grade"],
            player_data["headshot_pct"],
            player_data["first_blood"],
            player_data["clutch_wins"],
            player_data["agent"],
            player_data["economy_rating"],
            player_data["adjusted_kill_value"],
            player_data["sim_rating"],
            player_data["age"],
            player_data["peak_age_estimate"],
            player_data["career_stage"],
            player_data["match_id"],
            player_data["map_name"],
            player_data["tournament"],
            player_data["patch_version"],
            player_data["realworld_time"],
            player_data["data_source"],
            player_data["extraction_timestamp"],
            player_data["checksum_sha256"],
            player_data["confidence_tier"],
            player_data["separation_flag"],
            player_data["partner_datapoint_ref"],
            player_data["reconstruction_notes"],
        ])
        return record_id is not None
    except Exception as e:
        logger.error(f"Failed to insert player {player_data['name']}: {e}")
        return False


async def insert_web_match(conn: asyncpg.Connection, match_data: dict) -> bool:
    """Insert or update web match record (idempotent)."""
    query = """
        INSERT INTO web_data_store (
            data_type, data_key, data_version, payload,
            source_staging_id, firewall_verified
        ) VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (data_type, data_key, data_version)
        DO UPDATE SET
            payload = EXCLUDED.payload,
            firewall_verified = EXCLUDED.firewall_verified,
            exported_at = NOW()
        RETURNING web_data_id
    """
    
    try:
        web_data_id = await conn.fetchval(query, *[
            match_data["data_type"],
            match_data["data_key"],
            match_data["data_version"],
            match_data["payload"],
            match_data["source_staging_id"],
            match_data["firewall_verified"],
        ])
        return web_data_id is not None
    except Exception as e:
        logger.error(f"Failed to insert match {match_data['data_key']}: {e}")
        return False


async def seed_players(conn: asyncpg.Connection, dry_run: bool = False) -> int:
    """Seed players data from website/data/players.json."""
    players = load_json_data("players.json")
    if not players:
        logger.warning("No players data found")
        return 0
    
    logger.info(f"Found {len(players)} players to seed")
    
    if dry_run:
        logger.info("DRY RUN: Would insert/update players:")
        for i, player in enumerate(players):
            transformed = transform_player_to_performance(player, i)
            logger.info(f"  - {transformed['name']} ({transformed['player_id']}) on {transformed['map_name']}")
        return len(players)
    
    success_count = 0
    for i, player in enumerate(players):
        transformed = transform_player_to_performance(player, i)
        if await insert_player_performance(conn, transformed):
            success_count += 1
            logger.debug(f"Inserted/updated player: {transformed['name']}")
    
    logger.info(f"Successfully seeded {success_count}/{len(players)} players")
    return success_count


async def seed_matches(conn: asyncpg.Connection, dry_run: bool = False) -> int:
    """Seed matches data from website/data/matches.json."""
    matches = load_json_data("matches.json")
    if not matches:
        logger.warning("No matches data found")
        return 0
    
    logger.info(f"Found {len(matches)} matches to seed")
    
    if dry_run:
        logger.info("DRY RUN: Would insert/update matches:")
        for match in matches:
            logger.info(f"  - {match['match_id']}: {match['team_a']} vs {match['team_b']}")
        return len(matches)
    
    success_count = 0
    for match in matches:
        transformed = transform_match_to_web_store(match)
        if await insert_web_match(conn, transformed):
            success_count += 1
            logger.debug(f"Inserted/updated match: {match['match_id']}")
    
    logger.info(f"Successfully seeded {success_count}/{len(matches)} matches")
    return success_count


async def verify_seed(conn: asyncpg.Connection) -> dict[str, int]:
    """Verify seed data was inserted correctly."""
    results = {}
    
    # Count player_performance records
    row = await conn.fetchrow("SELECT COUNT(*) as count FROM player_performance")
    results["player_performance_count"] = row["count"]
    
    # Count web_data_store match records
    row = await conn.fetchrow(
        "SELECT COUNT(*) as count FROM web_data_store WHERE data_type = 'match_summary'"
    )
    results["match_summary_count"] = row["count"]
    
    # Count distinct players
    row = await conn.fetchrow("SELECT COUNT(DISTINCT player_id) as count FROM player_performance")
    results["distinct_players"] = row["count"]
    
    # Count distinct teams
    row = await conn.fetchrow("SELECT COUNT(DISTINCT team) as count FROM player_performance")
    results["distinct_teams"] = row["count"]
    
    return results


async def clear_seed_data(conn: asyncpg.Connection) -> None:
    """Clear seed data (for reset)."""
    logger.warning("Clearing seed data...")
    
    await conn.execute("DELETE FROM player_performance WHERE data_source = 'manual_seed'")
    await conn.execute("DELETE FROM web_data_store WHERE data_type = 'match_summary'")
    
    logger.info("Seed data cleared")


async def get_database_url() -> str:
    """Get database URL from environment or use local defaults."""
    # Check for explicit DATABASE_URL
    if url := os.getenv("DATABASE_URL"):
        return url
    
    # Build from components for local development
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "axiom_esports")
    user = os.getenv("POSTGRES_USER", "axiom")
    password = os.getenv("POSTGRES_PASSWORD", "changeme")
    
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


async def main():
    parser = argparse.ArgumentParser(description="Seed Axiom Esports database")
    parser.add_argument("--reset", action="store_true", help="Clear existing seed data first")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without inserting")
    parser.add_argument("--players-only", action="store_true", help="Only seed players")
    parser.add_argument("--matches-only", action="store_true", help="Only seed matches")
    args = parser.parse_args()
    
    # Get database URL
    database_url = await get_database_url()
    
    if args.dry_run:
        logger.info("DRY RUN MODE: No changes will be made")
    
    logger.info(f"Connecting to database...")
    
    try:
        conn = await asyncpg.connect(database_url)
        logger.info("Connected successfully")
        
        # Verify schema exists
        try:
            await conn.fetchrow("SELECT 1 FROM player_performance LIMIT 1")
        except asyncpg.UndefinedTableError:
            logger.error("Schema not initialized. Run migrations first!")
            await conn.close()
            sys.exit(1)
        
        # Clear data if requested
        if args.reset and not args.dry_run:
            await clear_seed_data(conn)
        
        # Seed data
        total_seeded = 0
        
        if not args.matches_only:
            total_seeded += await seed_players(conn, args.dry_run)
        
        if not args.players_only:
            total_seeded += await seed_matches(conn, args.dry_run)
        
        # Verify
        if not args.dry_run:
            stats = await verify_seed(conn)
            logger.info("Seed verification:")
            for key, value in stats.items():
                logger.info(f"  {key}: {value}")
        
        await conn.close()
        
        if args.dry_run:
            logger.info(f"DRY RUN complete. Would seed {total_seeded} records.")
        else:
            logger.info(f"Seeding complete. Total records: {total_seeded}")
        
        return 0
        
    except asyncpg.InvalidPasswordError:
        logger.error("Invalid database password")
        return 1
    except asyncpg.CannotConnectNowError:
        logger.error("Cannot connect to database. Is it running?")
        return 1
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
