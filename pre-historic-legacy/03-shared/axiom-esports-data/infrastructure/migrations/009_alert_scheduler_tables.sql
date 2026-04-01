-- Migration 009: Alert Scheduler Tables
-- Tables for the maintenance scheduler and alert management system

-- =====================================================
-- Active Alerts Table
-- Tracks currently firing alerts with state management
-- =====================================================
CREATE TABLE IF NOT EXISTS active_alerts (
    id                  VARCHAR(100) PRIMARY KEY,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Alert source
    rule_id             VARCHAR(100) NOT NULL REFERENCES alert_rules(rule_id),
    component_id        VARCHAR(100) NOT NULL,
    
    -- Alert details
    severity            VARCHAR(20) NOT NULL,
    CONSTRAINT chk_active_alert_severity CHECK (
        severity IN ('info', 'warning', 'critical')
    ),
    message             TEXT NOT NULL,
    details             JSONB DEFAULT '{}',
    
    -- Timing
    triggered_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Acknowledgment
    acknowledged_at     TIMESTAMPTZ,
    acknowledged_by     VARCHAR(100),
    
    -- Resolution
    resolved_at         TIMESTAMPTZ,
    resolution_note     TEXT
);

CREATE INDEX IF NOT EXISTS idx_active_alerts_rule 
    ON active_alerts (rule_id, resolved_at);

CREATE INDEX IF NOT EXISTS idx_active_alerts_component 
    ON active_alerts (component_id, resolved_at);

CREATE INDEX IF NOT EXISTS idx_active_alerts_severity 
    ON active_alerts (severity, triggered_at DESC) 
    WHERE resolved_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_active_alerts_unresolved 
    ON active_alerts (triggered_at DESC) 
    WHERE resolved_at IS NULL;

COMMENT ON TABLE active_alerts IS 
    'Currently active (firing) alerts with acknowledgment and resolution tracking.';

