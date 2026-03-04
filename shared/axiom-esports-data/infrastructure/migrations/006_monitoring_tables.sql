-- Migration 006: Monitoring and Alerting Tables
-- Axiom Pipeline Monitoring Schema

-- =====================================================
-- Pipeline Runs Table
-- Tracks all pipeline executions with detailed metrics
-- =====================================================
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id              VARCHAR(100) PRIMARY KEY,
    status              VARCHAR(20) NOT NULL DEFAULT 'running',
    -- CHECK constraint for valid statuses
    CONSTRAINT chk_run_status CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
    
    mode                VARCHAR(20) NOT NULL DEFAULT 'delta',
    -- CHECK constraint for valid modes
    CONSTRAINT chk_run_mode CHECK (mode IN ('delta', 'full', 'backfill')),
    
    epochs              INT[] NOT NULL DEFAULT '{1,2,3}',
    
    -- Timing
    started_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at        TIMESTAMPTZ,
    duration_seconds    NUMERIC(10,3),
    
    -- Record counts
    total_records       INT NOT NULL DEFAULT 0,
    processed_records   INT NOT NULL DEFAULT 0,
    failed_records      INT NOT NULL DEFAULT 0,
    duplicate_records   INT NOT NULL DEFAULT 0,
    skipped_records     INT NOT NULL DEFAULT 0,
    
    -- Quality metrics
    validation_pass_rate NUMERIC(5,4) DEFAULT 0,
    data_quality_score   NUMERIC(5,2) DEFAULT 0,  -- 0-100
    
    -- Error tracking
    error_count         INT NOT NULL DEFAULT 0,
    last_error          TEXT,
    error_types         VARCHAR(50)[] DEFAULT '{}',
    
    -- Metadata
    version             VARCHAR(20) DEFAULT '1.0.0',
    triggered_by        VARCHAR(100) DEFAULT 'system',  -- user, schedule, webhook
    
    -- Resource usage (if available)
    peak_memory_mb      INT,
    cpu_seconds         NUMERIC(10,2),
    
    -- Index for time-series queries
    CONSTRAINT valid_timestamps CHECK (completed_at IS NULL OR completed_at >= started_at)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_started 
    ON pipeline_runs (started_at DESC);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status 
    ON pipeline_runs (status, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_mode 
    ON pipeline_runs (mode, started_at DESC);

-- Partial index for active runs
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_active 
    ON pipeline_runs (started_at DESC) 
    WHERE status = 'running';

COMMENT ON TABLE pipeline_runs IS 
    'Tracks all pipeline executions with detailed metrics and outcomes.';

-- =====================================================
-- Pipeline Stages Table
-- Per-stage metrics for each pipeline run
-- =====================================================
CREATE TABLE IF NOT EXISTS pipeline_stages (
    stage_id            BIGSERIAL PRIMARY KEY,
    run_id              VARCHAR(100) NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    stage_name          VARCHAR(50) NOT NULL,
    -- CHECK constraint for valid stage names
    CONSTRAINT chk_stage_name CHECK (
        stage_name IN ('discover', 'fetch', 'verify', 'parse', 'transform', 'crossref', 'store', 'index')
    ),
    
    sequence_order      INT NOT NULL DEFAULT 0,
    
    -- Timing
    started_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at        TIMESTAMPTZ,
    duration_seconds    NUMERIC(10,3),
    
    -- Record counts
    records_in          INT NOT NULL DEFAULT 0,
    records_out         INT NOT NULL DEFAULT 0,
    records_failed      INT NOT NULL DEFAULT 0,
    
    -- Latency metrics (in milliseconds)
    avg_latency_ms      NUMERIC(10,3),
    p95_latency_ms      NUMERIC(10,3),
    p99_latency_ms      NUMERIC(10,3),
    
    -- Error details (limited to top errors)
    errors              JSONB DEFAULT '[]',
    
    -- Metadata
    worker_id           VARCHAR(50),  -- For distributed processing
    
    UNIQUE (run_id, stage_name)
);

CREATE INDEX IF NOT EXISTS idx_pipeline_stages_run 
    ON pipeline_stages (run_id, sequence_order);

CREATE INDEX IF NOT EXISTS idx_pipeline_stages_duration 
    ON pipeline_stages (stage_name, duration_seconds) 
    WHERE duration_seconds IS NOT NULL;

COMMENT ON TABLE pipeline_stages IS 
    'Per-stage execution metrics for detailed pipeline performance analysis.';

-- =====================================================
-- Pipeline Alerts Table
-- Tracks triggered alerts and their status
-- =====================================================
CREATE TABLE IF NOT EXISTS pipeline_alerts (
    alert_id            BIGSERIAL PRIMARY KEY,
    alert_uuid          UUID NOT NULL DEFAULT gen_random_uuid(),
    
    run_id              VARCHAR(100) REFERENCES pipeline_runs(run_id) ON DELETE SET NULL,
    rule_name           VARCHAR(100) NOT NULL,
    
    severity            VARCHAR(20) NOT NULL,
    -- CHECK constraint for valid severities
    CONSTRAINT chk_alert_severity CHECK (severity IN ('critical', 'warning', 'info')),
    
    status              VARCHAR(20) NOT NULL DEFAULT 'firing',
    -- CHECK constraint for valid statuses
    CONSTRAINT chk_alert_status CHECK (status IN ('pending', 'firing', 'resolved', 'silenced')),
    
    message             TEXT NOT NULL,
    context             JSONB DEFAULT '{}',
    
    -- Channels that received this alert
    channels            VARCHAR(50)[] DEFAULT '{}',
    
    -- Timing
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at         TIMESTAMPTZ,
    acknowledged_at     TIMESTAMPTZ,
    acknowledged_by     VARCHAR(100),
    
    -- Deduplication tracking
    dedup_key           VARCHAR(200),
    
    -- External references (e.g., GitHub issue URL)
    external_refs       JSONB DEFAULT '{}',
    
    -- Resolution details
    resolution_notes    TEXT,
    
    CONSTRAINT valid_alert_times CHECK (
        resolved_at IS NULL OR resolved_at >= created_at
    )
);

-- Indexes for alert queries
CREATE INDEX IF NOT EXISTS idx_pipeline_alerts_status 
    ON pipeline_alerts (status, severity, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_pipeline_alerts_rule 
    ON pipeline_alerts (rule_name, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_pipeline_alerts_run 
    ON pipeline_alerts (run_id, created_at DESC);

-- Partial index for active (firing) alerts
CREATE INDEX IF NOT EXISTS idx_pipeline_alerts_firing 
    ON pipeline_alerts (severity, rule_name) 
    WHERE status = 'firing';

-- Unique index for deduplication
CREATE UNIQUE INDEX IF NOT EXISTS idx_pipeline_alerts_dedup 
    ON pipeline_alerts (COALESCE(dedup_key, alert_uuid::text));

COMMENT ON TABLE pipeline_alerts IS 
    'Tracks all triggered alerts with lifecycle management (pending, firing, resolved).';

-- =====================================================
-- Pipeline Metrics Table
-- Time-series metrics storage (optional, for systems without Prometheus)
-- =====================================================
CREATE TABLE IF NOT EXISTS pipeline_metrics (
    metric_id           BIGSERIAL PRIMARY KEY,
    metric_name         VARCHAR(100) NOT NULL,
    metric_type         VARCHAR(20) NOT NULL DEFAULT 'gauge',
    -- CHECK constraint for valid metric types
    CONSTRAINT chk_metric_type CHECK (metric_type IN ('counter', 'gauge', 'histogram')),
    
    value               NUMERIC NOT NULL,
    
    -- Labels (tags) for the metric
    labels              JSONB DEFAULT '{}',
    
    -- Timestamp
    recorded_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Source
    run_id              VARCHAR(100) REFERENCES pipeline_runs(run_id) ON DELETE SET NULL,
    
    -- For histograms
    bucket_le           NUMERIC  -- Less than or equal to bucket value
);

-- Convert to TimescaleDB hypertable if available
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
        PERFORM create_hypertable('pipeline_metrics', 'recorded_at', 
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE);
    END IF;
EXCEPTION WHEN OTHERS THEN
    -- TimescaleDB not available, proceed without hypertable
    NULL;
END $$;

CREATE INDEX IF NOT EXISTS idx_pipeline_metrics_name_time 
    ON pipeline_metrics (metric_name, recorded_at DESC);

CREATE INDEX IF NOT EXISTS idx_pipeline_metrics_labels 
    ON pipeline_metrics USING GIN (labels);

COMMENT ON TABLE pipeline_metrics IS 
    'Time-series storage for pipeline metrics (fallback for systems without Prometheus).';

-- =====================================================
-- Anomaly Log Table
-- Detected anomalies for trend analysis
-- =====================================================
CREATE TABLE IF NOT EXISTS anomaly_log (
    anomaly_id          BIGSERIAL PRIMARY KEY,
    
    run_id              VARCHAR(100) REFERENCES pipeline_runs(run_id) ON DELETE SET NULL,
    
    anomaly_type        VARCHAR(50) NOT NULL,
    -- CHECK constraint for valid anomaly types
    CONSTRAINT chk_anomaly_type CHECK (
        anomaly_type IN (
            'volume_drop', 'volume_spike', 'error_rate_spike', 
            'latency_spike', 'schema_drift', 'duplicate_surge', 'missing_data'
        )
    ),
    
    severity            VARCHAR(20) NOT NULL DEFAULT 'medium',
    -- CHECK constraint for valid severities
    CONSTRAINT chk_anomaly_severity CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    
    message             TEXT NOT NULL,
    
    -- Values
    current_value       NUMERIC NOT NULL,
    expected_min        NUMERIC,
    expected_max        NUMERIC,
    
    -- Confidence 0-1
    confidence          NUMERIC(4,3) NOT NULL DEFAULT 0.5,
    
    -- Additional context
    context             JSONB DEFAULT '{}',
    
    detected_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Whether this anomaly triggered an alert
    alert_triggered     BOOLEAN DEFAULT FALSE,
    alert_id            BIGINT REFERENCES pipeline_alerts(alert_id) ON DELETE SET NULL,
    
    -- Whether this was a false positive
    false_positive      BOOLEAN DEFAULT FALSE,
    reviewed_by         VARCHAR(100),
    reviewed_at         TIMESTAMPTZ,
    review_notes        TEXT
);

CREATE INDEX IF NOT EXISTS idx_anomaly_log_detected 
    ON anomaly_log (detected_at DESC);

CREATE INDEX IF NOT EXISTS idx_anomaly_log_type 
    ON anomaly_log (anomaly_type, detected_at DESC);

CREATE INDEX IF NOT EXISTS idx_anomaly_log_unreviewed 
    ON anomaly_log (anomaly_type, severity) 
    WHERE reviewed_at IS NULL AND false_positive = FALSE;

COMMENT ON TABLE anomaly_log IS 
    'Log of detected anomalies for trend analysis and model improvement.';

-- =====================================================
-- Health Check Log Table
-- Periodic health check results
-- =====================================================
CREATE TABLE IF NOT EXISTS health_check_log (
    check_id            BIGSERIAL PRIMARY KEY,
    checked_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    overall_status      VARCHAR(20) NOT NULL,
    -- CHECK constraint for valid statuses
    CONSTRAINT chk_health_status CHECK (overall_status IN ('healthy', 'degraded', 'unhealthy')),
    
    -- Component checks stored as JSONB
    component_results   JSONB NOT NULL DEFAULT '{}',
    
    -- Summary of issues
    issues              TEXT[] DEFAULT '{}',
    
    -- Latency of the health check itself
    check_duration_ms   INT,
    
    -- Source (which instance performed the check)
    source_instance     VARCHAR(100) DEFAULT 'primary'
);

CREATE INDEX IF NOT EXISTS idx_health_check_time 
    ON health_check_log (checked_at DESC);

CREATE INDEX IF NOT EXISTS idx_health_check_status 
    ON health_check_log (overall_status, checked_at DESC);

COMMENT ON TABLE health_check_log IS 
    'Historical record of health check results for availability tracking.';

-- =====================================================
-- Functions and Triggers
-- =====================================================

-- Function to update duration on run completion
CREATE OR REPLACE FUNCTION update_run_duration()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.completed_at IS NOT NULL AND NEW.started_at IS NOT NULL THEN
        NEW.duration_seconds := EXTRACT(EPOCH FROM (NEW.completed_at - NEW.started_at));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-calculate duration
DROP TRIGGER IF EXISTS trg_update_run_duration ON pipeline_runs;
CREATE TRIGGER trg_update_run_duration
    BEFORE UPDATE ON pipeline_runs
    FOR EACH ROW
    WHEN (OLD.completed_at IS DISTINCT FROM NEW.completed_at)
    EXECUTE FUNCTION update_run_duration();

-- Function to calculate stage duration
CREATE OR REPLACE FUNCTION update_stage_duration()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.completed_at IS NOT NULL AND NEW.started_at IS NOT NULL THEN
        NEW.duration_seconds := EXTRACT(EPOCH FROM (NEW.completed_at - NEW.started_at));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for stage duration
DROP TRIGGER IF EXISTS trg_update_stage_duration ON pipeline_stages;
CREATE TRIGGER trg_update_stage_duration
    BEFORE UPDATE ON pipeline_stages
    FOR EACH ROW
    WHEN (OLD.completed_at IS DISTINCT FROM NEW.completed_at)
    EXECUTE FUNCTION update_stage_duration();

-- Function to get pipeline success rate (last N days)
CREATE OR REPLACE FUNCTION get_pipeline_success_rate(days INT DEFAULT 7)
RETURNS NUMERIC AS $$
DECLARE
    total_runs INT;
    successful_runs INT;
    success_rate NUMERIC;
BEGIN
    SELECT COUNT(*) INTO total_runs
    FROM pipeline_runs
    WHERE started_at >= NOW() - INTERVAL '1 day' * days;
    
    SELECT COUNT(*) INTO successful_runs
    FROM pipeline_runs
    WHERE started_at >= NOW() - INTERVAL '1 day' * days
      AND status = 'completed'
      AND (failed_records::NUMERIC / NULLIF(total_records, 0)) < 0.1;
    
    success_rate := CASE 
        WHEN total_runs = 0 THEN 0
        ELSE (successful_runs::NUMERIC / total_runs * 100)
    END;
    
    RETURN ROUND(success_rate, 2);
END;
$$ LANGUAGE plpgsql;

-- Function to get active alerts summary
CREATE OR REPLACE FUNCTION get_active_alerts_summary()
RETURNS TABLE (
    severity VARCHAR,
    count BIGINT,
    oldest TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.severity,
        COUNT(*) AS count,
        MIN(a.created_at) AS oldest
    FROM pipeline_alerts a
    WHERE a.status = 'firing'
    GROUP BY a.severity
    ORDER BY 
        CASE a.severity 
            WHEN 'critical' THEN 1 
            WHEN 'warning' THEN 2 
            ELSE 3 
        END;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Views
-- =====================================================

-- Daily run summary view
CREATE OR REPLACE VIEW v_daily_run_summary AS
SELECT 
    DATE(started_at) AS date,
    COUNT(*) AS total_runs,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS successful_runs,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_runs,
    SUM(total_records) AS total_records,
    SUM(processed_records) AS processed_records,
    SUM(failed_records) AS failed_records,
    AVG(data_quality_score) AS avg_quality_score,
    AVG(duration_seconds) AS avg_duration_seconds
FROM pipeline_runs
GROUP BY DATE(started_at)
ORDER BY date DESC;

-- Active alerts view
CREATE OR REPLACE VIEW v_active_alerts AS
SELECT 
    a.*,
    r.run_id AS related_run_id,
    r.status AS run_status,
    EXTRACT(EPOCH FROM (NOW() - a.created_at))/3600 AS hours_open
FROM pipeline_alerts a
LEFT JOIN pipeline_runs r ON a.run_id = r.run_id
WHERE a.status = 'firing'
ORDER BY 
    CASE a.severity WHEN 'critical' THEN 1 WHEN 'warning' THEN 2 ELSE 3 END,
    a.created_at DESC;

-- Recent anomalies view
CREATE OR REPLACE VIEW v_recent_anomalies AS
SELECT 
    a.*,
    al.message AS alert_message,
    al.severity AS alert_severity
FROM anomaly_log a
LEFT JOIN pipeline_alerts al ON a.alert_id = al.alert_id
WHERE a.detected_at >= NOW() - INTERVAL '24 hours'
ORDER BY a.detected_at DESC;

COMMENT ON VIEW v_daily_run_summary IS 
    'Daily aggregation of pipeline run statistics.';
COMMENT ON VIEW v_active_alerts IS 
    'Currently firing alerts with related run information.';
COMMENT ON VIEW v_recent_anomalies IS 
    'Anomalies detected in the last 24 hours.';
