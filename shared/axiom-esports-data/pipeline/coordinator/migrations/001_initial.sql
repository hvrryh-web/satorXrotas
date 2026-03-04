-- Initial migration for Central Job Coordinator
-- Creates tables for jobs, agents, results, and related entities

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- Core Tables
-- =============================================================================

-- Extraction Jobs Table
CREATE TABLE IF NOT EXISTS extraction_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game VARCHAR(20) NOT NULL CHECK (game IN ('cs', 'valorant')),
    source VARCHAR(50) NOT NULL,
    job_type VARCHAR(50) NOT NULL,
    priority INTEGER NOT NULL DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    epoch INTEGER NOT NULL DEFAULT 1 CHECK (epoch >= 1 AND epoch <= 3),
    region VARCHAR(50),
    date_start TIMESTAMP WITH TIME ZONE,
    date_end TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending', 'assigned', 'processing', 'completed', 'failed', 'cancelled')),
    assigned_agent VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    dependencies UUID[],
    metadata JSONB DEFAULT '{}',
    error_message TEXT,
    
    -- Indexes
    CONSTRAINT valid_dates CHECK (date_end IS NULL OR date_start IS NULL OR date_end >= date_start)
);

-- Agents Table
CREATE TABLE IF NOT EXISTS agents (
    id VARCHAR(100) PRIMARY KEY,
    game_specialization VARCHAR(20)[] NOT NULL DEFAULT '{}',
    source_capabilities VARCHAR(50)[] NOT NULL DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'idle' 
        CHECK (status IN ('idle', 'busy', 'offline')),
    current_job_id UUID REFERENCES extraction_jobs(id) ON DELETE SET NULL,
    last_heartbeat TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    total_jobs_completed INTEGER NOT NULL DEFAULT 0,
    total_jobs_failed INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Job Results Table
CREATE TABLE IF NOT EXISTS job_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL UNIQUE REFERENCES extraction_jobs(id) ON DELETE CASCADE,
    success BOOLEAN NOT NULL,
    error TEXT,
    records_extracted INTEGER NOT NULL DEFAULT 0,
    checksum VARCHAR(32),
    metadata JSONB DEFAULT '{}',
    completed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    processing_time_ms INTEGER
);

-- Raw Extractions Table (for content drift detection)
CREATE TABLE IF NOT EXISTS raw_extractions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game VARCHAR(20) NOT NULL,
    source VARCHAR(50) NOT NULL,
    source_id VARCHAR(200) NOT NULL,
    checksum VARCHAR(32) NOT NULL,
    data_size INTEGER NOT NULL DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    extracted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    UNIQUE(game, source, source_id, checksum)
);

-- Content Drift Alerts Table
CREATE TABLE IF NOT EXISTS content_drift_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    existing_extraction_id UUID NOT NULL REFERENCES raw_extractions(id) ON DELETE CASCADE,
    new_checksum VARCHAR(32) NOT NULL,
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL DEFAULT 'open' 
        CHECK (status IN ('open', 'investigating', 'resolved', 'ignored')),
    resolution_notes TEXT,
    
    UNIQUE(existing_extraction_id, new_checksum)
);

