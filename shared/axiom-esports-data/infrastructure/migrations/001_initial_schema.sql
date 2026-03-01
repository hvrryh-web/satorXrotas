-- Migration 001: Initial 37-field KCRITR Schema
-- Axiom Esports Data Infrastructure

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Core performance records table
CREATE TABLE IF NOT EXISTS player_performance (
    -- Identity (5 fields)
    player_id           UUID NOT NULL,
    name                VARCHAR(100) NOT NULL,
    team                VARCHAR(100),
    region              VARCHAR(20),
    role                VARCHAR(30),  -- Entry, IGL, Controller, Initiator, Sentinel

    -- Performance metrics (5 fields)
    kills               SMALLINT,
    deaths              SMALLINT,
    acs                 NUMERIC(6,2),
    adr                 NUMERIC(6,2),
    kast_pct            NUMERIC(5,2),  -- 0.00 to 100.00

    -- RAR Metrics (4 fields)
    role_adjusted_value     NUMERIC(8,4),
    replacement_level       NUMERIC(8,4),
    rar_score               NUMERIC(8,4),  -- role_adjusted_value / replacement_level
    investment_grade        CHAR(2),       -- A+, A, B, C, D

    -- Extended performance (10 fields)
    headshot_pct        NUMERIC(5,2),
    first_blood         SMALLINT,
    clutch_wins         SMALLINT,
    agent               VARCHAR(50),
    economy_rating      NUMERIC(6,2),
    adjusted_kill_value NUMERIC(8,4),  -- economy-normalized, used in SimRating
    sim_rating          NUMERIC(8,4),
    age                 SMALLINT,
    peak_age_estimate   SMALLINT,
    career_stage        VARCHAR(20),   -- rising, peak, declining

    -- Match context (5 fields)
    match_id            VARCHAR(50) NOT NULL,
    map_name            VARCHAR(50),
    tournament          VARCHAR(100),
    patch_version       VARCHAR(20),
    realworld_time      TIMESTAMPTZ NOT NULL,

    -- Data provenance (8 fields)
    data_source         VARCHAR(30),   -- vlr_gg, liquipedia, hltv, grid
    extraction_timestamp TIMESTAMPTZ DEFAULT NOW(),
    checksum_sha256     CHAR(64),
    confidence_tier     NUMERIC(5,2),  -- 0.00 to 100.00
    separation_flag     SMALLINT NOT NULL DEFAULT 0,  -- 0=raw, 1=reconstructed
    partner_datapoint_ref UUID,        -- FK to reconstructed record if applicable
    reconstruction_notes TEXT,
    record_id           BIGSERIAL,

    -- Composite primary key
    PRIMARY KEY (player_id, match_id, map_name)
);

-- Convert to hypertable partitioned by time
SELECT create_hypertable('player_performance', 'realworld_time',
    chunk_time_interval => INTERVAL '90 days',
    if_not_exists => TRUE);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_player_performance_player
    ON player_performance (player_id, realworld_time DESC);

CREATE INDEX IF NOT EXISTS idx_player_performance_match
    ON player_performance (match_id);

CREATE INDEX IF NOT EXISTS idx_player_performance_team_region
    ON player_performance (team, region, realworld_time DESC);

CREATE INDEX IF NOT EXISTS idx_player_performance_role
    ON player_performance (role, realworld_time DESC);

CREATE INDEX IF NOT EXISTS idx_player_performance_confidence
    ON player_performance (confidence_tier, separation_flag);

-- Separation constraint: raw records never reference reconstructions
ALTER TABLE player_performance
    ADD CONSTRAINT chk_separation_flag
    CHECK (separation_flag IN (0, 1));

-- Prevent raw records from having a reconstruction reference
ALTER TABLE player_performance
    ADD CONSTRAINT chk_no_ref_on_raw
    CHECK (NOT (separation_flag = 0 AND partner_datapoint_ref IS NOT NULL));

COMMENT ON TABLE player_performance IS
    'Unified master table: 88,560 validated records 2020-2026. '
    'separation_flag=0 for raw extractions (immutable), '
    'separation_flag=1 for reconstructed records.';
