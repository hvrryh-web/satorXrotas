import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import './LoadingCorridor.css';

export const LoadingCorridor: React.FC = () => {
  const navigate = useNavigate();
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    // Phase transitions
    const phases = [
      setTimeout(() => setPhase(1), 500),   // Start moving
      setTimeout(() => setPhase(2), 2500),  // Speed up
      setTimeout(() => setPhase(3), 4000),  // Transition out
      setTimeout(() => navigate('/services'), 5000)  // Complete
    ];

    return () => phases.forEach(clearTimeout);
  }, [navigate]);

  return (
    <div className="loading-corridor">
      {/* 3D Corridor Effect */}
      <div className="corridor-container">
        {/* Walls */}
        <motion.div 
          className="corridor-wall corridor-wall--left"
          animate={{ 
            scaleX: phase >= 2 ? 0.3 : 1,
            opacity: phase >= 3 ? 0 : 1
          }}
          transition={{ duration: 1.5, ease: 'easeInOut' }}
        />
        <motion.div 
          className="corridor-wall corridor-wall--right"
          animate={{ 
            scaleX: phase >= 2 ? 0.3 : 1,
            opacity: phase >= 3 ? 0 : 1
          }}
          transition={{ duration: 1.5, ease: 'easeInOut' }}
        />
        
        {/* Floor & Ceiling */}
        <motion.div 
          className="corridor-floor"
          animate={{ 
            scaleY: phase >= 2 ? 0.3 : 1,
            opacity: phase >= 3 ? 0 : 1
          }}
          transition={{ duration: 1.5, ease: 'easeInOut' }}
        />
        <motion.div 
          className="corridor-ceiling"
          animate={{ 
            scaleY: phase >= 2 ? 0.3 : 1,
            opacity: phase >= 3 ? 0 : 1
          }}
          transition={{ duration: 1.5, ease: 'easeInOut' }}
        />

        {/* Moving Lines */}
        <div className="corridor-lines">
          {[...Array(20)].map((_, i) => (
            <motion.div
              key={i}
              className="corridor-line"
              initial={{ z: -1000, opacity: 0 }}
              animate={{ 
                z: phase >= 1 ? 500 : -1000,
                opacity: phase >= 3 ? 0 : [0, 1, 0]
              }}
              transition={{ 
                duration: phase >= 2 ? 0.5 : 2,
                delay: i * 0.1,
                repeat: phase < 3 ? Infinity : 0,
                ease: 'linear'
              }}
              style={{
                left: `${10 + (i % 8) * 10}%`,
                top: `${10 + Math.floor(i / 8) * 30}%`
              }}
            />
          ))}
        </div>

        {/* Center Content */}
        <AnimatePresence>
          {phase < 3 && (
            <motion.div 
              className="corridor-content"
              exit={{ opacity: 0, scale: 0.8 }}
            >
              <motion.div 
                className="corridor-loader"
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
              >
                <div className="loader-ring loader-ring--outer" />
                <div className="loader-ring loader-ring--inner" />
              </motion.div>
              
              <motion.p className="corridor-text">
                {phase === 0 && 'Initializing...'}
                {phase === 1 && 'Loading Services...'}
                {phase === 2 && 'Preparing Interface...'}
              </motion.p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Progress Bar */}
      <div className="corridor-progress">
        <motion.div 
          className="progress-bar"
          initial={{ width: '0%' }}
          animate={{ width: `${(phase + 1) * 33}%` }}
          transition={{ duration: 0.5 }}
        />
      </div>
    </div>
  );
};

export default LoadingCorridor;
