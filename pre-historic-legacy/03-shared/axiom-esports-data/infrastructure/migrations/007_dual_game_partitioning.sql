-- Migration 007: Dual-Game Database Partitioning
-- Creates partitioned tables for concurrent CS and Valorant data storage

-- ============================================
-- 1. GAME TYPE ENUM
-- ============================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'game_type') THEN
        CREATE TYPE game_type AS ENUM ('cs', 'valorant');
    END IF;
END$$;

-- ============================================
-- 2. PARTITIONED MATCH TABLES
-- ============================================

-- Parent table for all matches
CREATE TABLE IF NOT EXISTS matches (
    id UUID DEFAULT gen_random_uuid(),
    game game_type NOT NULL,
    source VARCHAR(50) NOT NULL, -- hltv, vlr, etc.
    source_id VARCHAR(100) NOT NULL,
    
    -- Match identification
    tournament_id UUID,
    season_id UUID,
    match_date DATE NOT NULL,
    match_datetime TIMESTAMPTZ,
    
    -- Teams
    team_a_id UUID NOT NULL,
    team_b_id UUID NOT NULL,
    team_a_name VARCHAR(200),
    team_b_name VARCHAR(200),
    
    -- Results
    score_a SMALLINT DEFAULT 0,
    score_b SMALLINT DEFAULT 0,
    winner_team_id UUID,
    
    -- Metadata
    format VARCHAR(20), -- bo1, bo3, bo5
    status VARCHAR(20) DEFAULT 'scheduled', -- scheduled, live, completed
    epoch SMALLINT NOT NULL CHECK (epoch IN (1, 2, 3)),
    region VARCHAR(50),
    
    -- Extraction metadata
    extracted_at TIMESTAMPTZ DEFAULT NOW(),
    checksum VARCHAR(64),
    confidence_score DECIMAL(5,2),
    
    PRIMARY KEY (id, game), -- Include partition key
    UNIQUE (game, source, source_id)
) PARTITION BY LIST (game);

-- CS partition
CREATE TABLE IF NOT EXISTS matches_cs PARTITION OF matches
    FOR VALUES IN ('cs');

-- Valorant partition
CREATE TABLE IF NOT EXISTS matches_valorant PARTITION OF matches
    FOR VALUES IN ('valorant');

-- Indexes on parent (automatically applied to partitions)
CREATE INDEX IF NOT EXISTS idx_matches_date ON matches (match_date DESC);
CREATE INDEX IF NOT EXISTS idx_matches_tournament ON matches (tournament_id);
CREATE INDEX IF NOT EXISTS idx_matches_teams ON matches (team_a_id, team_b_id);
CREATE INDEX IF NOT EXISTS idx_matches_epoch ON matches (epoch, match_date);
CREATE INDEX IF NOT EXISTS idx_matches_source ON matches (source, source_id);

-- Convert to TimescaleDB hypertable for time-series optimization
SELECT create_hypertable('matches_cs', 'match_date', if_not_exists => TRUE);
SELECT create_hypertable('matches_valorant', 'match_date', if_not_exists => TRUE);

-- Set chunk size (1 week for matches)
SELECT set_chunk_time_interval('matches_cs', INTERVAL '7 days');
SELECT set_chunk_time_interval('matches_valorant', INTERVAL '7 days');

-- ============================================
-- 3. PARTITIONED PLAYER PERFORMANCE TABLES
-- ============================================

CREATE TABLE IF NOT EXISTS player_performance (
    id UUID DEFAULT gen_random_uuid(),
    game game_type NOT NULL,
    
    -- References
    match_id UUID NOT NULL,
    player_id UUID NOT NULL,
    team_id UUID,
    
    -- Player info
    player_name VARCHAR(200),
    team_name VARCHAR(200),
    
    -- Core stats (common to both games)
    kills SMALLINT DEFAULT 0,
    deaths SMALLINT DEFAULT 0,
    assists SMALLINT DEFAULT 0,
    
    -- Game-specific stats stored as JSONB
    game_stats JSONB,
    
    -- Metadata
    match_date DATE NOT NULL,
    extracted_at TIMESTAMPTZ DEFAULT NOW(),
    
    PRIMARY KEY (id, game)
) PARTITION BY LIST (game);

CREATE TABLE IF NOT EXISTS player_performance_cs PARTITION OF player_performance
    FOR VALUES IN ('cs');

CREATE TABLE IF NOT EXISTS player_performance_valorant PARTITION OF player_performance
    FOR VALUES IN ('valorant');

