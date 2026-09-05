import React, { useState, useEffect } from 'react';
import { Play, ChevronDown, Check, Activity, Clock, Layers, Sparkles } from 'lucide-react';
import { useProject } from '../../context/ProjectContext';
import { auditService } from '../../services/auditService';
import { useLocation, useNavigate } from 'react-router-dom';
import { Sentriq3DLogo } from '../Three/Sentriq3DLogo';

export const Navbar: React.FC = () => {
  const { projects, currentProject, setCurrentProject, setIsScanModalOpen } = useProject();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [healthOk, setHealthOk] = useState<boolean | null>(null);

  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    let isMounted = true;
    const checkHealth = async () => {
      try {
        const res = await auditService.getSystemHealth();
        if (isMounted) setHealthOk(res.status === 'ok');
      } catch {
        if (isMounted) setHealthOk(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 25000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  // Map path to section title
  const sectionNames: Record<string, string> = {
    '/': 'Executive Dashboard',
    '/dashboard': 'Executive Dashboard',
    '/projects': 'Project Ingestion',
    '/scan': 'Scan Orchestrator',
    '/inventory': 'Cryptographic Inventory',
    '/risk': 'Mosca Urgency & Risk',
    '/migration': 'PQC Migration Planner',
    '/reports': 'CBOM & Assessment',
    '/settings': 'Telemetry & Audit',
  };

  const currentSection = sectionNames[location.pathname] || 'Overview';

  return (
    <header className="sticky top-0 z-40 flex h-16 w-full items-center justify-between border-b border-slate-800/80 bg-[#06080F]/95 px-4 md:px-7 backdrop-blur-xl">
      {/* Brand & Breadcrumbs & Project Selector */}
      <div className="flex items-center gap-4 md:gap-6">
        <div className="flex items-center gap-2.5 cursor-pointer" onClick={() => navigate('/')}>
          <Sentriq3DLogo size="sm" showText={true} />
          <div className="hidden sm:flex items-center gap-2 ml-1">
            <span className="rounded-full border border-cyan-500/30 bg-cyan-950/60 px-2 py-0.2 text-[9px] font-mono font-bold tracking-widest text-cyan-300">
              PQC INTELLIGENCE
            </span>
          </div>
          <div className="text-[10px] text-slate-400 flex items-center gap-1.5 font-mono ml-2">
            <span className="text-slate-500 hidden md:inline">Console /</span>
            <span className="text-cyan-400 font-semibold">{currentSection}</span>
          </div>
        </div>

        {/* Active Project Dropdown Switcher */}
        {projects.length > 0 && (
          <div className="relative">
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center gap-2 rounded-xl border border-slate-800 bg-[#0B0F19] px-3 py-1.5 text-xs font-medium text-slate-200 hover:border-slate-700 transition-colors cursor-pointer"
            >
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                <span className="max-w-[120px] sm:max-w-[180px] truncate font-mono text-cyan-300 font-semibold">
                  {currentProject ? currentProject.name : 'Select Project'}
                </span>
              </div>
              <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
            </button>

            {dropdownOpen && (
              <div className="absolute left-0 mt-2 w-64 rounded-xl border border-slate-800 bg-[#0B0F19] p-1.5 shadow-2xl z-50 divide-y divide-slate-800/60">
                <div className="px-3 py-2 text-[10px] font-mono uppercase tracking-wider text-slate-500">
                  Target Repositories ({projects.length})
                </div>
                <div className="py-1 max-h-60 overflow-y-auto">
                  {projects.map((proj) => (
                    <button
                      key={proj.id}
                      onClick={() => {
                        setCurrentProject(proj);
                        setDropdownOpen(false);
                      }}
                      className={`flex w-full items-center justify-between px-3 py-2 text-left text-xs font-mono rounded-lg transition-colors cursor-pointer ${
                        currentProject?.id === proj.id
                          ? 'bg-cyan-950/60 text-cyan-300 font-semibold'
                          : 'text-slate-300 hover:bg-slate-900'
                      }`}
                    >
                      <span className="truncate">{proj.name}</span>
                      {currentProject?.id === proj.id && (
                        <Check className="h-3.5 w-3.5 text-cyan-400" />
                      )}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Right Action Items */}
      <div className="flex items-center gap-3">
        {/* Threat Horizon Alert Pill */}
        <div className="hidden lg:flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-950/40 px-3 py-1 text-[11px] font-mono text-amber-300">
          <Clock className="w-3.5 h-3.5 text-amber-400" />
          <span>Threat Horizon: <strong>2033</strong></span>
        </div>

        {/* Backend API Health Pill */}
        <div
          className="flex items-center gap-1.5 rounded-full border border-slate-800 bg-slate-900/60 px-3 py-1 text-[11px] font-mono text-slate-300"
          title={healthOk ? 'FastAPI Backend Online' : 'Backend Connecting...'}
        >
          <span
            className={`w-2 h-2 rounded-full ${
              healthOk === true
                ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]'
                : healthOk === false
                ? 'bg-rose-500'
                : 'bg-amber-400 animate-pulse'
            }`}
          />
          <span className="hidden sm:inline">
            {healthOk === true ? 'API Connected' : healthOk === false ? 'API Offline' : 'Checking API...'}
          </span>
        </div>

        {/* Launch Scan Quick Trigger */}
        <button
          onClick={() => setIsScanModalOpen(true)}
          className="inline-flex items-center gap-1.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 px-3.5 py-1.5 text-xs font-bold text-slate-950 transition-all shadow-md shadow-cyan-950/50 hover:shadow-cyan-500/20 cursor-pointer active:scale-95"
        >
          <Play className="h-3.5 w-3.5 fill-current" />
          <span>Launch Scan</span>
        </button>
      </div>
    </header>
  );
};
