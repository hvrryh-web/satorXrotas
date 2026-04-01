import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { QuarterGrid } from '../components/QuarterGrid/QuarterGrid';
import { HelpHub } from '../components/HelpHub/HelpHub';
import './ServiceSelection.css';

// Hub Icons
const AnalyticsIcon = () => (
  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M3 3v18h18" />
    <path d="M18 17V9" />
    <path d="M13 17V5" />
    <path d="M8 17v-3" />
  </svg>
);

const StatsIcon = () => (
  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
    <circle cx="12" cy="12" r="10" />
    <path d="M12 6v6l4 2" />
  </svg>
);

const InfoIcon = () => (
  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
    <circle cx="12" cy="12" r="10" />
    <path d="M12 16v-4" />
    <path d="M12 8h.01" />
  </svg>
);

const GameIcon = () => (
  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
    <rect x="2" y="6" width="20" height="12" rx="2" />
    <path d="M6 12h4" />
    <path d="M8 10v4" />
    <circle cx="17" cy="12" r="2" />
  </svg>
);

export const ServiceSelection: React.FC = () => {
  const navigate = useNavigate();
  const [activeHub, setActiveHub] = useState<string | null>(null);

  const hubData = [
    {
      id: 'analytics',
      title: 'ADVANCEDANALYTICSHUB',
      shortTitle: 'ANALYTICS',
      icon: <AnalyticsIcon />,
      color: '#D4AF37', // Gold
      description: 'Deep statistical analysis, predictive models, and performance insights',
      features: ['SimRating Engine', 'Predictive Models', 'Trend Analysis', 'Custom Reports'],
      route: '/analytics'
    },
    {
      id: 'stats',
      title: 'STATS*REFERENCEHUB',
      shortTitle: 'STATS',
      icon: <StatsIcon />,
      color: '#00F0FF', // Neon Blue
      description: 'Comprehensive player statistics, match history, and data reference',
      features: ['Player Profiles', 'Match Database', 'Team Statistics', 'Historical Data'],
      route: '/stats'
    },
    {
      id: 'info',
      title: 'INFOHUB',
      shortTitle: 'INFO',
      icon: <InfoIcon />,
      color: '#A8D8EA', // Pastel Blue
      description: 'Documentation, guides, and platform information center',
      features: ['Documentation', 'API Reference', 'Tutorials', 'FAQ'],
      route: '/info'
    },
    {
      id: 'game',
      title: 'GAMEHUB',
      shortTitle: 'GAME',
      icon: <GameIcon />,
      color: '#1E3A5F', // Navy Blue
      description: 'RadiantX simulation, match replay, and tactical analysis',
      features: ['Match Simulation', 'Tactical Viewer', 'Replay Analysis', 'Agent Stats'],
      route: '/game'
    }
  ];

  const handleCellClick = (cellId: string) => {
    const hub = hubData.find(h => h.id === cellId);
    if (hub && activeHub !== cellId) {
      setActiveHub(cellId);
    } else if (activeHub === cellId) {
      // Navigate when clicking expanded cell
      navigate(hub.route);
    }
  };

  const cells = hubData.map(hub => ({
    id: hub.id,
    title: hub.shortTitle,
    icon: hub.icon,
    color: hub.color,
    content: (
      <HubPreview 
        hub={hub} 
        isActive={activeHub === hub.id}
        onEnter={() => navigate(hub.route)}
      />
    )
  }));

  return (
    <div className="service-selection">
      {/* Header */}
      <motion.header 
        className="service-header"
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6 }}
      >
        <div className="service-header__brand">
          <span className="brand-symbol">◈</span>
          <span className="brand-text">SATOR³</span>
        </div>
        <h1 className="service-header__title">Service Selection</h1>
      </motion.header>

      {/* Quarter Grid */}
      <QuarterGrid
        cells={cells}
        hubContent={<HelpHub />}
        onCellClick={handleCellClick}
      />

      {/* Instructions */}
      <motion.div 
        className="service-instructions"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1, duration: 0.6 }}
      >
        <p>Click to expand • Drag handles to resize • Center for Help</p>
      </motion.div>
    </div>
  );
};

// Hub Preview Component
interface HubPreviewProps {
  hub: typeof hubData[0];
  isActive: boolean;
  onEnter: () => void;
}

const HubPreview: React.FC<HubPreviewProps> = ({ hub, isActive, onEnter }) => {
  return (
    <div className="hub-preview">
      <motion.h2 
        className="hub-preview__title"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        {hub.title}
      </motion.h2>
      
      <p className="hub-preview__description">{hub.description}</p>
      
      <div className="hub-preview__features">
        {hub.features.map((feature, i) => (
          <motion.span 
            key={feature}
            className="feature-tag"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.1 }}
            style={{ borderColor: hub.color }}
          >
            {feature}
          </motion.span>
        ))}
      </div>
      
      {isActive && (
        <motion.button
          className="hub-preview__enter"
          onClick={(e) => {
            e.stopPropagation();
            onEnter();
          }}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          style={{ 
            background: hub.color,
            color: hub.id === 'game' ? 'white' : 'var(--abyssal-void)'
          }}
        >
          ENTER HUB →
        </motion.button>
      )}
    </div>
  );
};

export default ServiceSelection;
