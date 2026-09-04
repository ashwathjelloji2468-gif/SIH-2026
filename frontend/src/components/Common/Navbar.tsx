import React, { useState, useEffect } from 'react';
import { Shield, Play, ChevronDown, Check, Activity, Clock, Layers, Sparkles } from 'lucide-react';
import { useProject } from '../../context/ProjectContext';
import { auditService } from '../../services/auditService';
import { useLocation } from 'react-router-dom';

export const Navbar: React.FC = () => {
  const { projects, currentProject, setCurrentProject, setIsScanModalOpen } = useProject();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [healthOk, setHealthOk] = useState<boolean | null>(null);
  const location = useLocation();

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
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-600/30 border border-cyan-500/40 text-cyan-400 shadow-sm shadow-cyan-950/40">
            <Shield className="h-4.5 w-4.5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-base font-extrabold tracking-wider text-slate-100 font-mono">
                SENTRIQ
              </span>
              <span className="hidden sm:inline-block rounded-full border border-cyan-500/30 bg-cyan-950/60 px-2 py-0.2 text-[9px] font-mono font-bold tracking-widest text-cyan-300">
                PQC INTELLIGENCE
              </span>
            </div>
            <div className="text-[10px] text-slate-400 flex items-center gap-1.5 font-mono">
              <span className="text-slate-500 hidden md:inline">Console /</span>
              <span className="text-cyan-400 font-semibold">{currentSection}</span>
            </div>
          </div>
        </div>

        <div className="hidden lg:block h-6 w-px bg-slate-800" />

        {/* Project Selector Dropdown */}
        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/90 px-3.5 py-1.5 text-xs text-slate-200 hover:border-slate-700 hover:bg-slate-900 transition-all cursor-pointer shadow-inner"
          >
            <Layers className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-400 text-[11px]">Repository:</span>
            <span className="font-mono font-semibold text-cyan-300 max-w-[130px] sm:max-w-[200px] truncate">
              {currentProject ? currentProject.name : 'Select Repository'}
            </span>
            <ChevronDown className="h-3.5 w-3.5 text-slate-400 ml-1" />
          </button>

          {dropdownOpen && (
            <div className="absolute left-0 mt-2 w-72 rounded-2xl border border-slate-800 bg-[#0B0F19] p-2 shadow-2xl z-50 animate-in fade-in zoom-in-95 duration-100">
              <div className="px-2.5 py-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-wider font-mono flex items-center justify-between border-b border-slate-800/80 mb-1">
                <span>Active Repositories</span>
                <span className="text-cyan-400">{projects.length} Available</span>
              </div>
              <div className="max-h-64 overflow-y-auto space-y-0.5">
                {projects.map((proj) => {
                  const isSelected = currentProject?.id === proj.id;
                  return (
                    <button
                      key={proj.id}
                      onClick={() => {
                        setCurrentProject(proj);
                        setDropdownOpen(false);
                      }}
                      className={`flex w-full items-center justify-between px-3 py-2 rounded-xl text-xs font-mono text-left transition-colors cursor-pointer ${
                        isSelected
                          ? 'bg-cyan-950/60 text-cyan-300 font-semibold border border-cyan-800/60'
                          : 'text-slate-300 hover:bg-slate-800/50'
                      }`}
                    >
                      <span className="truncate">{proj.name}</span>
                      {isSelected && <Check className="h-3.5 w-3.5 text-cyan-400 shrink-0 ml-2" />}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Right Telemetry Badges & Launch Action */}
      <div className="flex items-center gap-3 md:gap-4">
        {/* Threat Horizon Indicator */}
        <div className="hidden xl:flex items-center gap-2 rounded-full border border-rose-900/50 bg-rose-950/30 px-3 py-1 text-[11px] font-mono text-rose-300">
          <Clock className="w-3 h-3 text-rose-400" />
          <span>Threat Horizon: <strong>2033</strong></span>
        </div>

        {/* Backend Health Status */}
        <div className="flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900/80 px-2.5 py-1 text-[11px] font-mono text-slate-300">
          <span
            className={`h-2 w-2 rounded-full ${
              healthOk === true
                ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.9)]'
                : healthOk === false
                ? 'bg-rose-400 shadow-[0_0_8px_rgba(248,113,113,0.9)]'
                : 'bg-amber-400 animate-pulse'
            }`}
          />
          <span className="hidden sm:inline">{healthOk ? 'FastAPI 1.2.0 Connected' : 'API Connecting...'}</span>
          <span className="sm:hidden">{healthOk ? 'Live' : '...'}</span>
        </div>

        {/* Launch Scan Action */}
        <button
          onClick={() => setIsScanModalOpen(true)}
          className="flex items-center gap-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 px-4 py-2 text-xs font-bold text-slate-950 transition-all shadow-md shadow-cyan-950/60 hover:shadow-cyan-500/25 cursor-pointer active:scale-95"
        >
          <Play className="h-3.5 w-3.5 fill-current" />
          <span className="hidden sm:inline">Launch Scan</span>
          <span className="sm:hidden">Scan</span>
        </button>
      </div>
    </header>
  );
};
