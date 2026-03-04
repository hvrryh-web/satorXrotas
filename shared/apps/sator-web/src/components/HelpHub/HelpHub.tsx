import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { HealthCheckDashboard } from './HealthCheckDashboard';
import './HelpHub.css';

export const HelpHub: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'quickstart' | 'guides' | 'troubleshoot' | 'health'>('quickstart');

  const tabs = [
    { id: 'quickstart', label: 'Quick Start', icon: '🚀' },
    { id: 'guides', label: 'Guides', icon: '📚' },
    { id: 'troubleshoot', label: 'Troubleshoot', icon: '🔧' },
    { id: 'health', label: 'System Health', icon: '💓' }
  ];

  return (
    <div className="help-hub">
      {/* Header */}
      <header className="help-hub__header">
        <div className="help-hub__brand">
          <span className="help-icon">?</span>
          <h1>HELP HUB</h1>
        </div>
        <p className="help-hub__subtitle">Support Center & System Status</p>
      </header>

      {/* Navigation Tabs */}
      <nav className="help-hub__tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`help-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id as any)}
          >
            <span className="tab-icon">{tab.icon}</span>
            <span className="tab-label">{tab.label}</span>
          </button>
        ))}
      </nav>

      {/* Content Area */}
      <div className="help-hub__content">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
          >
            {activeTab === 'quickstart' && <QuickStartContent />}
            {activeTab === 'guides' && <GuidesContent />}
            {activeTab === 'troubleshoot' && <TroubleshootContent />}
            {activeTab === 'health' && <HealthCheckDashboard />}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Footer */}
      <footer className="help-hub__footer">
        <p>Need more help? Contact support@satorx.com</p>
      </footer>
    </div>
  );
};

// Quick Start Content
const QuickStartContent: React.FC = () => (
  <div className="help-content">
    <h2>🚀 Quick Start Guide</h2>
    
    <div className="quickstart-steps">
      <div className="step">
        <div className="step-number">1</div>
        <div className="step-content">
          <h3>Choose Your Hub</h3>
          <p>Select from the four service quadrants: Analytics, Stats, Info, or Game. Each hub specializes in different data and functionality.</p>
        </div>
      </div>

      <div className="step">
        <div className="step-number">2</div>
        <div className="step-content">
          <h3>Navigate the Interface</h3>
          <p>Use the quarterly grid to resize and focus on different services. Drag the gold handles to customize your view.</p>
        </div>
      </div>

      <div className="step">
        <div className="step-number">3</div>
        <div className="step-content">
          <h3>Access Data</h3>
          <p>Click "ENTER HUB" to access detailed analytics, player statistics, documentation, or game simulations.</p>
        </div>
      </div>

      <div className="step">
        <div className="step-number">4</div>
        <div className="step-content">
          <h3>Get Help</h3>
          <p>Click the center Help button (?) anytime to access guides, troubleshoot issues, or check system health.</p>
        </div>
      </div>
    </div>

    <div className="pro-tip">
      <strong>💡 Pro Tip:</strong> Use keyboard shortcuts! Press <kbd>1-4</kbd> to switch hubs, <kbd>?</kbd> for help, <kbd>Esc</kbd> to close.
    </div>
  </div>
);

// Guides Content
const GuidesContent: React.FC = () => (
  <div className="help-content">
    <h2>📚 User Guides</h2>
    
    <div className="guides-grid">
      <GuideCard 
        title="Analytics Deep Dive"
        description="Understanding SimRating, RAR metrics, and predictive models"
        icon="📊"
        readTime="5 min"
      />
      <GuideCard 
        title="Stats Reference"
        description="Complete guide to player statistics and match data interpretation"
        icon="📈"
        readTime="8 min"
      />
      <GuideCard 
        title="Game Simulation"
        description="How RadiantX processes matches and generates tactical insights"
        icon="🎮"
        readTime="6 min"
      />
      <GuideCard 
        title="API Integration"
        description="Connecting external tools to the SATOR platform"
        icon="🔌"
        readTime="10 min"
      />
      <GuideCard 
        title="Data Export"
        description="Exporting data for Excel, Tableau, or custom analysis"
        icon="📥"
        readTime="4 min"
      />
      <GuideCard 
        title="Custom Dashboards"
        description="Creating personalized views and saved queries"
        icon="🎨"
        readTime="7 min"
      />
    </div>
  </div>
);

const GuideCard: React.FC<{title: string, description: string, icon: string, readTime: string}> = ({
  title, description, icon, readTime
}) => (
  <motion.div 
    className="guide-card"
    whileHover={{ y: -4, boxShadow: '0 10px 30px rgba(0,0,0,0.3)' }}
  >
    <span className="guide-card__icon">{icon}</span>
    <h3>{title}</h3>
    <p>{description}</p>
    <span className="guide-card__time">{readTime} read</span>
  </motion.div>
);

// Troubleshoot Content
const TroubleshootContent: React.FC = () => (
  <div className="help-content">
    <h2>🔧 Troubleshooting</h2>
    
    <div className="troubleshoot-list">
      <TroubleshootItem 
        problem="Data not loading"
        solutions={[
          "Check internet connection",
          "Refresh the page (Ctrl+R / Cmd+R)",
          "Clear browser cache",
          "Check System Health tab for outages"
        ]}
      />
      <TroubleshootItem 
        problem="Slow performance"
        solutions={[
          "Close unused browser tabs",
          "Reduce grid complexity by collapsing unused quadrants",
          "Check CPU usage in Task Manager",
          "Try Chrome or Firefox for best performance"
        ]}
      />
      <TroubleshootItem 
        problem="Charts not displaying"
        solutions={[
          "Enable JavaScript in browser settings",
          "Disable ad blockers for this site",
          "Update browser to latest version",
          "Check console for error messages (F12)"
        ]}
      />
      <TroubleshootItem 
        problem="Export failing"
        solutions={[
          "Check available disk space",
          "Try smaller date ranges",
          "Use CSV format for large datasets",
          "Disable browser extensions temporarily"
        ]}
      />
    </div>
  </div>
);

const TroubleshootItem: React.FC<{problem: string, solutions: string[]}> = ({ problem, solutions }) => {
  const [isOpen, setIsOpen] = useState(false);
  
  return (
    <div className={`troubleshoot-item ${isOpen ? 'open' : ''}`}>
      <button className="troubleshoot-header" onClick={() => setIsOpen(!isOpen)}>
        <span className="troubleshoot-problem">{problem}</span>
        <span className="troubleshoot-toggle">{isOpen ? '−' : '+'}</span>
      </button>
      <AnimatePresence>
        {isOpen && (
          <motion.ul 
            className="troubleshoot-solutions"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
          >
            {solutions.map((solution, i) => (
              <li key={i}>{solution}</li>
            ))}
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  );
};

export default HelpHub;
