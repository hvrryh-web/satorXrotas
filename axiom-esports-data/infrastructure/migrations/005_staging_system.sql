-- Migration 005: Shared Staging Database System
-- Central staging layer connecting game (RadiantX) and web (SATOR Web) projects.
-- All data flows through staging before being exported to project-specific stores.

-- ============================================================================
-- STAGING: Ingest queue — receives all incoming data before routing
-- ============================================================================
CREATE TABLE IF NOT EXISTS staging_ingest_queue (
    ingest_id           BIGSERIAL PRIMARY KEY,
    source_system       VARCHAR(30) NOT NULL CHECK (source_system IN ('game', 'analytics', 'scraper', 'manual')),
    payload_type        VARCHAR(50) NOT NULL,  -- e.g. 'match_event', 'player_stat', 'game_definition', 'replay_log'
    payload             JSONB NOT NULL,
    checksum_sha256     CHAR(64) NOT NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'validated', 'rejected', 'exported')),
    validation_errors   TEXT[],
    ingested_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    validated_at        TIMESTAMPTZ,
    exported_at         TIMESTAMPTZ,
    target_project      VARCHAR(20) CHECK (target_project IN ('game', 'web', 'both', NULL)),
    ingested_by         VARCHAR(100) DEFAULT 'system'
);

CREATE INDEX IF NOT EXISTS idx_staging_ingest_status
    ON staging_ingest_queue (status, ingested_at DESC);

CREATE INDEX IF NOT EXISTS idx_staging_ingest_source
    ON staging_ingest_queue (source_system, payload_type);

CREATE INDEX IF NOT EXISTS idx_staging_ingest_checksum
    ON staging_ingest_queue (checksum_sha256);

-- ============================================================================
-- STAGING: Static base — snapshot of compiled definitions served to projects
-- ============================================================================
CREATE TABLE IF NOT EXISTS staging_static_base (
    static_id           BIGSERIAL PRIMARY KEY,
    data_domain         VARCHAR(50) NOT NULL,  -- 'agents', 'weapons', 'utilities', 'rulesets', 'maps', 'role_baselines'
    data_version        VARCHAR(20) NOT NULL DEFAULT 'v1',
    payload             JSONB NOT NULL,
    checksum_sha256     CHAR(64) NOT NULL,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    superseded_at       TIMESTAMPTZ,
    created_by          VARCHAR(100) DEFAULT 'system',
    UNIQUE (data_domain, data_version)
);

-- Only one active version per domain
CREATE UNIQUE INDEX IF NOT EXISTS idx_staging_static_active
    ON staging_static_base (data_domain) WHERE is_active = TRUE;

-- ============================================================================
-- GAME PROJECT: Game data store — definitions and match data for RadiantX
-- ============================================================================
CREATE TABLE IF NOT EXISTS game_data_store (
    game_data_id        BIGSERIAL PRIMARY KEY,
    data_type           VARCHAR(50) NOT NULL,  -- 'agent_def', 'weapon_def', 'map_def', 'match_replay', 'event_log'
    data_key            VARCHAR(100) NOT NULL,  -- unique key within type, e.g. 'agent.rifler.elite'
    data_version        VARCHAR(20) NOT NULL DEFAULT 'v1',
    payload             JSONB NOT NULL,
    source_staging_id   BIGINT REFERENCES staging_static_base(static_id),
    exported_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (data_type, data_key, data_version)
);

CREATE INDEX IF NOT EXISTS idx_game_data_type_key
    ON game_data_store (data_type, data_key) WHERE is_active = TRUE;

-- ============================================================================
-- WEB PROJECT: Web data store — sanitized public stats for SATOR Web
-- ============================================================================
CREATE TABLE IF NOT EXISTS web_data_store (
    web_data_id         BIGSERIAL PRIMARY KEY,
    data_type           VARCHAR(50) NOT NULL,  -- 'player_stats', 'match_summary', 'leaderboard', 'tournament_result'
    data_key            VARCHAR(100) NOT NULL,
    data_version        VARCHAR(20) NOT NULL DEFAULT 'v1',
    payload             JSONB NOT NULL,
    source_staging_id   BIGINT REFERENCES staging_ingest_queue(ingest_id),
    firewall_verified   BOOLEAN NOT NULL DEFAULT FALSE,  -- Must be TRUE before serving to web
    exported_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (data_type, data_key, data_version)
);

CREATE INDEX IF NOT EXISTS idx_web_data_type_key
    ON web_data_store (data_type, data_key) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_web_data_firewall
    ON web_data_store (firewall_verified) WHERE is_active = TRUE;

