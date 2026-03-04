"""
Partitioned storage manager for dual-game data.
Handles game-specific routing and cross-game queries.
"""

import asyncpg
from typing import Optional, List, Dict, Literal
from datetime import date

GameType = Literal['cs', 'valorant']


class PartitionedStorage:
    """
    Manages partitioned data storage for CS and Valorant.
    
    Automatically routes operations to correct partition based on game type.
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
    
    async def insert_match(
        self,
        game: GameType,
        source: str,
        source_id: str,
        match_data: Dict
    ) -> str:
        """Insert match into appropriate partition."""
        async with self.db_pool.acquire() as conn:
            match_id = await conn.fetchval(
                """
                SELECT insert_match(
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15
                )
                """,
                game,
                source,
                source_id,
                match_data.get('tournament_id'),
                match_data.get('match_date'),
                match_data.get('team_a_id'),
                match_data.get('team_b_id'),
                match_data.get('team_a_name'),
                match_data.get('team_b_name'),
                match_data.get('score_a', 0),
                match_data.get('score_b', 0),
                match_data.get('format'),
                match_data.get('epoch', 2),
                match_data.get('region'),
                match_data.get('checksum')
            )
            return str(match_id)
    
    async def get_matches(
        self,
        game: Optional[GameType] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        team_id: Optional[str] = None,
        tournament_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Query matches with automatic game filtering.
        
        If game is specified, queries only that partition.
        If game is None, queries both partitions.
        """
        async with self.db_pool.acquire() as conn:
            if game:
                # Query specific partition
                rows = await conn.fetch(
                    """
                    SELECT * FROM matches
                    WHERE game = $1
                      AND ($2::date IS NULL OR match_date >= $2)
                      AND ($3::date IS NULL OR match_date <= $3)
                      AND ($4::uuid IS NULL OR team_a_id = $4 OR team_b_id = $4)
                      AND ($5::uuid IS NULL OR tournament_id = $5)
                    ORDER BY match_date DESC
                    LIMIT $6
                    """,
                    game, start_date, end_date, team_id, tournament_id, limit
                )
            else:
                # Query all partitions
                rows = await conn.fetch(
                    """
                    SELECT * FROM matches
                    WHERE ($1::date IS NULL OR match_date >= $1)
                      AND ($2::date IS NULL OR match_date <= $2)
                      AND ($3::uuid IS NULL OR team_a_id = $3 OR team_b_id = $3)
                    ORDER BY match_date DESC
                    LIMIT $4
                    """,
                    start_date, end_date, team_id, limit
                )
            
            return [dict(row) for row in rows]
    
    async def get_game_stats(self) -> Dict:
        """Get storage statistics for both games."""
        async with self.db_pool.acquire() as conn:
            cs_stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as match_count,
                    COUNT(DISTINCT team_a_id) + COUNT(DISTINCT team_b_id) as team_count,
                    MAX(extracted_at) as last_update
                FROM matches_cs
                """
            )
            
            val_stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as match_count,
                    COUNT(DISTINCT team_a_id) + COUNT(DISTINCT team_b_id) as team_count,
                    MAX(extracted_at) as last_update
                FROM matches_valorant
                """
            )
            
            return {
                'cs': dict(cs_stats) if cs_stats else {},
                'valorant': dict(val_stats) if val_stats else {}
            }

    async def insert_player_performance(
        self,
        game: GameType,
        match_id: str,
        player_id: str,
        team_id: Optional[str],
        player_name: str,
        team_name: Optional[str],
        kills: int,
        deaths: int,
        assists: int,
        game_stats: Dict,
        match_date: date
    ) -> Optional[str]:
        """Insert player performance into appropriate partition."""
        async with self.db_pool.acquire() as conn:
            perf_id = await conn.fetchval(
                """
                SELECT insert_player_performance($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                """,
                game,
                match_id,
                player_id,
                team_id,
                player_name,
                team_name,
                kills,
                deaths,
                assists,
                game_stats,
                match_date
            )
            return str(perf_id) if perf_id else None

    async def get_player_performances(
        self,
        game: Optional[GameType] = None,
        player_id: Optional[str] = None,
        match_id: Optional[str] = None,
        team_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Query player performances with automatic game filtering.
        
        If game is specified, queries only that partition.
        If game is None, queries both partitions.
        """
        async with self.db_pool.acquire() as conn:
            if game:
                rows = await conn.fetch(
                    """
                    SELECT * FROM player_performance
                    WHERE game = $1
                      AND ($2::uuid IS NULL OR player_id = $2)
                      AND ($3::uuid IS NULL OR match_id = $3)
                      AND ($4::uuid IS NULL OR team_id = $4)
                      AND ($5::date IS NULL OR match_date >= $5)
                      AND ($6::date IS NULL OR match_date <= $6)
                    ORDER BY match_date DESC
                    LIMIT $7
                    """,
                    game, player_id, match_id, team_id, start_date, end_date, limit
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM player_performance
                    WHERE ($1::uuid IS NULL OR player_id = $1)
                      AND ($2::uuid IS NULL OR match_id = $2)
                      AND ($3::uuid IS NULL OR team_id = $3)
                      AND ($4::date IS NULL OR match_date >= $4)
                      AND ($5::date IS NULL OR match_date <= $5)
                    ORDER BY match_date DESC
                    LIMIT $6
                    """,
                    player_id, match_id, team_id, start_date, end_date, limit
                )
            
            return [dict(row) for row in rows]

    async def get_cs_player_stats(
        self,
        player_id: Optional[str] = None,
        min_matches: int = 5
    ) -> List[Dict]:
        """Get aggregated CS player statistics from materialized view."""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM player_career_stats_cs
                WHERE ($1::uuid IS NULL OR player_id = $1)
                  AND total_matches >= $2
                ORDER BY avg_rating DESC NULLS LAST
                """,
                player_id, min_matches
            )
            return [dict(row) for row in rows]

    async def get_valorant_player_stats(
        self,
        player_id: Optional[str] = None,
        min_matches: int = 5
    ) -> List[Dict]:
        """Get aggregated Valorant player statistics from materialized view."""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM player_career_stats_valorant
                WHERE ($1::uuid IS NULL OR player_id = $1)
                  AND total_matches >= $2
                ORDER BY avg_acs DESC NULLS LAST
                """,
                player_id, min_matches
            )
            return [dict(row) for row in rows]

    async def refresh_career_stats(self) -> None:
        """Refresh the career statistics materialized views."""
        async with self.db_pool.acquire() as conn:
            await conn.execute("SELECT refresh_career_stats()")

    async def get_storage_stats(self) -> List[Dict]:
        """Get storage statistics for partitioned tables."""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM storage_stats")
            return [dict(row) for row in rows]

    async def get_data_freshness(self) -> List[Dict]:
        """Get data freshness for both games."""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM data_freshness")
            return [dict(row) for row in rows]


