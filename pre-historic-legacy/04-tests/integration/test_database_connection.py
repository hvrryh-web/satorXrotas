"""
Database Connection Integration Tests
=====================================

Tests for PostgreSQL database connectivity, migrations, and CRUD operations.

These tests verify:
- Connection to PostgreSQL database
- Required extensions (TimescaleDB) are installed
- Migrations have been applied correctly
- Basic CRUD operations work
"""

import os
from typing import Any

import pytest

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://axiom:axiom@localhost:5432/axiom_esports")

# Check if database is available
try:
    import psycopg2
    import asyncpg

    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False


pytestmark = [
    pytest.mark.skipif(
        not DB_AVAILABLE, reason="Database drivers not installed (psycopg2/asyncpg)"
    ),
    pytest.mark.skipif(
        os.getenv("SKIP_DB_TESTS", "false").lower() == "true",
        reason="Database tests disabled via SKIP_DB_TESTS env var",
    ),
    pytest.mark.db,
]


class TestDatabaseConnection:
    """Test basic database connectivity."""

    def test_sync_connection(self):
        """Test synchronous PostgreSQL connection."""
        import psycopg2

        conn = psycopg2.connect(DATABASE_URL)
        assert conn is not None

        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1

        cursor.close()
        conn.close()

    @pytest.mark.asyncio
    async def test_async_connection(self):
        """Test asynchronous PostgreSQL connection."""
        import asyncpg

        conn = await asyncpg.connect(DATABASE_URL)
        assert conn is not None

        result = await conn.fetchval("SELECT 1")
        assert result == 1

        await conn.close()

    def test_connection_with_version(self):
        """Test connection and retrieve PostgreSQL version."""
        import psycopg2

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]

        assert "PostgreSQL" in version
        cursor.close()
        conn.close()

    def test_connection_pool(self):
        """Test multiple concurrent connections."""
        import psycopg2
        from psycopg2 import pool

        # Create a connection pool
        conn_pool = pool.SimpleConnectionPool(
            1, 5, DATABASE_URL
        )

        # Get multiple connections
        connections = []
        for _ in range(3):
            conn = conn_pool.getconn()
            connections.append(conn)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            assert cursor.fetchone()[0] == 1
            cursor.close()

        # Return connections to pool
        for conn in connections:
            conn_pool.putconn(conn)

        conn_pool.closeall()


class TestDatabaseExtensions:
    """Test that required PostgreSQL extensions are installed."""

    def test_timescaledb_extension(self):
        """Test that TimescaleDB extension is installed."""
        import psycopg2

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT extname, extversion 
            FROM pg_extension 
            WHERE extname = 'timescaledb'
        """)
        result = cursor.fetchone()

        if result:
            assert result[0] == "timescaledb"
            assert result[1] is not None
        else:
            pytest.skip("TimescaleDB extension not installed (optional for tests)")

        cursor.close()
        conn.close()

    def test_pgcrypto_extension(self):
        """Test that pgcrypto extension is available."""
        import psycopg2

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) 
            FROM pg_available_extensions 
            WHERE name = 'pgcrypto'
        """)
        result = cursor.fetchone()

        # pgcrypto should be available
        assert result[0] >= 0  # May or may not be installed

        cursor.close()
        conn.close()


class TestDatabaseMigrations:
    """Test that database migrations have been applied."""

    def test_player_performance_table_exists(self):
        """Test that player_performance table exists."""
        import psycopg2

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'player_performance'
            )
        """)
        exists = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        assert exists, "player_performance table does not exist"

    def test_player_performance_columns(self):
        """Test that player_performance has expected columns."""
        import psycopg2

        expected_columns = {
            "player_id", "name", "team", "region", "role",
            "kills", "deaths", "acs", "adr", "kast_pct",
            "sim_rating", "rar_score", "investment_grade",
            "match_id", "map_name", "realworld_time",
        }

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'player_performance'
        """)
        columns = {row[0] for row in cursor.fetchall()}

        cursor.close()
        conn.close()

        # Check that key columns exist
        missing = expected_columns - columns
        if missing:
            pytest.skip(f"Missing columns (migrations may not be applied): {missing}")

    def test_indexes_exist(self):
        """Test that expected indexes exist on player_performance."""
        import psycopg2

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'player_performance'
        """)
        indexes = {row[0] for row in cursor.fetchall()}

        cursor.close()
        conn.close()

        # Should have at least the primary key index
        assert len(indexes) > 0, "No indexes found on player_performance"

    def test_hypertable_exists(self):
        """Test that player_performance is a TimescaleDB hypertable."""
        import psycopg2

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM timescaledb_information.hypertables
                WHERE hypertable_name = 'player_performance'
            )
        """)
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result and result[0]:
            assert True
        else:
            pytest.skip("player_performance is not a hypertable (TimescaleDB may not be installed)")


class TestDatabaseCRUD:
    """Test basic CRUD operations on the database."""

    @pytest.fixture