-- =====================================================
-- Alert History Table
-- Archive of resolved alerts for reporting and analysis
-- =====================================================
CREATE TABLE IF NOT EXISTS alert_history (
    history_id          BIGSERIAL PRIMARY KEY,
    alert_id            VARCHAR(100) NOT NULL,
    
    -- Copy of alert data at resolution
    rule_id             VARCHAR(100) NOT NULL,
    component_id        VARCHAR(100) NOT NULL,
    severity            VARCHAR(20) NOT NULL,
    message             TEXT NOT NULL,
    details             JSONB DEFAULT '{}',
    
    -- Timing
    triggered_at        TIMESTAMPTZ NOT NULL,
    acknowledged_at     TIMESTAMPTZ,
    acknowledged_by     VARCHAR(100),
    resolved_at         TIMESTAMPTZ NOT NULL,
    resolution_note     TEXT,
    duration_seconds    INT GENERATED ALWAYS AS (
        EXTRACT(EPOCH FROM (resolved_at - triggered_at))
    ) STORED,
    
    -- Archive timestamp
    archived_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alert_history_time 
    ON alert_history (resolved_at DESC);

CREATE INDEX IF NOT EXISTS idx_alert_history_rule 
    ON alert_history (rule_id, resolved_at DESC);

CREATE INDEX IF NOT EXISTS idx_alert_history_component 
    ON alert_history (component_id, resolved_at DESC);

-- Convert to TimescaleDB hypertable if available
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
        PERFORM create_hypertable('alert_history', 'resolved_at', 
            chunk_time_interval => INTERVAL '7 days',
            if_not_exists => TRUE);
    END IF;
EXCEPTION WHEN OTHERS THEN
    NULL;
END $$;

COMMENT ON TABLE alert_history IS 
    'Archive of resolved alerts for MTTR calculations and trend analysis.';

-- =====================================================
-- Notification Log Table
-- Track all sent notifications for audit and debugging
-- =====================================================
CREATE TABLE IF NOT EXISTS notification_log (
    log_id              BIGSERIAL PRIMARY KEY,
    sent_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Recipient info
    channel             VARCHAR(50) NOT NULL,
    CONSTRAINT chk_notification_channel CHECK (
        channel IN ('email', 'slack', 'pagerduty', 'webhook', 'sms')
    ),
    recipient           VARCHAR(200) NOT NULL,
    
    -- Content
    notification_type   VARCHAR(50) NOT NULL,
    CONSTRAINT chk_notification_type CHECK (
        notification_type IN ('alert', 'maintenance', 'recovery', 'digest')
    ),
    subject             VARCHAR(500),
    body                TEXT,
    
    -- Related entities
    alert_id            VARCHAR(100),
    maintenance_id      VARCHAR(100),
    
    -- Delivery status
    status              VARCHAR(20) NOT NULL DEFAULT 'pending',
    CONSTRAINT chk_notification_status CHECK (
        status IN ('pending', 'sent', 'failed', 'bounced')
    ),
    error_message       TEXT,
    retry_count         INT DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_notification_log_time 
    ON notification_log (sent_at DESC);

CREATE INDEX IF NOT EXISTS idx_notification_log_status 
    ON notification_log (status, retry_count) 
    WHERE status IN ('pending', 'failed');

CREATE INDEX IF NOT EXISTS idx_notification_log_alert 
    ON notification_log (alert_id, sent_at DESC);

COMMENT ON TABLE notification_log IS 
    'Audit log of all notifications sent by the alerting system.';

-- =====================================================
-- Scheduler State Table
-- Tracks scheduler runs and heartbeats
-- =====================================================
CREATE TABLE IF NOT EXISTS scheduler_state (
    scheduler_id        VARCHAR(100) PRIMARY KEY,
    scheduler_type      VARCHAR(50) NOT NULL,
    CONSTRAINT chk_scheduler_type CHECK (
        scheduler_type IN ('maintenance', 'alert', 'cleanup')
    ),
    
    -- Status
    status              VARCHAR(20) NOT NULL DEFAULT 'running',
    CONSTRAINT chk_scheduler_status CHECK (
        status IN ('running', 'paused', 'stopped', 'error')
    ),
    
    -- Heartbeat tracking
    started_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_heartbeat_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_run_at         TIMESTAMPTZ,
    
    -- Run statistics
    run_count           INT DEFAULT 0,
    error_count         INT DEFAULT 0,
    
    -- Host info
    hostname            VARCHAR(100),
    pid                 INT
);

CREATE INDEX IF NOT EXISTS idx_scheduler_state_active 
    ON scheduler_state (scheduler_type, status) 
    WHERE status = 'running';

COMMENT ON TABLE scheduler_state IS 
    'Tracks scheduler instances for high-availability and monitoring.';

-- =====================================================
-- Functions and Triggers
-- =====================================================

-- Function to archive resolved alerts to history
CREATE OR REPLACE FUNCTION archive_resolved_alert()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.resolved_at IS NOT NULL AND OLD.resolved_at IS NULL THEN
        INSERT INTO alert_history (
            alert_id, rule_id, component_id, severity,
            message, details, triggered_at,
            acknowledged_at, acknowledged_by,
            resolved_at, resolution_note
        ) VALUES (
            NEW.id, NEW.rule_id, NEW.component_id, NEW.severity,
            NEW.message, NEW.details, NEW.triggered_at,
            NEW.acknowledged_at, NEW.acknowledged_by,
            NEW.resolved_at, NEW.resolution_note
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_archive_resolved_alert ON active_alerts;
CREATE TRIGGER trg_archive_resolved_alert
    AFTER UPDATE ON active_alerts
    FOR EACH ROW
    WHEN (NEW.resolved_at IS NOT NULL AND OLD.resolved_at IS NULL)
    EXECUTE FUNCTION archive_resolved_alert();

-- Function to clean up old active alerts (should be archived first)
CREATE OR REPLACE FUNCTION cleanup_old_alerts(
    p_days INT DEFAULT 30
)
RETURNS INT AS $$
DECLARE
    v_count INT;
BEGIN
    DELETE FROM active_alerts
    WHERE resolved_at < NOW() - INTERVAL '1 day' * p_days;
    
    GET DIAGNOSTICS v_count = ROW_COUNT;
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get alert statistics
CREATE OR REPLACE FUNCTION get_alert_stats(
    p_hours INT DEFAULT 24
)
RETURNS TABLE (
    total_alerts BIGINT,
    active_alerts BIGINT,
    avg_resolution_minutes NUMERIC,
    alerts_by_severity JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*) FROM alert_history 
         WHERE resolved_at > NOW() - INTERVAL '1 hour' * p_hours)::BIGNT as total_alerts,
        (SELECT COUNT(*) FROM active_alerts 
         WHERE resolved_at IS NULL)::BIGINT as active_alerts,
        (SELECT ROUND(AVG(duration_seconds)/60, 2) 
         FROM alert_history 
         WHERE resolved_at > NOW() - INTERVAL '1 hour' * p_hours) as avg_resolution_minutes,
        (SELECT jsonb_object_agg(severity, cnt)
         FROM (
             SELECT severity, COUNT(*) as cnt
             FROM active_alerts
             WHERE resolved_at IS NULL
             GROUP BY severity
         ) sub) as alerts_by_severity;
END;
$$ LANGUAGE plpgsql;

-- Function to record scheduler heartbeat
CREATE OR REPLACE FUNCTION record_scheduler_heartbeat(
    p_scheduler_id VARCHAR(100),
    p_scheduler_type VARCHAR(50)
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO scheduler_state (
        scheduler_id, scheduler_type, last_heartbeat_at, run_count
    ) VALUES (
        p_scheduler_id, p_scheduler_type, NOW(), 1
    )
    ON CONFLICT (scheduler_id) DO UPDATE SET
        last_heartbeat_at = NOW(),
        run_count = scheduler_state.run_count + 1,
        status = 'running';
END;
$$ LANGUAGE plpgsql;

-- Function to create maintenance notification
CREATE OR REPLACE FUNCTION notify_maintenance_start()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'in_progress' AND OLD.status != 'in_progress' THEN
        -- Create notifications for affected components
        INSERT INTO dashboard_notifications (
            user_id, notification_type, title, message, related_maintenance_id
        )
        SELECT 
            DISTINCT 'all_users',
            'maintenance',
            'Maintenance Started: ' || NEW.title,
            'Maintenance is now in progress for: ' || 
                COALESCE(array_to_string(NEW.affected_components, ', '), 
                        array_to_string(NEW.affected_layers, ', ')),
            NEW.window_id
        FROM dashboard_sessions
        WHERE expires_at > NOW() OR expires_at IS NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_notify_maintenance_start ON maintenance_windows;
CREATE TRIGGER trg_notify_maintenance_start
    AFTER UPDATE ON maintenance_windows
    FOR EACH ROW
    EXECUTE FUNCTION notify_maintenance_start();

-- Comments on functions
COMMENT ON FUNCTION archive_resolved_alert() IS 
    'Automatically archives resolved alerts to history table.';
COMMENT ON FUNCTION cleanup_old_alerts(INT) IS 
    'Removes old resolved alerts from active table (they should be archived).';
COMMENT ON FUNCTION get_alert_stats(INT) IS 
    'Returns alert statistics for the specified time period.';
COMMENT ON FUNCTION record_scheduler_heartbeat(VARCHAR, VARCHAR) IS 
    'Records a heartbeat from a scheduler instance.';
