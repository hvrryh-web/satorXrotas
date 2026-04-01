-- Migration 008: Developer Dashboard Tables
-- Extended tables for the developer dashboard UI

-- =====================================================
-- Dashboard Sessions Table
-- Tracks active dashboard sessions and user preferences
-- =====================================================
CREATE TABLE IF NOT EXISTS dashboard_sessions (
    session_id          VARCHAR(100) PRIMARY KEY,
    user_id             VARCHAR(100),
    user_role           VARCHAR(50) DEFAULT 'developer',
    
    -- Session metadata
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_activity_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at          TIMESTAMPTZ,
    
    -- User preferences
    preferred_layers    VARCHAR(50)[] DEFAULT '{}',
    default_view        VARCHAR(20) DEFAULT 'grid',
    refresh_interval    INT DEFAULT 30,  -- seconds
    
    -- Session data
    ip_address          INET,
    user_agent          TEXT
);

CREATE INDEX IF NOT EXISTS idx_dashboard_sessions_user 
    ON dashboard_sessions (user_id, last_activity_at DESC);

CREATE INDEX IF NOT EXISTS idx_dashboard_sessions_expiry 
    ON dashboard_sessions (expires_at) 
    WHERE expires_at IS NOT NULL;

COMMENT ON TABLE dashboard_sessions IS 
    'Active dashboard sessions with user preferences and activity tracking.';

-- =====================================================
-- Component Health History Table
-- Time-series storage for component health check results
-- =====================================================
CREATE TABLE IF NOT EXISTS component_health_history (
    history_id          BIGSERIAL PRIMARY KEY,
    recorded_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Component reference
    component_id        VARCHAR(100) NOT NULL,
    layer               VARCHAR(50) NOT NULL,
    
    -- Status
    overall_status      VARCHAR(20) NOT NULL,
    CONSTRAINT chk_component_status CHECK (overall_status IN ('healthy', 'degraded', 'critical', 'unknown', 'maintenance')),
    
    -- Individual checks (stored as JSONB for flexibility)
    checks              JSONB NOT NULL DEFAULT '[]',
    
    -- Response metrics
    avg_response_time_ms NUMERIC(10,3),
    max_response_time_ms NUMERIC(10,3),
    failed_checks_count INT DEFAULT 0,
    
    -- Source
    collector_version   VARCHAR(20) DEFAULT '1.0.0',
    source_instance     VARCHAR(100) DEFAULT 'primary'
);

-- Convert to TimescaleDB hypertable if available
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
        PERFORM create_hypertable('component_health_history', 'recorded_at', 
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE);
    END IF;
EXCEPTION WHEN OTHERS THEN
    -- TimescaleDB not available, proceed without hypertable
    NULL;
END $$;

CREATE INDEX IF NOT EXISTS idx_component_health_time 
    ON component_health_history (recorded_at DESC);

CREATE INDEX IF NOT EXISTS idx_component_health_component 
    ON component_health_history (component_id, recorded_at DESC);

CREATE INDEX IF NOT EXISTS idx_component_health_layer 
    ON component_health_history (layer, recorded_at DESC);

CREATE INDEX IF NOT EXISTS idx_component_health_status 
    ON component_health_history (overall_status, recorded_at DESC);

COMMENT ON TABLE component_health_history IS 
    'Time-series history of component health check results for trend analysis.';

-- =====================================================
-- Dashboard Audit Log
-- Tracks user actions and system events
-- =====================================================
CREATE TABLE IF NOT EXISTS dashboard_audit_log (
    audit_id            BIGSERIAL PRIMARY KEY,
    occurred_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Event details
    event_type          VARCHAR(50) NOT NULL,
    CONSTRAINT chk_audit_event_type CHECK (
        event_type IN ('view', 'action', 'alert_ack', 'maintenance_start', 
                      'maintenance_end', 'config_change', 'login', 'logout')
    ),
    
    -- Actor
    user_id             VARCHAR(100),
    session_id          VARCHAR(100) REFERENCES dashboard_sessions(session_id) ON DELETE SET NULL,
    
    -- Target
    target_type         VARCHAR(50),  -- component, layer, alert, etc.
    target_id           VARCHAR(100),
    
    -- Details
    description         TEXT,
    metadata            JSONB DEFAULT '{}',
    
    -- IP for security auditing
    ip_address          INET
);