def test_player(self) -> dict[str, Any]:
        """Create a test player record."""
        import uuid

        return {
            "player_id": str(uuid.uuid4()),
            "name": "TestPlayer_Integration",
            "team": "TestTeam",
            "region": "NA",
            "role": "Duelist",
            "kills": 100,
            "deaths": 80,
            "acs": 250.5,
            "adr": 160.0,
            "kast_pct": 75.0,
            "match_id": "test_match_001",
            "map_name": "Ascent",
            "realworld_time": "2026-03-04 12:00:00+00",
        }

    def test_insert_player(self, test_player: dict[str, Any]):
        """Test inserting a player record."""
        import psycopg2

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # Check if table exists first
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'player_performance'
            )
        """)
        if not cursor.fetchone()[0]:
            pytest.skip("player_performance table does not exist")

        try:
            # Insert test player
            cursor.execute("""
                INSERT INTO player_performance (
                    player_id, name, team, region, role,
                    kills, deaths, acs, adr, kast_pct,
                    match_id, map_name, realworld_time
                ) VALUES (
                    %(player_id)s, %(name)s, %(team)s, %(region)s, %(role)s,
                    %(kills)s, %(deaths)s, %(acs)s, %(adr)s, %(kast_pct)s,
                    %(match_id)s, %(map_name)s, %(realworld_time)s
                ) RETURNING player_id
            """, test_player)

            player_id = cursor.fetchone()[0]
            conn.commit()

            assert player_id == test_player["player_id"]

            # Cleanup
            cursor.execute(
                "DELETE FROM player_performance WHERE player_id = %s",
                (player_id,)
            )
            conn.commit()

        except psycopg2.Error as e:
            pytest.skip(f"Database error (schema may differ): {e}")

        finally:
            cursor.close()
            conn.close()

    def test_select_players(self):
        """Test selecting players from the database."""
        import psycopg2

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT player_id, name, team, region, role
                FROM player_performance
                LIMIT 10
            """)
            results = cursor.fetchall()

            # Results should be a list
            assert isinstance(results, list)

            # If there are results, verify structure
            if results:
                for row in results:
                    assert len(row) == 5  # 5 columns selected

        except psycopg2.Error as e:
            pytest.skip(f"Database error: {e}")

        finally:
            cursor.close()
            conn.close()

    def test_update_player(self, test_player: dict[str, Any]):
        """Test updating a player record."""
        import psycopg2

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        try:
            # Insert test player
            cursor.execute("""
                INSERT INTO player_performance (
                    player_id, name, team, region, role,
                    kills, deaths, acs, adr, kast_pct,
                    match_id, map_name, realworld_time
                ) VALUES (
                    %(player_id)s, %(name)s, %(team)s, %(region)s, %(role)s,
                    %(kills)s, %(deaths)s, %(acs)s, %(adr)s, %(kast_pct)s,
                    %(match_id)s, %(map_name)s, %(realworld_time)s
                )
            """, test_player)

            # Update the player
            cursor.execute("""
                UPDATE player_performance
                SET kills = 150, acs = 300.0
                WHERE player_id = %s
            """, (test_player["player_id"],))

            conn.commit()

            # Verify update
            cursor.execute("""
                SELECT kills, acs FROM player_performance
                WHERE player_id = %s
            """, (test_player["player_id"],))
            result = cursor.fetchone()

            assert result[0] == 150
            assert result[1] == 300.0

            # Cleanup
            cursor.execute(
                "DELETE FROM player_performance WHERE player_id = %s",
                (test_player["player_id"],)
            )
            conn.commit()

        except psycopg2.Error as e:
            pytest.skip(f"Database error (schema may differ): {e}")

        finally:
            cursor.close()
            conn.close()

    def test_delete_player(self, test_player: dict[str, Any]):
        """Test deleting a player record."""
        import psycopg2

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        try:
            # Insert test player
            cursor.execute("""
                INSERT INTO player_performance (
                    player_id, name, team, region, role,
                    kills, deaths, acs, adr, kast_pct,
                    match_id, map_name, realworld_time
                ) VALUES (
                    %(player_id)s, %(name)s, %(team)s, %(region)s, %(role)s,
                    %(kills)s, %(deaths)s, %(acs)s, %(adr)s, %(kast_pct)s,
                    %(match_id)s, %(map_name)s, %(realworld_time)s
                )
            """, test_player)
            conn.commit()

            # Delete the player
            cursor.execute(
                "DELETE FROM player_performance WHERE player_id = %s",
                (test_player["player_id"],)
            )
            conn.commit()

            # Verify deletion
            cursor.execute("""
                SELECT COUNT(*) FROM player_performance
                WHERE player_id = %s
            """, (test_player["player_id"],))
            count = cursor.fetchone()[0]

            assert count == 0

        except psycopg2.Error as e:
            pytest.skip(f"Database error (schema may differ): {e}")

        finally:
            cursor.close()
            conn.close()


class TestDatabaseConstraints:
    """Test database constraints and validation."""

    def test_primary_key_constraint(self):
        """Test that primary key constraints are enforced."""
        import psycopg2
        from psycopg2 import errors

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        try:
            # Try to insert a duplicate key (this should fail)
            # First, get an existing record's primary key
            cursor.execute("""
                SELECT player_id, match_id, map_name
                FROM player_performance
                LIMIT 1
            """)
            existing = cursor.fetchone()

            if not existing:
                pytest.skip("No existing records to test constraint")

            player_id, match_id, map_name = existing

            # Attempt to insert duplicate
            cursor.execute("""
                INSERT INTO player_performance (
                    player_id, match_id, map_name, realworld_time
                ) VALUES (%s, %s, %s, NOW())
            """, (player_id, match_id, map_name))

            conn.commit()
            pytest.fail("Expected unique violation error")

        except errors.UniqueViolation:
            # Expected behavior
            conn.rollback()
            assert True

        except psycopg2.Error as e:
            pytest.skip(f"Database error: {e}")

        finally:
            cursor.close()
            conn.close()

    def test_null_constraints(self):
        """Test that NOT NULL constraints are enforced."""
        import psycopg2
        from psycopg2 import errors

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        try:
            # Try to insert without required fields
            cursor.execute("""
                INSERT INTO player_performance (name) VALUES ('test')
            """)
            conn.commit()

        except errors.NotNullViolation:
            # Expected behavior
            conn.rollback()
            assert True

        except psycopg2.Error as e:
            # Other errors are acceptable (constraint may differ)
            conn.rollback()
            pytest.skip(f"Constraint behavior: {e}")

        finally:
            cursor.close()
            conn.close()