-- Indexes
CREATE INDEX IF NOT EXISTS idx_performance_player ON player_performance (player_id, match_date DESC);
CREATE INDEX IF NOT EXISTS idx_performance_match ON player_performance (match_id);
CREATE INDEX IF NOT EXISTS idx_performance_team ON player_performance (team_id);

-- Convert to hypertables
SELECT create_hypertable('player_performance_cs', 'match_date', if_not_exists => TRUE);
SELECT create_hypertable('player_performance_valorant', 'match_date', if_not_exists => TRUE);

-- ============================================
-- 4. GAME-SPECIFIC PLAYER STATS VIEWS
-- ============================================

-- CS Player Stats View
CREATE OR REPLACE VIEW cs_player_stats AS
SELECT 
    pp.*,
    (pp.game_stats->>'adr')::DECIMAL as adr,
    (pp.game_stats->>'kast')::DECIMAL as kast_pct,
    (pp.game_stats->>'rating')::DECIMAL as rating,
    (pp.game_stats->>'hs_pct')::DECIMAL as hs_pct,
    (pp.game_stats->>'first_kills')::SMALLINT as first_kills,
    (pp.game_stats->>'clutches_won')::SMALLINT as clutches_won,
    CASE WHEN pp.deaths > 0 THEN pp.kills::DECIMAL / pp.deaths ELSE pp.kills END as kdr
FROM player_performance pp
WHERE pp.game = 'cs';

-- Valorant Player Stats View
CREATE OR REPLACE VIEW valorant_player_stats AS
SELECT 
    pp.*,
    (pp.game_stats->>'acs')::DECIMAL as acs,
    (pp.game_stats->>'adr')::DECIMAL as adr,
    (pp.game_stats->>'kast_pct')::DECIMAL as kast_pct,
    (pp.game_stats->>'hs_pct')::DECIMAL as hs_pct,
    (pp.game_stats->>'first_bloods')::SMALLINT as first_bloods,
    (pp.game_stats->>'first_deaths')::SMALLINT as first_deaths,
    (pp.game_stats->>'agent')::VARCHAR as agent_played,
    CASE WHEN pp.deaths > 0 THEN pp.kills::DECIMAL / pp.deaths ELSE pp.kills END as kdr
FROM player_performance pp
WHERE pp.game = 'valorant';

-- ============================================
-- 5. TEAMS TABLES (Game-Specific)
-- ============================================

CREATE TABLE IF NOT EXISTS teams (
    id UUID DEFAULT gen_random_uuid(),
    game game_type NOT NULL,
    source_id VARCHAR(100),
    name VARCHAR(200) NOT NULL,
    tag VARCHAR(50),
    region VARCHAR(50),
    logo_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    PRIMARY KEY (id, game),
    UNIQUE (game, name)
) PARTITION BY LIST (game);

CREATE TABLE IF NOT EXISTS teams_cs PARTITION OF teams FOR VALUES IN ('cs');
CREATE TABLE IF NOT EXISTS teams_valorant PARTITION OF teams FOR VALUES IN ('valorant');

CREATE INDEX IF NOT EXISTS idx_teams_region ON teams (region);

-- ============================================
-- 6. PLAYERS TABLES (Game-Specific)
-- ============================================

CREATE TABLE IF NOT EXISTS players (
    id UUID DEFAULT gen_random_uuid(),
    game game_type NOT NULL,
    source_id VARCHAR(100),
    name VARCHAR(200) NOT NULL,
    real_name VARCHAR(200),
    nationality VARCHAR(100),
    current_team_id UUID,
    role VARCHAR(50), -- IGL, Entry, Support, etc.
    
    -- Career aggregates
    total_matches INTEGER DEFAULT 0,
    total_kills INTEGER DEFAULT 0,
    total_deaths INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_extracted_at TIMESTAMPTZ,
    
    PRIMARY KEY (id, game),
    UNIQUE (game, name)
) PARTITION BY LIST (game);

CREATE TABLE IF NOT EXISTS players_cs PARTITION OF players FOR VALUES IN ('cs');
CREATE TABLE IF NOT EXISTS players_valorant PARTITION OF players FOR VALUES IN ('valorant');

CREATE INDEX IF NOT EXISTS idx_players_team ON players (current_team_id);

