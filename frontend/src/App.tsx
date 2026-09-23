import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ProjectProvider } from './context/ProjectContext';
import { Navbar } from './components/Common/Navbar';
import { Sidebar } from './components/Common/Sidebar';
import { ScanModal } from './components/Common/ScanModal';
import { SentriqLoader } from './components/Common/SentriqLoader';
import { SentriqWelcomeBanner } from './components/Guide/SentriqWelcomeBanner';
import { ContextualHelpDrawer } from './components/Guide/ContextualHelpDrawer';
import { GuidedTourOverlay } from './components/Guide/GuidedTourOverlay';
import LandingPage from './pages/LandingPage';
import { Home } from './pages/Home';
import { Project } from './pages/Project';
import { Scan } from './pages/Scan';
import { Inventory } from './pages/Inventory';
import { Risk } from './pages/Risk';
import { Migration } from './pages/Migration';
import { Recommendations } from './pages/Recommendations';
import { Reports } from './pages/Reports';
import { BusinessCriticality } from './pages/BusinessCriticality';
import { Settings } from './pages/Settings';
import { QARS } from './pages/QARS';
import { Guide } from './pages/Guide';

/** Internal app layout with Navbar + Sidebar + Global Help Overlays */
const AppLayout: React.FC<{ children: React.ReactNode; onStartTour?: () => void }> = ({ children, onStartTour }) => {
  const [isTourActive, setIsTourActive] = useState(false);

  const startTour = () => {
    setIsTourActive(true);
    if (onStartTour) onStartTour();
  };

  return (
    <div className="min-h-screen bg-[#0B1120] bg-hex-pattern bg-radial-subtle text-slate-100 flex flex-col selection:bg-cyan-500/20 selection:text-cyan-300">
      {/* Top Global Navigation */}
      <Navbar />

      <div className="flex-1 flex w-full">
        {/* Left Sidebar */}
        <Sidebar />

        {/* Main Application Area */}
        <main className="flex-1 overflow-x-hidden p-4 md:p-8 max-w-7xl mx-auto w-full">
          <SentriqWelcomeBanner onStartTour={startTour} />
          {children}
        </main>
      </div>

      {/* Page-Aware Contextual Help Drawer & Guided Tour Overlay */}
      <ContextualHelpDrawer onStartTour={startTour} />
      <GuidedTourOverlay isActive={isTourActive} onClose={() => setIsTourActive(false)} />
    </div>
  );
};

export const App: React.FC = () => {
  const [initializing, setInitializing] = useState<boolean>(true);
  const [globalTourActive, setGlobalTourActive] = useState<boolean>(false);

  useEffect(() => {
    // Smooth 1.4s startup initialization sequence
    const timer = setTimeout(() => {
      setInitializing(false);
    }, 1400);
    return () => clearTimeout(timer);
  }, []);

  return (
    <ProjectProvider>
      {/* Full-Screen Premium Startup Loader */}
      <SentriqLoader isLoading={initializing} />

      <BrowserRouter>
        <Routes>
          {/* Public Landing Page — standalone layout, no sidebar */}
          <Route path="/" element={<LandingPage />} />

          {/* Internal Application Routes — with Navbar + Sidebar */}
          <Route path="/dashboard" element={<AppLayout><Home /></AppLayout>} />
          <Route path="/projects" element={<AppLayout><Project /></AppLayout>} />
          <Route path="/scan" element={<AppLayout><Scan /></AppLayout>} />
          <Route path="/inventory" element={<AppLayout><Inventory /></AppLayout>} />
          <Route path="/risk" element={<AppLayout><Risk /></AppLayout>} />
          <Route path="/qars" element={<AppLayout><QARS /></AppLayout>} />
          <Route path="/recommendations" element={<AppLayout><Recommendations /></AppLayout>} />
          <Route path="/migration" element={<AppLayout><Migration /></AppLayout>} />
          <Route path="/reports" element={<AppLayout><Reports /></AppLayout>} />
          <Route path="/business-criticality" element={<AppLayout><BusinessCriticality /></AppLayout>} />
          <Route path="/settings" element={<AppLayout><Settings /></AppLayout>} />
          <Route path="/guide" element={<AppLayout><Guide onStartTour={() => setGlobalTourActive(true)} /></AppLayout>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>

        {/* Global Trigger Scan Modal */}
        <ScanModal />
      </BrowserRouter>
    </ProjectProvider>
  );
};

export default App;
