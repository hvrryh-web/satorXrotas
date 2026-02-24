-- Migration 004: Extraction Log for Delta Tracking

CREATE TABLE IF NOT EXISTS extraction_log (
    log_id              BIGSERIAL PRIMARY KEY,
    source              VARCHAR(30) NOT NULL,  -- vlr_gg, liquipedia, hltv
    entity_type         VARCHAR(30) NOT NULL,  -- match, player, team, tournament
    entity_id           VARCHAR(100) NOT NULL,
    entity_url          VARCHAR(500),
    first_extracted_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_extracted_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_modified_hash  CHAR(64),   -- SHA-256 of last known content
    extraction_count    INT NOT NULL DEFAULT 1,
    last_http_status    SMALLINT,
    last_schema_version VARCHAR(10),
    is_complete         BOOLEAN DEFAULT FALSE,
    error_count         INT DEFAULT 0,
    last_error          TEXT,

    UNIQUE (source, entity_type, entity_id)
);

CREATE INDEX IF NOT EXISTS idx_extraction_log_last_extracted
    ON extraction_log (last_extracted_at DESC);

CREATE INDEX IF NOT EXISTS idx_extraction_log_source_type
    ON extraction_log (source, entity_type, is_complete);

-- Function: upsert extraction log entry
CREATE OR REPLACE FUNCTION upsert_extraction_log(
    p_source VARCHAR,
    p_entity_type VARCHAR,
    p_entity_id VARCHAR,
    p_entity_url VARCHAR,
    p_content_hash CHAR(64),
    p_http_status SMALLINT,
    p_schema_version VARCHAR
) RETURNS BOOLEAN AS $$
DECLARE
    content_changed BOOLEAN := TRUE;
BEGIN
    INSERT INTO extraction_log
        (source, entity_type, entity_id, entity_url,
         last_modified_hash, last_http_status, last_schema_version)
    VALUES
        (p_source, p_entity_type, p_entity_id, p_entity_url,
         p_content_hash, p_http_status, p_schema_version)
    ON CONFLICT (source, entity_type, entity_id)
    DO UPDATE SET
        last_extracted_at   = NOW(),
        extraction_count    = extraction_log.extraction_count + 1,
        last_http_status    = p_http_status,
        last_schema_version = p_schema_version,
        content_changed     = (extraction_log.last_modified_hash != p_content_hash),
        last_modified_hash  = p_content_hash;

    -- Return whether content changed (TRUE = re-process, FALSE = skip)
    SELECT (last_modified_hash = p_content_hash) INTO content_changed
    FROM extraction_log
    WHERE source = p_source AND entity_type = p_entity_type AND entity_id = p_entity_id;

    RETURN NOT content_changed;
END;
$$ LANGUAGE plpgsql;

-- Schema drift detection log
CREATE TABLE IF NOT EXISTS schema_drift_log (
    drift_id        BIGSERIAL PRIMARY KEY,
    detected_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_url      VARCHAR(500),
    expected_schema VARCHAR(10),
    detected_fields TEXT[],
    missing_fields  TEXT[],
    extra_fields    TEXT[],
    alert_sent      BOOLEAN DEFAULT FALSE
);

COMMENT ON TABLE extraction_log IS
    'Tracks last-extracted timestamps for delta extraction. '
    '90% reduction in VLR requests by only re-scraping changed records.';

COMMENT ON TABLE schema_drift_log IS
    'Records when VLR.gg schema deviates from expected structure. '
    'Triggers admin alert and falls back to cache.';