CREATE INDEX IF NOT EXISTS idx_dashboard_audit_time 
    ON dashboard_audit_log (occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_dashboard_audit_user 
    ON dashboard_audit_log (user_id, occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_dashboard_audit_event 
    ON dashboard_audit_log (event_type, occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_dashboard_audit_target 
    ON dashboard_audit_log (target_type, target_id, occurred_at DESC);

COMMENT ON TABLE dashboard_audit_log IS 
    'Audit trail of dashboard user actions and system events.';

-- =====================================================
-- Maintenance Windows Extended Table
-- Enhanced maintenance scheduling with approval workflow
-- =====================================================
CREATE TABLE IF NOT EXISTS maintenance_windows (
    window_id           VARCHAR(100) PRIMARY KEY,
    title               VARCHAR(200) NOT NULL,
    description         TEXT,
    
    -- Timing
    scheduled_start     TIMESTAMPTZ NOT NULL,
    scheduled_end       TIMESTAMPTZ NOT NULL,
    actual_start        TIMESTAMPTZ,
    actual_end          TIMESTAMPTZ,
    timezone            VARCHAR(50) DEFAULT 'UTC',
    
    -- Affected systems
    affected_layers     VARCHAR(50)[] DEFAULT '{}',
    affected_components VARCHAR(100)[] DEFAULT '{}',
    
    -- Status workflow
    status              VARCHAR(20) NOT NULL DEFAULT 'scheduled',
    CONSTRAINT chk_maintenance_status CHECK (
        status IN ('draft', 'pending_approval', 'scheduled', 'in_progress', 'completed', 'cancelled', 'failed')
    ),
    
    -- Approval workflow
    requested_by        VARCHAR(100) NOT NULL,
    requested_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    approved_by         VARCHAR(100),
    approved_at         TIMESTAMPTZ,
    
    -- Execution
    executed_by         VARCHAR(100),
    execution_notes     TEXT,
    
    -- Notification settings
    notify_before_minutes INT[] DEFAULT '{60, 15}',
    notifications_sent  TIMESTAMPTZ[] DEFAULT '{}',
    
    -- Rollback plan
    rollback_procedure  TEXT,
    rollback_triggered  BOOLEAN DEFAULT FALSE,
    
    CONSTRAINT valid_maintenance_window CHECK (scheduled_end > scheduled_start)
);

CREATE INDEX IF NOT EXISTS idx_maintenance_windows_time 
    ON maintenance_windows (scheduled_start, scheduled_end);

CREATE INDEX IF NOT EXISTS idx_maintenance_windows_status 
    ON maintenance_windows (status, scheduled_start);

CREATE INDEX IF NOT EXISTS idx_maintenance_windows_affected 
    ON maintenance_windows USING GIN (affected_components);

-- Partial index for active/pending maintenance
CREATE INDEX IF NOT EXISTS idx_maintenance_windows_active 
    ON maintenance_windows (scheduled_start) 
    WHERE status IN ('scheduled', 'in_progress');

COMMENT ON TABLE maintenance_windows IS 
    'Scheduled maintenance windows with approval workflow and execution tracking.';

-- =====================================================
-- Alert Rules Table
-- Configurable alerting rules with thresholds
-- =====================================================
CREATE TABLE IF NOT EXISTS alert_rules (
    rule_id             VARCHAR(100) PRIMARY KEY,
    name                VARCHAR(200) NOT NULL,
    description         TEXT,
    
    -- Rule is active
    enabled             BOOLEAN DEFAULT TRUE,
    
    -- Condition scope
    component_id        VARCHAR(100),  -- NULL = all components
    layer               VARCHAR(50),   -- NULL = all layers
    check_type          VARCHAR(50),   -- NULL = all check types
    
    -- Condition logic
    condition_type      VARCHAR(50) NOT NULL,
    CONSTRAINT chk_alert_condition CHECK (
        condition_type IN ('status_change', 'threshold_exceeded', 'consecutive_failures', 'no_data')
    ),
    
    -- Threshold values
    warning_threshold   NUMERIC,
    critical_threshold  NUMERIC,
    consecutive_count   INT DEFAULT 1,
    
    -- Severity
    severity            VARCHAR(20) NOT NULL DEFAULT 'warning',
    CONSTRAINT chk_rule_severity CHECK (severity IN ('info', 'warning', 'critical')),
    
    -- Notification channels
    notify_channels     VARCHAR(50)[] DEFAULT '{}',
    notify_recipients   VARCHAR(200)[] DEFAULT '{}',
    
    -- Cooldown to prevent spam
    cooldown_minutes    INT DEFAULT 15,
    
    -- Metadata
    created_by          VARCHAR(100) NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Stats
    trigger_count       INT DEFAULT 0,
    last_triggered_at   TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_alert_rules_enabled 
    ON alert_rules (enabled, layer, component_id);

CREATE INDEX IF NOT EXISTS idx_alert_rules_severity 
    ON alert_rules (severity) 
    WHERE enabled = TRUE;

COMMENT ON TABLE alert_rules IS 
    'Configurable alerting rules for system monitoring.';

-- =====================================================
-- Dashboard Notifications Table
-- User-specific notification queue
-- =====================================================
CREATE TABLE IF NOT EXISTS dashboard_notifications (
    notification_id     BIGSERIAL PRIMARY KEY,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Recipient
    user_id             VARCHAR(100) NOT NULL,
    
    -- Content
    notification_type   VARCHAR(50) NOT NULL,
    CONSTRAINT chk_notification_type CHECK (
        notification_type IN ('alert', 'maintenance', 'system', 'info')
    ),
    
    title               VARCHAR(200) NOT NULL,
    message             TEXT NOT NULL,
    
    -- Related entities
    related_alert_id    BIGINT,
    related_maintenance_id VARCHAR(100),
    
    -- Status
    is_read             BOOLEAN DEFAULT FALSE,
    read_at             TIMESTAMPTZ,
    
    -- Action link
    action_url          TEXT,
    action_text         VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_dashboard_notifications_user 
    ON dashboard_notifications (user_id, is_read, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_dashboard_notifications_unread 
    ON dashboard_notifications (user_id, created_at DESC) 
    WHERE is_read = FALSE;

COMMENT ON TABLE dashboard_notifications IS 
    'User-specific notification queue for dashboard alerts and updates.';

-- =====================================================
-- Views for Dashboard
-- =====================================================

-- Component health summary view (latest status per component)
CREATE OR REPLACE VIEW v_component_health_latest AS
WITH latest_check AS (
    SELECT DISTINCT ON (component_id)
        component_id,
        overall_status,
        checks,
        recorded_at,
        avg_response_time_ms
    FROM component_health_history
    ORDER BY component_id, recorded_at DESC
)
SELECT 
    c.*,
    COALESCE(l.overall_status, 'unknown') as current_status,
    l.checks as latest_checks,
    l.recorded_at as last_check_at,
    l.avg_response_time_ms
FROM (
    SELECT 
        component_id,
        name,
        layer,
        description,
        health_endpoint,
        check_interval_seconds
    FROM (
        VALUES 
            ('postgres_primary', 'PostgreSQL Primary', 'infrastructure', 'Main PostgreSQL database', 'postgresql://health', 60),
            ('redis_cache', 'Redis Cache', 'infrastructure', 'Caching layer', NULL, 60),
            ('fastapi_main', 'FastAPI Main', 'api_services', 'Main FastAPI backend', '/health', 30),
            ('pipeline_coordinator', 'Pipeline Coordinator', 'api_services', 'Job coordination service', 'http://localhost:8080/health', 30),
            ('cs_extractor', 'CS Extractor', 'data_pipeline', 'Counter-Strike data extraction', NULL, 300),
            ('valorant_extractor', 'Valorant Extractor', 'data_pipeline', 'Valorant data extraction', NULL, 300),
            ('lol_extractor', 'LoL Extractor', 'data_pipeline', 'League of Legends data extraction', NULL, 300),
            ('static_website', 'Static Website (GitHub Pages)', 'web_platform', 'Marketing site', 'https://satorx.github.io', 300),
            ('react_web_app', 'SATOR Web (Vercel)', 'web_platform', 'React web application', 'https://sator-web.vercel.app', 60),
            ('supabase', 'Supabase', 'external', 'PostgreSQL hosting', 'https://status.supabase.com', 300),
            ('render_api', 'Render (API)', 'external', 'API hosting', 'https://status.render.com', 300),
            ('vercel', 'Vercel', 'external', 'Frontend hosting', 'https://www.vercel-status.com', 300)
    ) AS t(component_id, name, layer, description, health_endpoint, check_interval_seconds)
) c
LEFT JOIN latest_check l ON c.component_id = l.component_id;

-- Layer status summary view
CREATE OR REPLACE VIEW v_layer_status_summary AS
SELECT 
    layer,
    COUNT(*) as total_components,
    COUNT(*) FILTER (WHERE current_status = 'healthy') as healthy_count,
    COUNT(*) FILTER (WHERE current_status = 'degraded') as degraded_count,
    COUNT(*) FILTER (WHERE current_status = 'critical') as critical_count,
    COUNT(*) FILTER (WHERE current_status = 'unknown') as unknown_count,
    CASE 
        WHEN COUNT(*) FILTER (WHERE current_status = 'critical') > 0 THEN 'critical'
        WHEN COUNT(*) FILTER (WHERE current_status = 'degraded') > 0 THEN 'degraded'
        WHEN COUNT(*) FILTER (WHERE current_status = 'unknown') = COUNT(*) THEN 'unknown'
        ELSE 'healthy'
    END as overall_status
FROM v_component_health_latest
GROUP BY layer;

-- Upcoming maintenance view
CREATE OR REPLACE VIEW v_upcoming_maintenance AS
SELECT 
    *,
    EXTRACT(EPOCH FROM (scheduled_start - NOW()))/3600 as hours_until_start
FROM maintenance_windows
WHERE status IN ('scheduled', 'pending_approval')
  AND scheduled_start > NOW()
ORDER BY scheduled_start;

-- Active alerts summary view
CREATE OR REPLACE VIEW v_dashboard_alerts AS
SELECT 
    a.*,
    EXTRACT(EPOCH FROM (NOW() - a.created_at))/3600 as hours_open,
    r.name as rule_name,
    r.severity as rule_severity
FROM pipeline_alerts a
LEFT JOIN alert_rules r ON a.rule_name = r.rule_id
WHERE a.status = 'firing'
ORDER BY 
    CASE a.severity WHEN 'critical' THEN 1 WHEN 'warning' THEN 2 ELSE 3 END,
    a.created_at DESC;

-- =====================================================
-- Functions for Dashboard
-- =====================================================

-- Function to record component health check
CREATE OR REPLACE FUNCTION record_component_health(
    p_component_id VARCHAR(100),
    p_layer VARCHAR(50),
    p_status VARCHAR(20),
    p_checks JSONB DEFAULT '[]',
    p_response_time_ms NUMERIC DEFAULT NULL
)
RETURNS BIGINT AS $$
DECLARE
    v_history_id BIGINT;
BEGIN
    INSERT INTO component_health_history (
        component_id,
        layer,
        overall_status,
        checks,
        avg_response_time_ms
    ) VALUES (
        p_component_id,
        p_layer,
        p_status,
        p_checks,
        p_response_time_ms
    )
    RETURNING history_id INTO v_history_id;
    
    RETURN v_history_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get health history for a component
CREATE OR REPLACE FUNCTION get_component_health_history(
    p_component_id VARCHAR(100),
    p_hours INT DEFAULT 24
)
RETURNS TABLE (
    recorded_at TIMESTAMPTZ,
    overall_status VARCHAR(20),
    checks JSONB,
    avg_response_time_ms NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        h.recorded_at,
        h.overall_status,
        h.checks,
        h.avg_response_time_ms
    FROM component_health_history h
    WHERE h.component_id = p_component_id
      AND h.recorded_at >= NOW() - INTERVAL '1 hour' * p_hours
    ORDER BY h.recorded_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get dashboard summary
CREATE OR REPLACE FUNCTION get_dashboard_summary()
RETURNS TABLE (
    total_components BIGINT,
    healthy_count BIGINT,
    degraded_count BIGINT,
    critical_count BIGINT,
    unknown_count BIGINT,
    overall_status VARCHAR(20)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_components,
        COUNT(*) FILTER (WHERE current_status = 'healthy')::BIGINT as healthy_count,
        COUNT(*) FILTER (WHERE current_status = 'degraded')::BIGINT as degraded_count,
        COUNT(*) FILTER (WHERE current_status = 'critical')::BIGINT as critical_count,
        COUNT(*) FILTER (WHERE current_status = 'unknown')::BIGINT as unknown_count,
        CASE 
            WHEN COUNT(*) FILTER (WHERE current_status = 'critical') > 0 THEN 'critical'
            WHEN COUNT(*) FILTER (WHERE current_status = 'degraded') > 0 THEN 'degraded'
            ELSE 'healthy'
        END::VARCHAR(20) as overall_status
    FROM v_component_health_latest;
END;
$$ LANGUAGE plpgsql;

-- Function to create notification
CREATE OR REPLACE FUNCTION create_notification(
    p_user_id VARCHAR(100),
    p_type VARCHAR(50),
    p_title VARCHAR(200),
    p_message TEXT,
    p_related_alert_id BIGINT DEFAULT NULL,
    p_action_url TEXT DEFAULT NULL
)
RETURNS BIGINT AS $$
DECLARE
    v_notification_id BIGINT;
BEGIN
    INSERT INTO dashboard_notifications (
        user_id,
        notification_type,
        title,
        message,
        related_alert_id,
        action_url
    ) VALUES (
        p_user_id,
        p_type,
        p_title,
        p_message,
        p_related_alert_id,
        p_action_url
    )
    RETURNING notification_id INTO v_notification_id;
    
    RETURN v_notification_id;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update alert_rules updated_at
CREATE OR REPLACE FUNCTION update_alert_rule_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_alert_rule ON alert_rules;
CREATE TRIGGER trg_update_alert_rule
    BEFORE UPDATE ON alert_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_alert_rule_timestamp();

-- Comments on views
COMMENT ON VIEW v_component_health_latest IS 
    'Latest health status for all registered components.';
COMMENT ON VIEW v_layer_status_summary IS 
    'Aggregated health status by system layer.';
COMMENT ON VIEW v_upcoming_maintenance IS 
    'Upcoming scheduled maintenance windows.';
COMMENT ON VIEW v_dashboard_alerts IS 
    'Currently firing alerts with rule information.';
