"""
Axiom Esports Database Connection Manager
=========================================
Async PostgreSQL connection layer with:
- Environment-based configuration
- Connection pooling (optimized for free tier)
- Retry logic for cloud database connections
- Health check query
- Support for Supabase/Neon connection strings
- SSL mode configuration
"""

import logging
import os
import ssl
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import urlparse

try:
    import asyncpg
except ImportError:
    asyncpg = None

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration from environment variables."""
    
    database_url: str = ""
    host: str = "localhost"
    port: int = 5432
    database: str = "axiom_esports"
    user: str = "axiom"
    password: str = ""
    ssl_mode: str = "prefer"
    ssl_root_cert: Optional[str] = None
    pool_size: int = 5
    max_overflow: int = 2
    pool_timeout: int = 30
    command_timeout: int = 30
    max_retries: int = 5
    retry_delay: float = 2.0
    connect_timeout: int = 10
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        config = cls()
        
        if url := os.getenv("DATABASE_URL"):
            config.database_url = url
            parsed = urlparse(url)
            config.host = parsed.hostname or config.host
            config.port = parsed.port or config.port
            config.database = parsed.path.lstrip("/") or config.database
            config.user = parsed.username or config.user
            config.password = parsed.password or config.password
            
            if parsed.query:
                for param in parsed.query.split("&"):
                    if "=" in param:
                        key, value = param.split("=", 1)
                        if key == "sslmode":
                            config.ssl_mode = value
        else:
            config.host = os.getenv("POSTGRES_HOST", config.host)
            config.port = int(os.getenv("POSTGRES_PORT", config.port))
            config.database = os.getenv("POSTGRES_DB", config.database)
            config.user = os.getenv("POSTGRES_USER", config.user)
            config.password = os.getenv("POSTGRES_PASSWORD", config.password)
            config.database_url = (
                f"postgresql://{config.user}:{config.password}"
                f"@{config.host}:{config.port}/{config.database}"
            )
        
        config.ssl_mode = os.getenv("DB_SSL_MODE", config.ssl_mode)
        config.ssl_root_cert = os.getenv("DB_SSL_ROOT_CERT")
        config.pool_size = int(os.getenv("DB_POOL_SIZE", config.pool_size))
        config.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", config.max_overflow))
        config.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", config.pool_timeout))
        config.command_timeout = int(os.getenv("DB_QUERY_TIMEOUT", config.command_timeout))
        config.max_retries = int(os.getenv("DB_CONNECT_RETRY_ATTEMPTS", config.max_retries))
        config.retry_delay = float(os.getenv("DB_CONNECT_RETRY_DELAY", config.retry_delay))
        config.connect_timeout = int(os.getenv("DB_CONNECT_TIMEOUT", config.connect_timeout))
        
        return config
    
    def get_ssl_context(self) -> Optional[ssl.SSLContext]:
        if self.ssl_mode == "disable":
            return None
        
        if self.ssl_mode in ("require", "verify-ca", "verify-full"):
            context = ssl.create_default_context()
            if self.ssl_root_cert:
                context.load_verify_locations(self.ssl_root_cert)
            if self.ssl_mode == "require":
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            elif self.ssl_mode == "verify-ca":
                context.check_hostname = False
                context.verify_mode = ssl.CERT_REQUIRED
            elif self.ssl_mode == "verify-full":
                context.check_hostname = True
                context.verify_mode = ssl.CERT_REQUIRED
            return context
        return True


class Database:
    """Async PostgreSQL database manager with connection pooling."""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig.from_env()
        self.pool = None
        self._closed = True
    
    async def connect(self) -> "Database":
        if self.pool and not self._closed:
            return self
        
        if asyncpg is None:
            raise RuntimeError("asyncpg not installed. Run: pip install asyncpg")
        
        ssl_context = self.config.get_ssl_context()
        last_error = None
        
        for attempt in range(1, self.config.max_retries + 1):
            try:
                self.pool = await asyncpg.create_pool(
                    dsn=self.config.database_url,
                    min_size=self.config.pool_size,
                    max_size=self.config.pool_size + self.config.max_overflow,
                    command_timeout=self.config.command_timeout,
                    ssl=ssl_context,
                    host=self.config.host,
                    port=self.config.port,
                    database=self.config.database,
                    user=self.config.user,
                    password=self.config.password,
                    server_settings={"application_name": "axiom_esports_api", "jit": "off"},
                )
                self._closed = False
                logger.info(f"Database connected (pool: {self.config.pool_size})")
                return self
            except Exception as e:
                last_error = e
                logger.warning(f"Connection attempt {attempt} failed: {e}")
                if attempt < self.config.max_retries:
                    import asyncio
                    wait_time = self.config.retry_delay * (2 ** (attempt - 1))
                    await asyncio.sleep(wait_time)
        
        raise last_error or ConnectionError("Could not connect to database")
    
    async def disconnect(self) -> None:
        if self.pool and not self._closed:
            await self.pool.close()
            self._closed = True
            logger.info("Database disconnected")
    
    async def health_check(self) -> dict[str, Any]:
        import time
        if not self.pool or self._closed:
            return {"status": "disconnected", "latency_ms": None}
        
        start = time.perf_counter()
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                latency_ms = (time.perf_counter() - start) * 1000
                return {
                    "status": "healthy" if result == 1 else "unhealthy",
                    "latency_ms": round(latency_ms, 2),
                    "pool_size": self.pool.get_size(),
                    "pool_free": self.pool.get_idle_size(),
                }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    @asynccontextmanager
    async def transaction(self):
        if not self.pool:
            raise RuntimeError("Database not connected")
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                yield conn
    
    async def execute(self, query: str, *args) -> str:
        if not self.pool:
            raise RuntimeError("Database not connected")
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args) -> list:
        if not self.pool:
            raise RuntimeError("Database not connected")
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args):
        if not self.pool:
            raise RuntimeError("Database not connected")
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetchval(self, query: str, *args):
        if not self.pool:
            raise RuntimeError("Database not connected")
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)
    
    # Application queries
    async def get_player_record(self, player_id: str) -> Optional[dict]:
        from uuid import UUID
        try:
            player_uuid = UUID(player_id) if not isinstance(player_id, UUID) else player_id
        except ValueError:
            return None
        
        query = """
            SELECT player_id, name, team, region, role,
                   kills, deaths, acs, adr, kast_pct,
                   headshot_pct, first_blood, clutch_wins,
                   sim_rating, match_id, map_name, tournament
            FROM player_performance
            WHERE player_id = $1
            ORDER BY realworld_time DESC LIMIT 1
        """
        row = await self.fetchrow(query, player_uuid)
        return dict(row) if row else None
    
    async def get_player_list(self, region=None, role=None, min_maps=50,
                              grade=None, limit=50, offset=0):
        conditions = ["confidence_tier >= 90.0"]
        params = []
        param_idx = 1
        
        if region:
            conditions.append(f"region = ${param_idx}")
            params.append(region)
            param_idx += 1
        if role:
            conditions.append(f"role = ${param_idx}")
            params.append(role)
            param_idx += 1
        if grade:
            conditions.append(f"investment_grade = ${param_idx}")
            params.append(grade)
            param_idx += 1
        
        where_clause = " AND ".join(conditions)
        
        count_row = await self.fetchrow(
            f"SELECT COUNT(DISTINCT player_id) as total FROM player_performance WHERE {where_clause}",
            *params
        )
        total = count_row["total"] if count_row else 0
        
        query = f"""
            SELECT player_id, MAX(name) as name, MAX(team) as team,
                   MAX(region) as region, MAX(role) as role,
                   COUNT(DISTINCT match_id) as maps_played,
                   AVG(acs) as avg_acs, AVG(sim_rating) as avg_rating
            FROM player_performance
            WHERE {where_clause}
            GROUP BY player_id
            HAVING COUNT(DISTINCT match_id) >= ${param_idx}
            ORDER BY avg_rating DESC NULLS LAST
            LIMIT ${param_idx + 1} OFFSET ${param_idx + 2}
        """
        rows = await self.fetch(query, *(params + [min_maps, limit, offset]))
        return [dict(row) for row in rows], total
    
    async def get_match_record(self, match_id: str) -> Optional[dict]:
        query = """
            SELECT data_key, payload, exported_at
            FROM web_data_store
            WHERE data_type = 'match_summary'
            AND data_key = $1 AND firewall_verified = TRUE
            LIMIT 1
        """
        row = await self.fetchrow(query, match_id)
        if row:
            import json
            result = dict(row)
            result["payload"] = json.loads(result["payload"])
            return result
        return None
    
    async def get_sator_events(self, match_id: str, round_number: int) -> list:
        query = """
            SELECT event_id, player_id, event_type, round_number,
                   map_x, map_y, intensity
            FROM sator_events
            WHERE match_id = $1 AND round_number = $2
            ORDER BY tick
        """
        rows = await self.fetch(query, match_id, round_number)
        return [dict(row) for row in rows]
    
    async def get_arepo_markers(self, match_id: str, round_number: int) -> list:
        query = """
            SELECT marker_id, victim_id, killer_id, map_x, map_y,
                   weapon, is_multikill, is_clutch
            FROM arepo_markers
            WHERE match_id = $1 AND round_number = $2
        """
        rows = await self.fetch(query, match_id, round_number)
        return [dict(row) for row in rows]
    
    async def get_rotas_trails(self, match_id: str, round_number: int) -> list:
        query = """
            SELECT trail_id, player_id, tick_sequence,
                   x_sequence, y_sequence, direction_lr
            FROM rotas_trails
            WHERE match_id = $1 AND round_number = $2
        """
        rows = await self.fetch(query, match_id, round_number)
        return [dict(row) for row in rows]


# Legacy compatibility
_database_instance = None

async def get_db() -> Database:
    global _database_instance
    if _database_instance is None:
        _database_instance = Database()
        await _database_instance.connect()
    return _database_instance


async def close_db() -> None:
    global _database_instance
    if _database_instance:
        await _database_instance.disconnect()
        _database_instance = None


# Original function signatures for backward compatibility
DATABASE_URL = os.getenv("DATABASE_URL")


async def get_player_record(player_id: str) -> Optional[dict]:
    if not DATABASE_URL:
        logger.debug("DATABASE_URL not set - no live data")
        return None
    try:
        db = await get_db()
        return await db.get_player_record(player_id)
    except Exception as e:
        logger.warning(f"DB error: {e}")
        return None


async def get_player_list(region=None, role=None, min_maps=50,
                          grade=None, limit=50, offset=0):
    if not DATABASE_URL:
        return [], 0
    try:
        db = await get_db()
        return await db.get_player_list(region, role, min_maps, grade, limit, offset)
    except Exception as e:
        logger.warning(f"DB error: {e}")
        return [], 0


async def get_match_record(match_id: str) -> Optional[dict]:
    if not DATABASE_URL:
        return None
    try:
        db = await get_db()
        return await db.get_match_record(match_id)
    except Exception as e:
        logger.warning(f"DB error: {e}")
        return None


async def get_sator_events(match_id: str, round_number: int) -> list:
    if not DATABASE_URL:
        return []
    try:
        db = await get_db()
        return await db.get_sator_events(match_id, round_number)
    except Exception as e:
        logger.warning(f"DB error: {e}")
        return []


async def get_arepo_markers(match_id: str, round_number: int) -> list:
    if not DATABASE_URL:
        return []
    try:
        db = await get_db()
        return await db.get_arepo_markers(match_id, round_number)
    except Exception as e:
        logger.warning(f"DB error: {e}")
        return []


async def get_rotas_trails(match_id: str, round_number: int) -> list:
    if not DATABASE_URL:
        return []
    try:
        db = await get_db()
        return await db.get_rotas_trails(match_id, round_number)
    except Exception as e:
        logger.warning(f"DB error: {e}")
        return []
