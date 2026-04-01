-- Migration 002: SATOR Square Visualization Metadata Tables

-- Map spatial reference data
CREATE TABLE IF NOT EXISTS map_spatial_ref (
    map_name        VARCHAR(50) PRIMARY KEY,
    svg_path        VARCHAR(200),
    width_units     SMALLINT,
    height_units    SMALLINT,
    callout_data    JSONB,  -- {zone_name: {x, y, w, h}}
    site_polygons   JSONB,  -- A site, B site coordinates
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- SATOR Layer 1: Golden halo event markers (planters, MVPs, hot streaks)
CREATE TABLE IF NOT EXISTS sator_events (
    event_id        BIGSERIAL PRIMARY KEY,
    match_id        VARCHAR(50) NOT NULL,
    player_id       UUID NOT NULL,
    event_type      VARCHAR(30) NOT NULL,  -- plant, mvp, hotstreak, ace
    round_number    SMALLINT,
    tick            INT,
    map_x           NUMERIC(6,2),
    map_y           NUMERIC(6,2),
    intensity       NUMERIC(4,2),  -- 0.0 to 1.0 for halo size
    realworld_time  TIMESTAMPTZ NOT NULL
);

SELECT create_hypertable('sator_events', 'realworld_time',
    chunk_time_interval => INTERVAL '90 days',
    if_not_exists => TRUE);

-- AREPO Layer 4: Death stain and multikill persistence markers
CREATE TABLE IF NOT EXISTS arepo_markers (
    marker_id       BIGSERIAL PRIMARY KEY,
    match_id        VARCHAR(50) NOT NULL,
    round_number    SMALLINT NOT NULL,
    victim_id       UUID NOT NULL,
    killer_id       UUID NOT NULL,
    map_x           NUMERIC(6,2) NOT NULL,
    map_y           NUMERIC(6,2) NOT NULL,
    weapon          VARCHAR(50),
    is_multikill    BOOLEAN DEFAULT FALSE,
    multikill_count SMALLINT DEFAULT 1,
    is_clutch       BOOLEAN DEFAULT FALSE,
    realworld_time  TIMESTAMPTZ NOT NULL
);

SELECT create_hypertable('arepo_markers', 'realworld_time',
    chunk_time_interval => INTERVAL '90 days',
    if_not_exists => TRUE);

-- ROTAS Layer 5: Rotation trail data
CREATE TABLE IF NOT EXISTS rotas_trails (
    trail_id        BIGSERIAL PRIMARY KEY,
    match_id        VARCHAR(50) NOT NULL,
    player_id       UUID NOT NULL,
    round_number    SMALLINT NOT NULL,
    tick_sequence   INT[] NOT NULL,      -- ordered ticks
    x_sequence      NUMERIC(6,2)[] NOT NULL,
    y_sequence      NUMERIC(6,2)[] NOT NULL,
    direction_lr    SMALLINT,             -- -1 left, 0 neutral, 1 right
    realworld_time  TIMESTAMPTZ NOT NULL
);

SELECT create_hypertable('rotas_trails', 'realworld_time',
    chunk_time_interval => INTERVAL '90 days',
    if_not_exists => TRUE);

-- Seed base map entries
INSERT INTO map_spatial_ref (map_name, width_units, height_units) VALUES
    ('Ascent', 1024, 1024),
    ('Bind', 1024, 1024),
    ('Haven', 1024, 1024),
    ('Pearl', 1024, 1024),
    ('Icebox', 1024, 1024),
    ('Breeze', 1024, 1024),
    ('Fracture', 1024, 1024),
    ('Lotus', 1024, 1024),
    ('Sunset', 1024, 1024)
ON CONFLICT DO NOTHING;
