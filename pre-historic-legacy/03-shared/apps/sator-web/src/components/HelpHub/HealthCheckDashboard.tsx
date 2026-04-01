import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import './HealthCheckDashboard.css';

interface HealthStatus {
  component: string;
  status: 'healthy' | 'degraded' | 'critical' | 'maintenance';
  latency: number;
  lastChecked: string;
  uptime: number;
}

export const HealthCheckDashboard: React.FC = () => {
  const [healthData, setHealthData] = useState<HealthStatus[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate health check data - in real app, fetch from API
    const mockData: HealthStatus[] = [
      { component: 'PostgreSQL Database', status: 'healthy', latency: 12, lastChecked: '2s ago', uptime: 99.99 },
      { component: 'FastAPI Backend', status: 'healthy', latency: 45, lastChecked: '3s ago', uptime: 99.95 },
      { component: 'React Frontend', status: 'healthy', latency: 23, lastChecked: '1s ago', uptime: 99.98 },
      { component: 'CS Data Extractor', status: 'degraded', latency: 1200, lastChecked: '5s ago', uptime: 97.50 },
      { component: 'Valorant Extractor', status: 'healthy', latency: 89, lastChecked: '4s ago', uptime: 98.90 },
      { component: 'Pipeline Coordinator', status: 'healthy', latency: 34, lastChecked: '2s ago', uptime: 99.80 },
      { component: 'Redis Cache', status: 'healthy', latency: 2, lastChecked: '1s ago', uptime: 99.99 },
      { component: 'External APIs', status: 'healthy', latency: 156, lastChecked: '6s ago', uptime: 99.70 },
    ];
    
    setTimeout(() => {
      setHealthData(mockData);
      setLoading(false);
    }, 1000);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return '#22C55E';
      case 'degraded': return '#F59E0B';
      case 'critical': return '#EF4444';
      case 'maintenance': return '#3B82F6';
      default: return '#9CA3AF';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return '✓';
      case 'degraded': return '!';
      case 'critical': return '✕';
      case 'maintenance': return '🔧';
      default: return '?';
    }
  };

  const overallStatus = healthData.every(h => h.status === 'healthy') 
    ? 'healthy' 
    : healthData.some(h => h.status === 'critical') 
      ? 'critical' 
      : 'degraded';

  if (loading) {
    return (
      <div className="health-dashboard health-dashboard--loading">
        <div className="health-loader" />
        <p>Checking system health...</p>
      </div>
    );
  }

  return (
    <div className="health-dashboard">
      {/* Overall Status */}
      <motion.div 
        className={`health-overall health-overall--${overallStatus}`}
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
      >
        <div className="overall-indicator">
          <span className="overall-icon">{getStatusIcon(overallStatus)}</span>
        </div>
        <div className="overall-info">
          <h3>System Status: {overallStatus.toUpperCase()}</h3>
          <p>{healthData.filter(h => h.status === 'healthy').length} of {healthData.length} services operational</p>
        </div>
        <div className="overall-uptime">
          <span className="uptime-value">99.8%</span>
          <span className="uptime-label">30-day uptime</span>
        </div>
      </motion.div>

      {/* Component Grid */}
      <div className="health-components">
        {healthData.map((item, index) => (
          <motion.div
            key={item.component}
            className={`health-card health-card--${item.status}`}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <div className="health-card__header">
              <span 
                className="health-status-dot"
                style={{ backgroundColor: getStatusColor(item.status) }}
              />
              <h4>{item.component}</h4>
              <span className={`health-badge health-badge--${item.status}`}>
                {item.status}
              </span>
            </div>
            
            <div className="health-card__metrics">
              <div className="metric">
                <span className="metric-label">Latency</span>
                <span className="metric-value">{item.latency}ms</span>
              </div>
              <div className="metric">
                <span className="metric-label">Uptime</span>
                <span className="metric-value">{item.uptime}%</span>
              </div>
            </div>
            
            <div className="health-card__footer">
              <span className="last-checked">Checked {item.lastChecked}</span>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Refresh Button */}
      <button 
        className="health-refresh"
        onClick={() => {
          setLoading(true);
          setTimeout(() => setLoading(false), 1000);
        }}
      >
        ↻ Refresh Status
      </button>
    </div>
  );
};

export default HealthCheckDashboard;
