import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Pages
import { LandingPage } from './pages/LandingPage';
import { LoadingCorridor } from './pages/LoadingCorridor';
import { ServiceSelection } from './pages/ServiceSelection';

// Import design system CSS
import './styles/globals.css';
import './App.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 2,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="app">
          <Routes>
            {/* Landing Page */}
            <Route path="/" element={<LandingPage />} />
            
            {/* Loading Corridor */}
            <Route path="/loading" element={<LoadingCorridor />} />
            
            {/* Service Selection (Main Dashboard) */}
            <Route path="/services" element={<ServiceSelection />} />
            
            {/* Hub Routes - Placeholders for now */}
            <Route path="/analytics" element={<div>Analytics Hub (Coming Soon)</div>} />
            <Route path="/stats" element={<div>Stats Hub (Coming Soon)</div>} />
            <Route path="/info" element={<div>Info Hub (Coming Soon)</div>} />
            <Route path="/game" element={<div>Game Hub (Coming Soon)</div>} />
            
            {/* Redirect unknown routes */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
