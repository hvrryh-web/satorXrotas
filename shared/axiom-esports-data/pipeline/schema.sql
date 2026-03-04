-- Axiom Pipeline Database Schema
-- ================================
-- Run this SQL to initialize the pipeline state store tables.
--
-- Usage:
--   psql $DATABASE_URL -f schema.sql
--

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Pipeline runs table
-- Stores all pipeline execution runs with their status and metrics
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    trigger_type VARCHAR(20) NOT NULL DEFAULT 'manual',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    metrics JSONB NOT NULL DEFAULT '{}',
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    parent_run_id UUID REFERENCES pipeline_runs(run_id) ON DELETE SET NULL
);

-- Indexes for pipeline_runs
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status ON pipeline_runs(status);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_created_at ON pipeline_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_trigger_type ON pipeline_runs(trigger_type);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_parent ON pipeline_runs(parent_run_id);

-- Pipeline run logs table
-- Stores detailed logs for each run
CREATE TABLE IF NOT EXISTS pipeline_run_logs (
    log_id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    level VARCHAR(10) NOT NULL DEFAULT 'INFO',
    message TEXT NOT NULL,
    source VARCHAR(100) DEFAULT '',
    metadata JSONB DEFAULT '{}'
);

-- Indexes for pipeline_run_logs
CREATE INDEX IF NOT EXISTS idx_pipeline_run_logs_run_id ON pipeline_run_logs(run_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_run_logs_timestamp ON pipeline_run_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_pipeline_run_logs_level ON pipeline_run_logs(level);

-- Scheduled jobs table
-- Stores cron, webhook, and event-triggered job configurations
CREATE TABLE IF NOT EXISTS pipeline_scheduled_jobs (
    job_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    trigger_type VARCHAR(20) NOT NULL DEFAULT 'cron',
    cron_expression VARCHAR(100),
    webhook_secret VARCHAR(255),
    event_filter JSONB,
    pipeline_args JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    run_count INTEGER NOT NULL DEFAULT 0,
    failure_count INTEGER NOT NULL DEFAULT 0
);

-- Indexes for pipeline_scheduled_jobs
CREATE INDEX IF NOT EXISTS idx_pipeline_scheduled_jobs_status ON pipeline_scheduled_jobs(status);
CREATE INDEX IF NOT EXISTS idx_pipeline_scheduled_jobs_next_run ON pipeline_scheduled_jobs(next_run_at);
CREATE INDEX IF NOT EXISTS idx_pipeline_scheduled_jobs_name ON pipeline_scheduled_jobs(name);

-- Checkpoints table
-- Stores progress checkpoints for resumable runs
CREATE TABLE IF NOT EXISTS pipeline_checkpoints (
    checkpoint_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    stage VARCHAR(50) NOT NULL,
    completed_match_ids JSONB NOT NULL DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for pipeline_checkpoints
CREATE INDEX IF NOT EXISTS idx_pipeline_checkpoints_run_id ON pipeline_checkpoints(run_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_checkpoints_created_at ON pipeline_checkpoints(created_at DESC);

-- Run history/triggers table for audit
-- Records all triggers with their source
CREATE TABLE IF NOT EXISTS pipeline_triggers (
    trigger_id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    trigger_type VARCHAR(20) NOT NULL,
    triggered_by VARCHAR(100),
    webhook_payload JSONB,
    triggered_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pipeline_triggers_run_id ON pipeline_triggers(run_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_triggers_triggered_at ON pipeline_triggers(triggered_at DESC);

-- Daemon metrics table
-- Stores daemon health and performance metrics
CREATE TABLE IF NOT EXISTS pipeline_daemon_metrics (
    metric_id SERIAL PRIMARY KEY,
    daemon_id VARCHAR(100) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    metric_value JSONB NOT NULL DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pipeline_daemon_metrics_daemon ON pipeline_daemon_metrics(daemon_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_daemon_metrics_recorded ON pipeline_daemon_metrics(recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_pipeline_daemon_metrics_type ON pipeline_daemon_metrics(metric_type);

-- Views

-- Active runs view
CREATE OR REPLACE VIEW v_pipeline_active_runs AS
SELECT 
    run_id,
    status,
    trigger_type,
    created_at,
    started_at,
    EXTRACT(EPOCH FROM (NOW() - started_at))::INTEGER AS duration_seconds,
    metrics->>'records_processed' AS records_processed,
    metrics->>'current_stage' AS current_stage
FROM pipeline_runs
WHERE status IN ('pending', 'running', 'retrying')
ORDER BY created_at DESC;

-- Job execution stats view
CREATE OR REPLACE VIEW v_pipeline_job_stats AS
SELECT 
    job_id,
    name,
    trigger_type,
    status,
    run_count,
    failure_count,
    CASE 
        WHEN run_count > 0 THEN (failure_count::FLOAT / run_count * 100)::NUMERIC(5,2)
        ELSE 0 
    END AS failure_rate,
    last_run_at,
    next_run_at
FROM pipeline_scheduled_jobs
ORDER BY run_count DESC;

-- Daily run summary view
CREATE OR REPLACE VIEW v_pipeline_daily_summary AS
SELECT 
    DATE(created_at) AS run_date,
    COUNT(*) AS total_runs,
    COUNT(*) FILTER (WHERE status = 'completed') AS completed_runs,
    COUNT(*) FILTER (WHERE status = 'failed') AS failed_runs,
    COUNT(*) FILTER (WHERE status = 'cancelled') AS cancelled_runs,
    SUM(COALESCE((metrics->>'records_processed')::INTEGER, 0)) AS total_records_processed,
    SUM(COALESCE((metrics->>'records_failed')::INTEGER, 0)) AS total_records_failed,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) FILTER (WHERE completed_at IS NOT NULL)::INTEGER AS avg_duration_seconds
FROM pipeline_runs
GROUP BY DATE(created_at)
ORDER BY run_date DESC;

-- Functions

-- Update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
DROP TRIGGER IF EXISTS update_pipeline_runs_updated_at ON pipeline_runs;
CREATE TRIGGER update_pipeline_runs_updated_at
    BEFORE UPDATE ON pipeline_runs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_pipeline_scheduled_jobs_updated_at ON pipeline_scheduled_jobs;
CREATE TRIGGER update_pipeline_scheduled_jobs_updated_at
    BEFORE UPDATE ON pipeline_scheduled_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Cleanup old logs function (run periodically)
CREATE OR REPLACE FUNCTION cleanup_old_pipeline_logs(retention_days INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM pipeline_run_logs
    WHERE timestamp < NOW() - INTERVAL '1 day' * retention_days;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Cleanup old daemon metrics function
CREATE OR REPLACE FUNCTION cleanup_old_daemon_metrics(retention_days INTEGER DEFAULT 7)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM pipeline_daemon_metrics
    WHERE recorded_at < NOW() - INTERVAL '1 day' * retention_days;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON TABLE pipeline_runs IS 'Stores all pipeline execution runs';
COMMENT ON TABLE pipeline_run_logs IS 'Detailed logs for each pipeline run';
COMMENT ON TABLE pipeline_scheduled_jobs IS 'Scheduled job configurations (cron, webhook, event)';
COMMENT ON TABLE pipeline_checkpoints IS 'Progress checkpoints for resumable runs';
COMMENT ON TABLE pipeline_triggers IS 'Audit trail of all pipeline triggers';
COMMENT ON TABLE pipeline_daemon_metrics IS 'Daemon health and performance metrics';
