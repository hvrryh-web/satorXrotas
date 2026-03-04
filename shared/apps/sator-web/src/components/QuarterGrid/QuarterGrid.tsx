import React, { useState, useRef, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './QuarterGrid.css';

export interface QuarterCell {
  id: string;
  title: string;
  icon: React.ReactNode;
  content: React.ReactNode;
  color: string;
  isExpanded?: boolean;
  isCollapsed?: boolean;
}

interface QuarterGridProps {
  cells: QuarterCell[];
  hubContent?: React.ReactNode;
  onCellClick?: (cellId: string) => void;
  className?: string;
}

interface ResizeState {
  isResizing: boolean;
  direction: 'horizontal' | 'vertical' | 'corner' | null;
  startX: number;
  startY: number;
  initialSizes: number[];
}

export const QuarterGrid: React.FC<QuarterGridProps> = ({
  cells,
  hubContent,
  onCellClick,
  className = ''
}) => {
  const [expandedCell, setExpandedCell] = useState<string | null>(null);
  const [hubExpanded, setHubExpanded] = useState(false);
  const [columnSizes, setColumnSizes] = useState([50, 50]);
  const [rowSizes, setRowSizes] = useState([50, 50]);
  const [resizeState, setResizeState] = useState<ResizeState>({
    isResizing: false,
    direction: null,
    startX: 0,
    startY: 0,
    initialSizes: []
  });

  const gridRef = useRef<HTMLDivElement>(null);

  // Handle cell expansion
  const handleCellClick = (cellId: string) => {
    if (expandedCell === cellId) {
      setExpandedCell(null);
    } else {
      setExpandedCell(cellId);
    }
    onCellClick?.(cellId);
  };

  // Handle hub expansion
  const handleHubClick = () => {
    setHubExpanded(true);
  };

  const handleHubClose = () => {
    setHubExpanded(false);
  };

  // Resize handlers
  const handleResizeStart = useCallback((
    e: React.MouseEvent,
    direction: 'horizontal' | 'vertical' | 'corner'
  ) => {
    e.preventDefault();
    e.stopPropagation();
    
    setResizeState({
      isResizing: true,
      direction,
      startX: e.clientX,
      startY: e.clientY,
      initialSizes: direction === 'horizontal' ? columnSizes : 
                    direction === 'vertical' ? rowSizes : 
                    [...columnSizes, ...rowSizes]
    });
  }, [columnSizes, rowSizes]);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!resizeState.isResizing || !gridRef.current) return;

      const rect = gridRef.current.getBoundingClientRect();
      const deltaX = ((e.clientX - resizeState.startX) / rect.width) * 100;
      const deltaY = ((e.clientY - resizeState.startY) / rect.height) * 100;

      if (resizeState.direction === 'horizontal') {
        const newSize = Math.max(20, Math.min(80, resizeState.initialSizes[0] + deltaX));
        setColumnSizes([newSize, 100 - newSize]);
      } else if (resizeState.direction === 'vertical') {
        const newSize = Math.max(20, Math.min(80, resizeState.initialSizes[0] + deltaY));
        setRowSizes([newSize, 100 - newSize]);
      } else if (resizeState.direction === 'corner') {
        const newColSize = Math.max(20, Math.min(80, resizeState.initialSizes[0] + deltaX));
        const newRowSize = Math.max(20, Math.min(80, resizeState.initialSizes[2] + deltaY));
        setColumnSizes([newColSize, 100 - newColSize]);
        setRowSizes([newRowSize, 100 - newRowSize]);
      }
    };

    const handleMouseUp = () => {
      setResizeState(prev => ({ ...prev, isResizing: false, direction: null }));
    };

    if (resizeState.isResizing) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = resizeState.direction === 'horizontal' ? 'col-resize' :
                                    resizeState.direction === 'vertical' ? 'row-resize' : 'nwse-resize';
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
    };
  }, [resizeState]);

  // Get cell position styles
  const getCellStyle = (index: number): React.CSSProperties => {
    const isExpanded = expandedCell === cells[index].id;
    const isCollapsed = expandedCell !== null && expandedCell !== cells[index].id;

    if (isExpanded) {
      return {
        gridColumn: '1 / -1',
        gridRow: '1 / -1',
        zIndex: 10
      };
    }

    if (isCollapsed) {
      return {
        opacity: 0.2,
        pointerEvents: 'none',
        transform: 'scale(0.95)'
      };
    }

    return {};
  };

  return (
    <div 
      ref={gridRef}
      className={`quarter-grid ${className} ${resizeState.isResizing ? 'is-resizing' : ''}`}
      style={{
        gridTemplateColumns: `${columnSizes[0]}% ${columnSizes[1]}%`,
        gridTemplateRows: `${rowSizes[0]}% ${rowSizes[1]}%`
      }}
    >
      {cells.map((cell, index) => (
        <QuarterCellComponent
          key={cell.id}
          cell={cell}
          style={getCellStyle(index)}
          onClick={() => handleCellClick(cell.id)}
          onResizeStart={handleResizeStart}
          showHandles={!expandedCell && index < 3}
          index={index}
        />
      ))}

      {/* Center Hub */}
      {hubContent && (
        <HubButton 
          onClick={handleHubClick}
          isExpanded={hubExpanded}
        />
      )}

      {/* Expanded Hub Overlay */}
      <AnimatePresence>
        {hubExpanded && hubContent && (
          <HubOverlay onClose={handleHubClose}>
            {hubContent}
          </HubOverlay>
        )}
      </AnimatePresence>
    </div>
  );
};