-- ============================================================================
-- STAGING: Export forms — transformation rules for each project
-- ============================================================================
CREATE TABLE IF NOT EXISTS staging_export_forms (
    form_id             BIGSERIAL PRIMARY KEY,
    form_name           VARCHAR(100) NOT NULL UNIQUE,
    target_project      VARCHAR(20) NOT NULL CHECK (target_project IN ('game', 'web')),
    source_payload_type VARCHAR(50) NOT NULL,
    transform_rules     JSONB NOT NULL,  -- field mappings, filters, renames
    firewall_fields     TEXT[],          -- fields to strip for web forms
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- STAGING: Export log — audit trail of all data exports to projects
-- ============================================================================
CREATE TABLE IF NOT EXISTS staging_export_log (
    export_id           BIGSERIAL PRIMARY KEY,
    form_id             BIGINT REFERENCES staging_export_forms(form_id),
    source_ingest_id    BIGINT,
    source_static_id    BIGINT,
    target_project      VARCHAR(20) NOT NULL,
    target_table        VARCHAR(50) NOT NULL,
    target_record_id    BIGINT,
    exported_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    exported_by         VARCHAR(100) DEFAULT 'system',
    status              VARCHAR(20) NOT NULL DEFAULT 'success' CHECK (status IN ('success', 'failed', 'rolled_back')),
    error_message       TEXT
);

CREATE INDEX IF NOT EXISTS idx_export_log_project
    ON staging_export_log (target_project, exported_at DESC);

-- ============================================================================
-- STAGING: Health check table — monitors data freshness and pipeline status
-- ============================================================================
CREATE TABLE IF NOT EXISTS staging_health_status (
    check_id            BIGSERIAL PRIMARY KEY,
    check_type          VARCHAR(50) NOT NULL,  -- 'freshness', 'integrity', 'firewall', 'capacity'
    check_target        VARCHAR(100) NOT NULL,
    status              VARCHAR(20) NOT NULL CHECK (status IN ('healthy', 'warning', 'critical')),
    details             JSONB,
    checked_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_health_status_latest
    ON staging_health_status (check_type, checked_at DESC);

-- ============================================================================
-- SEED: Default export forms
-- ============================================================================
INSERT INTO staging_export_forms (form_name, target_project, source_payload_type, transform_rules, firewall_fields) VALUES
(
    'game_agent_definitions',
    'game',
    'game_definition',
    '{"field_map": {"id": "data_key", "payload": "payload"}, "filters": {"data_domain": "agents"}}',
    NULL
),
(
    'game_weapon_definitions',
    'game',
    'game_definition',
    '{"field_map": {"id": "data_key", "payload": "payload"}, "filters": {"data_domain": "weapons"}}',
    NULL
),
(
    'game_match_replay',
    'game',
    'match_event',
    '{"field_map": {"match_id": "data_key", "events": "payload"}, "filters": {}}',
    NULL
),
(
    'web_player_stats',
    'web',
    'player_stat',
    '{"field_map": {"playerId": "player_id", "matchId": "match_id", "kills": "kills", "deaths": "deaths", "assists": "assists", "damage": "damage", "headshots": "headshot_pct", "firstKills": "first_blood", "clutchesWon": "clutch_wins"}, "filters": {}}',
    ARRAY['internalAgentState', 'radarData', 'detailedReplayFrameData', 'simulationTick', 'seedValue', 'visionConeData', 'smokeTickData', 'recoilPattern']
),
(
    'web_match_summary',
    'web',
    'player_stat',
    '{"field_map": {"matchId": "match_id", "mapName": "map_name", "tournament": "tournament"}, "aggregation": "per_match"}',
    ARRAY['internalAgentState', 'radarData', 'detailedReplayFrameData', 'simulationTick', 'seedValue', 'visionConeData', 'smokeTickData', 'recoilPattern']
),
(
    'web_leaderboard',
    'web',
    'player_stat',
    '{"field_map": {"playerId": "player_id", "name": "name", "simRating": "sim_rating", "rarScore": "rar_score", "investmentGrade": "investment_grade"}, "aggregation": "latest_per_player"}',
    ARRAY['internalAgentState', 'radarData', 'detailedReplayFrameData', 'simulationTick', 'seedValue', 'visionConeData', 'smokeTickData', 'recoilPattern']
)
ON CONFLICT (form_name) DO NOTHING;

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON TABLE staging_ingest_queue IS
    'Central ingest queue for all data entering the SATOR staging system. '
    'Data from game, analytics, scrapers, or manual entry arrives here first.';

COMMENT ON TABLE staging_static_base IS
    'Versioned static data definitions (agents, weapons, maps, etc.). '
    'Serves as the saved base that both projects draw from.';

COMMENT ON TABLE game_data_store IS
    'RadiantX game project data store. Contains game definitions, replays, '
    'and event logs exported from staging.';

COMMENT ON TABLE web_data_store IS
    'SATOR Web project data store. Contains sanitized public stats. '
    'All records must pass firewall verification before serving.';

COMMENT ON TABLE staging_export_forms IS
    'Transform rules for converting staging data into project-specific formats. '
    'Web forms always strip GAME_ONLY_FIELDS; game forms include full data.';

COMMENT ON TABLE staging_export_log IS
    'Immutable audit trail of every data export from staging to project stores.';
