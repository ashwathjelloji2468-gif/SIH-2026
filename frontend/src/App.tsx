import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ProjectProvider } from './context/ProjectContext';
import { Navbar } from './components/Common/Navbar';
import { Sidebar } from './components/Common/Sidebar';
import { ScanModal } from './components/Common/ScanModal';
import LandingPage from './pages/LandingPage';
import { Home } from './pages/Home';
import { Project } from './pages/Project';
import { Scan } from './pages/Scan';
import { Inventory } from './pages/Inventory';
import { Risk } from './pages/Risk';
import { Migration } from './pages/Migration';
import { Reports } from './pages/Reports';
import { Settings } from './pages/Settings';

/** Internal app layout with Navbar + Sidebar */
const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="min-h-screen bg-[#0B1120] bg-hex-pattern bg-radial-subtle text-slate-100 flex flex-col selection:bg-cyan-500/20 selection:text-cyan-300">
    {/* Top Global Navigation */}
    <Navbar />

    <div className="flex-1 flex w-full">
      {/* Left Sidebar */}
      <Sidebar />

      {/* Main Application Area */}
      <main className="flex-1 overflow-x-hidden p-4 md:p-8 max-w-7xl mx-auto w-full">
        {children}
      </main>
    </div>
  </div>
);

export const App: React.FC = () => {
  return (
    <ProjectProvider>
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
          <Route path="/migration" element={<AppLayout><Migration /></AppLayout>} />
          <Route path="/reports" element={<AppLayout><Reports /></AppLayout>} />
          <Route path="/settings" element={<AppLayout><Settings /></AppLayout>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>

        {/* Global Trigger Scan Modal (Available across all routes & landing page) */}
        <ScanModal />
      </BrowserRouter>
    </ProjectProvider>
  );
};

export default App;
