-- Migration 003: Dual-Storage Raw/Reconstructed Separation Protocol

-- Immutable raw extraction archive
CREATE TABLE IF NOT EXISTS raw_extractions (
    raw_id              BIGSERIAL PRIMARY KEY,
    source_url          VARCHAR(500) NOT NULL,
    extracted_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    epoch               SMALLINT NOT NULL CHECK (epoch IN (1, 2, 3)),
    -- Epoch 1: 2020-2022, Epoch 2: 2023-2025, Epoch 3: 2026+
    raw_payload         JSONB NOT NULL,
    checksum_sha256     CHAR(64) NOT NULL UNIQUE,
    schema_version      VARCHAR(10) NOT NULL DEFAULT 'v2',
    vlr_match_id        VARCHAR(50),
    http_status         SMALLINT,
    user_agent_used     VARCHAR(200),
    rate_limit_delay_ms INT
);

-- Raw extractions are append-only — enforce with trigger
CREATE OR REPLACE FUNCTION prevent_raw_update()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Raw extractions are immutable. '
        'Record raw_id=% cannot be modified.', OLD.raw_id;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER raw_extractions_immutable
    BEFORE UPDATE OR DELETE ON raw_extractions
    FOR EACH ROW EXECUTE FUNCTION prevent_raw_update();

-- Reconstructed records table (partner records)
CREATE TABLE IF NOT EXISTS reconstructed_records (
    recon_id                BIGSERIAL PRIMARY KEY,
    partner_raw_id          BIGINT REFERENCES raw_extractions(raw_id),
    player_id               UUID NOT NULL,
    match_id                VARCHAR(50) NOT NULL,
    map_name                VARCHAR(50),
    reconstruction_method   VARCHAR(50),  -- acs_differential, role_inference, etc.
    confidence_tier         NUMERIC(5,2),
    reconstructed_fields    VARCHAR[] NOT NULL,  -- which fields were reconstructed
    reconstructed_values    JSONB NOT NULL,
    reconstruction_notes    TEXT,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    created_by              VARCHAR(100)  -- script or agent name
);

CREATE INDEX IF NOT EXISTS idx_recon_partner
    ON reconstructed_records (partner_raw_id);

CREATE INDEX IF NOT EXISTS idx_recon_player_match
    ON reconstructed_records (player_id, match_id);

-- View: unified records with separation metadata
CREATE OR REPLACE VIEW unified_records AS
SELECT
    pp.*,
    re.epoch,
    re.schema_version,
    re.vlr_match_id AS source_match_id,
    CASE
        WHEN pp.separation_flag = 0 THEN 'RAW'
        WHEN pp.separation_flag = 1 THEN 'RECONSTRUCTED'
    END AS record_type
FROM player_performance pp
LEFT JOIN raw_extractions re
    ON pp.checksum_sha256 = re.checksum_sha256;

COMMENT ON TABLE raw_extractions IS
    'Immutable append-only store for all VLR.gg raw extractions. '
    'Never modified after first write. SHA-256 enforces uniqueness.';

COMMENT ON TABLE reconstructed_records IS
    'Separated store for inferred/reconstructed data points. '
    'Always references a parent raw_extraction via partner_raw_id.';