-- ============================================
-- 7. SHARED TOURNAMENTS TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS tournaments (
    id UUID DEFAULT gen_random_uuid(),
    game game_type NOT NULL,
    source_id VARCHAR(100),
    name VARCHAR(300) NOT NULL,
    tier VARCHAR(20), -- S, A, B, C
    
    -- Dates
    start_date DATE,
    end_date DATE,
    
    -- Location/Region
    location VARCHAR(200),
    region VARCHAR(50),
    
    -- Prize
    prize_pool DECIMAL(15,2),
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Status
    status VARCHAR(20) DEFAULT 'upcoming',
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_tournaments_game ON tournaments (game, start_date DESC);
CREATE INDEX IF NOT EXISTS idx_tournaments_status ON tournaments (status);

-- ============================================
-- 8. RAW EXTRACTION STORAGE (Partitioned)
-- ============================================

CREATE TABLE IF NOT EXISTS raw_extractions (
    id UUID DEFAULT gen_random_uuid(),
    game game_type NOT NULL,
    source VARCHAR(50) NOT NULL,
    job_id UUID,
    
    -- Source identification
    source_type VARCHAR(50), -- match, player, tournament
    source_id VARCHAR(100),
    source_url TEXT,
    
    -- Content
    raw_data JSONB NOT NULL,
    raw_html TEXT,
    
    -- Integrity
    checksum VARCHAR(64) NOT NULL,
    extracted_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Processing status
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMPTZ,
    processing_error TEXT,
    
    PRIMARY KEY (id, game)
) PARTITION BY LIST (game);

CREATE TABLE IF NOT EXISTS raw_extractions_cs PARTITION OF raw_extractions
    FOR VALUES IN ('cs');

CREATE TABLE IF NOT EXISTS raw_extractions_valorant PARTITION OF raw_extractions
    FOR VALUES IN ('valorant');

CREATE INDEX IF NOT EXISTS idx_raw_source ON raw_extractions (game, source, source_id);
CREATE INDEX IF NOT EXISTS idx_raw_checksum ON raw_extractions (checksum);
CREATE INDEX IF NOT EXISTS idx_raw_processed ON raw_extractions (processed, extracted_at);

-- ============================================
-- 9. AGGREGATE STATISTICS TABLES
-- ============================================

-- Player career aggregates (materialized view)
CREATE MATERIALIZED VIEW IF NOT EXISTS player_career_stats_cs AS
SELECT 
    player_id,
    COUNT(*) as total_matches,
    SUM(kills) as total_kills,
    SUM(deaths) as total_deaths,
    SUM(assists) as total_assists,
    AVG((game_stats->>'rating')::DECIMAL) as avg_rating,
    AVG((game_stats->>'adr')::DECIMAL) as avg_adr,
    MAX(match_date) as last_match_date
FROM player_performance_cs
GROUP BY player_id;

CREATE MATERIALIZED VIEW IF NOT EXISTS player_career_stats_valorant AS
SELECT 
    player_id,
    COUNT(*) as total_matches,
    SUM(kills) as total_kills,
    SUM(deaths) as total_deaths,
    SUM(assists) as total_assists,
    AVG((game_stats->>'acs')::DECIMAL) as avg_acs,
    AVG((game_stats->>'adr')::DECIMAL) as avg_adr,
    MAX(match_date) as last_match_date
FROM player_performance_valorant
GROUP BY player_id;

-- Refresh indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_career_cs_player ON player_career_stats_cs (player_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_career_val_player ON player_career_stats_valorant (player_id);

-- ============================================
-- 10. CONCURRENT ACCESS CONTROL
-- ============================================

-- Row-level security for game isolation (optional)
ALTER TABLE matches ENABLE ROW LEVEL SECURITY;

CREATE POLICY matches_game_isolation ON matches
    USING (game = current_setting('app.current_game')::game_type);

-- Function to set current game context
CREATE OR REPLACE FUNCTION set_game_context(game_name TEXT)
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_game', game_name, FALSE);
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 11. PERFORMANCE OPTIMIZATION
-- ============================================

-- Auto-vacuum tuning for high-write tables
ALTER TABLE matches_cs SET (autovacuum_vacuum_scale_factor = 0.1);
ALTER TABLE matches_valorant SET (autovacuum_vacuum_scale_factor = 0.1);
ALTER TABLE player_performance_cs SET (autovacuum_vacuum_scale_factor = 0.1);
ALTER TABLE player_performance_valorant SET (autovacuum_vacuum_scale_factor = 0.1);

-- Compression policy for older data
SELECT add_compression_policy('matches_cs', INTERVAL '30 days');
SELECT add_compression_policy('matches_valorant', INTERVAL '30 days');
SELECT add_compression_policy('player_performance_cs', INTERVAL '30 days');
SELECT add_compression_policy('player_performance_valorant', INTERVAL '30 days');

-- ============================================
-- 12. MONITORING VIEWS
-- ============================================

-- Data freshness by game
CREATE OR REPLACE VIEW data_freshness AS
SELECT 
    'cs' as game,
    MAX(extracted_at) as last_extraction,
    COUNT(*) FILTER (WHERE extracted_at > NOW() - INTERVAL '24 hours') as last_24h_records
FROM matches_cs
UNION ALL
SELECT 
    'valorant' as game,
    MAX(extracted_at) as last_extraction,
    COUNT(*) FILTER (WHERE extracted_at > NOW() - INTERVAL '24 hours') as last_24h_records
FROM matches_valorant;

-- Table sizes by game
CREATE OR REPLACE VIEW storage_stats AS
SELECT 
    relname as table_name,
    pg_size_pretty(pg_total_relation_size(relid)) as total_size,
    pg_total_relation_size(relid) as size_bytes,
    n_live_tup as row_count
FROM pg_stat_user_tables
WHERE relname LIKE '%cs%' OR relname LIKE '%valorant%'
ORDER BY pg_total_relation_size(relid) DESC;

-- ============================================
-- 13. STORED PROCEDURES FOR DATA LOADING
-- ============================================

-- Insert match with conflict handling
CREATE OR REPLACE FUNCTION insert_match(
    p_game game_type,
    p_source VARCHAR,
    p_source_id VARCHAR,
    p_tournament_id UUID,
    p_match_date DATE,
    p_team_a_id UUID,
    p_team_b_id UUID,
    p_team_a_name VARCHAR,
    p_team_b_name VARCHAR,
    p_score_a SMALLINT,
    p_score_b SMALLINT,
    p_format VARCHAR,
    p_epoch SMALLINT,
    p_region VARCHAR,
    p_checksum VARCHAR
)
RETURNS UUID AS $$
DECLARE
    v_match_id UUID;
BEGIN
    INSERT INTO matches (
        game, source, source_id, tournament_id, match_date,
        team_a_id, team_b_id, team_a_name, team_b_name,
        score_a, score_b, format, epoch, region, checksum
    ) VALUES (
        p_game, p_source, p_source_id, p_tournament_id, p_match_date,
        p_team_a_id, p_team_b_id, p_team_a_name, p_team_b_name,
        p_score_a, p_score_b, p_format, p_epoch, p_region, p_checksum
    )
    ON CONFLICT (game, source, source_id) 
    DO UPDATE SET
        score_a = EXCLUDED.score_a,
        score_b = EXCLUDED.score_b,
        checksum = EXCLUDED.checksum,
        extracted_at = NOW()
    RETURNING id INTO v_match_id;
    
    RETURN v_match_id;
END;
$$ LANGUAGE plpgsql;

-- Insert player performance
CREATE OR REPLACE FUNCTION insert_player_performance(
    p_game game_type,
    p_match_id UUID,
    p_player_id UUID,
    p_team_id UUID,
    p_player_name VARCHAR,
    p_team_name VARCHAR,
    p_kills SMALLINT,
    p_deaths SMALLINT,
    p_assists SMALLINT,
    p_game_stats JSONB,
    p_match_date DATE
)
RETURNS UUID AS $$
DECLARE
    v_perf_id UUID;
BEGIN
    INSERT INTO player_performance (
        game, match_id, player_id, team_id, player_name, team_name,
        kills, deaths, assists, game_stats, match_date
    ) VALUES (
        p_game, p_match_id, p_player_id, p_team_id, p_player_name, p_team_name,
        p_kills, p_deaths, p_assists, p_game_stats, p_match_date
    )
    ON CONFLICT DO NOTHING
    RETURNING id INTO v_perf_id;
    
    RETURN v_perf_id;
END;
$$ LANGUAGE plpgsql;

-- Refresh career stats materialized views
CREATE OR REPLACE FUNCTION refresh_career_stats()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY player_career_stats_cs;
    REFRESH MATERIALIZED VIEW CONCURRENTLY player_career_stats_valorant;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 14. CLEANUP AND MAINTENANCE
-- ============================================

-- Function to cleanup old raw extractions
CREATE OR REPLACE FUNCTION cleanup_old_extractions(retention_days INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM raw_extractions
    WHERE extracted_at < NOW() - INTERVAL '1 day' * retention_days
      AND processed = TRUE;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Schedule cleanup (optional, requires pg_cron)
-- SELECT cron.schedule('cleanup-extractions', '0 2 * * *', 'SELECT cleanup_old_extractions(7)');