# Usage Examples
USAGE_EXAMPLES = """
# Example 1: Initialize storage with database pool
import asyncpg

pool = await asyncpg.create_pool(DATABASE_URL)
storage = PartitionedStorage(pool)

# Example 2: Insert a CS match
match_id = await storage.insert_match(
    game='cs',
    source='hltv',
    source_id='match-12345',
    match_data={
        'match_date': date(2024, 3, 15),
        'team_a_id': 'uuid-for-team-a',
        'team_b_id': 'uuid-for-team-b',
        'team_a_name': 'Team A',
        'team_b_name': 'Team B',
        'score_a': 16,
        'score_b': 14,
        'format': 'bo3',
        'epoch': 2,
        'region': 'EU',
        'checksum': 'sha256-hash'
    }
)

# Example 3: Insert player performance for Valorant
perf_id = await storage.insert_player_performance(
    game='valorant',
    match_id=match_id,
    player_id='player-uuid',
    team_id='team-uuid',
    player_name='PlayerName',
    team_name='TeamName',
    kills=25,
    deaths=15,
    assists=8,
    game_stats={
        'acs': 285.5,
        'adr': 165.2,
        'kast_pct': 78.5,
        'agent': 'Jett',
        'first_bloods': 4
    },
    match_date=date(2024, 3, 15)
)

# Example 4: Query matches by game
# Get only CS matches
cs_matches = await storage.get_matches(game='cs', limit=50)

# Get matches from both games
all_matches = await storage.get_matches(limit=100)

# Get matches for a specific team and date range
team_matches = await storage.get_matches(
    game='valorant',
    team_id='team-uuid',
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31)
)

# Example 5: Query player performances
performances = await storage.get_player_performances(
    game='cs',
    player_id='player-uuid',
    limit=50
)

# Example 6: Get aggregated career stats
cs_career_stats = await storage.get_cs_player_stats(min_matches=10)
val_career_stats = await storage.get_valorant_player_stats(min_matches=10)

# Example 7: Get storage statistics
storage_stats = await storage.get_storage_stats()
print(f"Table sizes: {storage_stats}")

# Example 8: Check data freshness
freshness = await storage.get_data_freshness()
for game in freshness:
    print(f"{game['game']}: Last extraction at {game['last_extraction']}")

# Example 9: Refresh materialized views (run periodically)
await storage.refresh_career_stats()

# Example 10: Get game statistics
stats = await storage.get_game_stats()
print(f"CS matches: {stats['cs']['match_count']}")
print(f"Valorant matches: {stats['valorant']['match_count']}")
"""

if __name__ == "__main__":
    print("PartitionedStorage module for dual-game data storage")
    print("=" * 50)
    print(USAGE_EXAMPLES)
