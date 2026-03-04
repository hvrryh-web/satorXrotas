import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import './LandingPage.css';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  const handleEnter = () => {
    navigate('/loading');
  };

  return (
    <div className="landing-page">
      {/* Background Effects */}
      <div className="landing-page__bg">
        <div className="bg-gradient" />
        <div className="bg-glow bg-glow--1" />
        <div className="bg-glow bg-glow--2" />
        <div className="bg-glow bg-glow--3" />
      </div>

      {/* Content */}
      <motion.div 
        className="landing-page__content"
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
      >
        {/* Logo */}
        <motion.div 
          className="landing-logo"
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.8 }}
        >
          <span className="landing-logo__symbol">◈</span>
          <span className="landing-logo__text">SATOR</span>
          <span className="landing-logo__cube">³</span>
        </motion.div>

        {/* Tagline */}
        <motion.p 
          className="landing-tagline"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6, duration: 0.8 }}
        >
          Porcelain³ Intelligence Platform
        </motion.p>

        {/* Enter Button */}
        <motion.button
          className="landing-enter-btn"
          onClick={handleEnter}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.9, duration: 0.6 }}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.98 }}
        >
          <span className="enter-btn__text">ENTER PLATFORM</span>
          <span className="enter-btn__arrow">→</span>
        </motion.button>

        {/* Footer */}
        <motion.footer 
          className="landing-footer"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2, duration: 0.6 }}
        >
          <span className="footer-brand">Ralph Lauren × Apple × Nike × 5 Gum</span>
        </motion.footer>
      </motion.div>
    </div>
  );
};

export default LandingPage;
