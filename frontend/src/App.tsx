import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ProjectProvider } from './context/ProjectContext';
import { Navbar } from './components/Common/Navbar';
import { Sidebar } from './components/Common/Sidebar';
import { ScanModal } from './components/Common/ScanModal';
import { Home } from './pages/Home';
import { Project } from './pages/Project';
import { Scan } from './pages/Scan';
import { Inventory } from './pages/Inventory';
import { Risk } from './pages/Risk';
import { Migration } from './pages/Migration';
import { Reports } from './pages/Reports';
import { Settings } from './pages/Settings';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <ProjectProvider>
        <div className="min-h-screen bg-[#070A12] text-slate-100 flex flex-col selection:bg-cyan-500/20 selection:text-cyan-300">
          {/* Top Global Navigation */}
          <Navbar />

          <div className="flex-1 flex w-full">
            {/* Left Sidebar */}
            <Sidebar />

            {/* Main Application Area */}
            <main className="flex-1 overflow-x-hidden p-4 md:p-8 max-w-7xl mx-auto w-full">
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/projects" element={<Project />} />
                <Route path="/scan" element={<Scan />} />
                <Route path="/inventory" element={<Inventory />} />
                <Route path="/risk" element={<Risk />} />
                <Route path="/migration" element={<Migration />} />
                <Route path="/reports" element={<Reports />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </main>
          </div>

          {/* Quick Trigger Scan Modal */}
          <ScanModal />
        </div>
      </ProjectProvider>
    </BrowserRouter>
  );
};

export default App;