-- Rate Limit Status Table (for persistence across restarts)
CREATE TABLE IF NOT EXISTS rate_limit_status (
    source VARCHAR(50) PRIMARY KEY,
    requests_per_minute INTEGER NOT NULL DEFAULT 60,
    requests_per_hour INTEGER NOT NULL DEFAULT 1000,
    burst_allowance INTEGER NOT NULL DEFAULT 10,
    consecutive_failures INTEGER NOT NULL DEFAULT 0,
    backoff_until TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Coordinator Events Table (for audit trail)
CREATE TABLE IF NOT EXISTS coordinator_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,  -- 'job', 'agent', 'system'
    entity_id VARCHAR(100),
    details JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- Indexes
-- =============================================================================

-- Job indexes
CREATE INDEX IF NOT EXISTS idx_jobs_status ON extraction_jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_game ON extraction_jobs(game);
CREATE INDEX IF NOT EXISTS idx_jobs_source ON extraction_jobs(source);
CREATE INDEX IF NOT EXISTS idx_jobs_assigned_agent ON extraction_jobs(assigned_agent) WHERE assigned_agent IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON extraction_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_status_created ON extraction_jobs(status, created_at) 
    WHERE status IN ('pending', 'assigned', 'processing');

-- Agent indexes
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_heartbeat ON agents(last_heartbeat);

-- Raw extractions indexes
CREATE INDEX IF NOT EXISTS idx_extractions_lookup ON raw_extractions(game, source, source_id);
CREATE INDEX IF NOT EXISTS idx_extractions_checksum ON raw_extractions(checksum);
CREATE INDEX IF NOT EXISTS idx_extractions_extracted ON raw_extractions(extracted_at);

-- Events indexes
CREATE INDEX IF NOT EXISTS idx_events_type ON coordinator_events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_created ON coordinator_events(created_at);

-- =============================================================================
-- Functions and Triggers
-- =============================================================================

-- Update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for agents table
DROP TRIGGER IF EXISTS update_agents_updated_at ON agents;
CREATE TRIGGER update_agents_updated_at
    BEFORE UPDATE ON agents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for rate_limit_status table
DROP TRIGGER IF EXISTS update_rate_limit_updated_at ON rate_limit_status;
CREATE TRIGGER update_rate_limit_updated_at
    BEFORE UPDATE ON rate_limit_status
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to log job status changes
CREATE OR REPLACE FUNCTION log_job_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS NULL OR OLD.status != NEW.status THEN
        INSERT INTO coordinator_events (event_type, entity_type, entity_id, details)
        VALUES (
            'job_status_changed',
            'job',
            NEW.id::text,
            jsonb_build_object(
                'old_status', OLD.status,
                'new_status', NEW.status,
                'assigned_agent', NEW.assigned_agent
            )
        );
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for job status changes
DROP TRIGGER IF EXISTS log_job_status_change ON extraction_jobs;
CREATE TRIGGER log_job_status_change
    AFTER UPDATE OF status ON extraction_jobs
    FOR EACH ROW
    EXECUTE FUNCTION log_job_status_change();

-- Function to clean up old events
CREATE OR REPLACE FUNCTION cleanup_old_events()
RETURNS void AS $$
BEGIN
    DELETE FROM coordinator_events 
    WHERE created_at < NOW() - INTERVAL '30 days';
    
    DELETE FROM raw_extractions 
    WHERE extracted_at < NOW() - INTERVAL '90 days';
END;
$$ language 'plpgsql';

-- =============================================================================
-- Views
-- =============================================================================

-- Job queue view (pending and assigned jobs)
CREATE OR REPLACE VIEW job_queue AS
SELECT 
    j.id,
    j.game,
    j.source,
    j.job_type,
    j.priority,
    j.status,
    j.assigned_agent,
    j.created_at,
    j.started_at,
    EXTRACT(EPOCH FROM (NOW() - j.created_at))/60 as age_minutes
FROM extraction_jobs j
WHERE j.status IN ('pending', 'assigned', 'processing')
ORDER BY j.priority DESC, j.created_at ASC;

-- Agent status view
CREATE OR REPLACE VIEW agent_status AS
SELECT 
    a.id,
    a.status,
    a.game_specialization,
    a.source_capabilities,
    a.total_jobs_completed,
    a.total_jobs_failed,
    EXTRACT(EPOCH FROM (NOW() - a.last_heartbeat))/60 as minutes_since_heartbeat,
    CASE 
        WHEN a.last_heartbeat < NOW() - INTERVAL '2 minutes' THEN 'stale'
        ELSE 'fresh'
    END as heartbeat_status
FROM agents a;

-- Performance summary view
CREATE OR REPLACE VIEW performance_summary AS
SELECT 
    game,
    source,
    COUNT(*) FILTER (WHERE status = 'completed') as completed,
    COUNT(*) FILTER (WHERE status = 'failed') as failed,
    COUNT(*) FILTER (WHERE status = 'pending') as pending,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) FILTER (WHERE status = 'completed') as avg_processing_time_sec
FROM extraction_jobs
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY game, source;

-- =============================================================================
-- Initial Data
-- =============================================================================

-- Insert default rate limit configurations
INSERT INTO rate_limit_status (source, requests_per_minute, requests_per_hour, burst_allowance)
VALUES 
    ('hltv', 30, 500, 5),
    ('vlr', 60, 2000, 10),
    ('liquipedia', 30, 300, 5),
    ('esl', 100, 3000, 20),
    ('blast', 60, 1000, 10),
    ('pgl', 60, 1000, 10),
    ('faceit', 120, 5000, 20),
    ('riot', 100, 3000, 15)
ON CONFLICT (source) DO NOTHING;