// Quarter Cell Component
interface QuarterCellComponentProps {
  cell: QuarterCell;
  style: React.CSSProperties;
  onClick: () => void;
  onResizeStart: (e: React.MouseEvent, direction: 'horizontal' | 'vertical' | 'corner') => void;
  showHandles: boolean;
  index: number;
}

const QuarterCellComponent: React.FC<QuarterCellComponentProps> = ({
  cell,
  style,
  onClick,
  onResizeStart,
  showHandles,
  index
}) => {
  return (
    <motion.div
      className={`quarter-cell quarter-cell--${cell.id}`}
      style={{
        ...style,
        borderColor: cell.color
      }}
      onClick={onClick}
      layout
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      whileHover={{ 
        boxShadow: `0 0 30px ${cell.color}40`,
        borderColor: cell.color
      }}
    >
      {/* Cell Header */}
      <div className="quarter-cell__header" style={{ background: `${cell.color}20` }}>
        <span className="quarter-cell__icon">{cell.icon}</span>
        <h3 className="quarter-cell__title">{cell.title}</h3>
      </div>

      {/* Cell Content */}
      <div className="quarter-cell__content">
        {cell.content}
      </div>

      {/* Resize Handles */}
      {showHandles && (
        <>
          {/* Right handle (horizontal resize) */}
          {(index === 0 || index === 2) && (
            <div
              className="resize-handle resize-handle--horizontal"
              onMouseDown={(e) => onResizeStart(e, 'horizontal')}
              title="Drag to resize horizontally"
            />
          )}
          
          {/* Bottom handle (vertical resize) */}
          {(index === 0 || index === 1) && (
            <div
              className="resize-handle resize-handle--vertical"
              onMouseDown={(e) => onResizeStart(e, 'vertical')}
              title="Drag to resize vertically"
            />
          )}
          
          {/* Corner handle (both directions) */}
          {index === 0 && (
            <div
              className="resize-handle resize-handle--corner"
              onMouseDown={(e) => onResizeStart(e, 'corner')}
              title="Drag to resize both directions"
            />
          )}
        </>
      )}

      {/* Expand Indicator */}
      <div className="quarter-cell__expand-indicator">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" />
        </svg>
      </div>
    </motion.div>
  );
};

// Hub Button Component
interface HubButtonProps {
  onClick: () => void;
  isExpanded: boolean;
}

const HubButton: React.FC<HubButtonProps> = ({ onClick, isExpanded }) => {
  return (
    <motion.button
      className="quarter-hub"
      onClick={onClick}
      initial={{ scale: 0, rotate: -180 }}
      animate={{ scale: 1, rotate: 0 }}
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.95 }}
      transition={{ type: 'spring', stiffness: 260, damping: 20 }}
      style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        x: '-50%',
        y: '-50%',
        zIndex: 100
      }}
    >
      <span className="quarter-hub__icon">?</span>
      <span className="quarter-hub__label">HELP</span>
    </motion.button>
  );
};

// Hub Overlay Component
interface HubOverlayProps {
  children: React.ReactNode;
  onClose: () => void;
}

const HubOverlay: React.FC<HubOverlayProps> = ({ children, onClose }) => {
  return (
    <motion.div
      className="hub-overlay"
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      exit={{ scale: 0, opacity: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 1000,
        background: 'var(--glass-dark)',
        backdropFilter: 'blur(20px)'
      }}
    >
      {/* Close Button */}
      <motion.button
        className="hub-overlay__close"
        onClick={onClose}
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.3 }}
        whileHover={{ scale: 1.1, rotate: 90 }}
      >
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M18 6L6 18M6 6l12 12" />
        </svg>
      </motion.button>

      {/* Content */}
      <motion.div
        className="hub-overlay__content"
        initial={{ y: 50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.4 }}
      >
        {children}
      </motion.div>
    </motion.div>
  );
};

export default QuarterGrid;
