import React, { useState, useEffect } from 'react';
import { Shield, Play, ChevronDown, Check, Activity, Terminal } from 'lucide-react';
import { useProject } from '../../context/ProjectContext';
import { auditService } from '../../services/auditService';

export const Navbar: React.FC = () => {
  const { projects, currentProject, setCurrentProject, setIsScanModalOpen } = useProject();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [healthOk, setHealthOk] = useState<boolean | null>(null);

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
    const interval = setInterval(checkHealth, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-800 bg-[#070A12]/90 px-4 md:px-6 backdrop-blur-md">
      {/* Brand & Active Project Selector */}
      <div className="flex items-center gap-4 md:gap-6">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-600/20 border border-cyan-500/30 text-cyan-400 shadow-inner">
            <Shield className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-base font-extrabold tracking-wider text-slate-100 font-mono">
                SENTRIQ
              </span>
              <span className="hidden sm:inline-block rounded border border-cyan-500/30 bg-cyan-950/40 px-1.5 py-0.2 text-[10px] font-mono font-semibold text-cyan-400">
                PQC 2.0
              </span>
            </div>
            <p className="text-[10px] text-slate-400 hidden sm:block">Quantum Migration Intelligence</p>
          </div>
        </div>

        {/* Project Selector Dropdown */}
        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/80 px-3 py-1.5 text-xs text-slate-200 hover:border-slate-700 transition-colors cursor-pointer"
          >
            <span className="text-slate-400">Project:</span>
            <span className="font-mono font-medium text-cyan-300 max-w-[140px] md:max-w-[200px] truncate">
              {currentProject ? currentProject.name : 'Select Project'}
            </span>
            <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
          </button>

          {dropdownOpen && (
            <div className="absolute left-0 mt-2 w-64 rounded-xl border border-slate-800 bg-[#0B0F19] p-1.5 shadow-2xl z-50">
              <div className="px-2 py-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Active Projects ({projects.length})
              </div>
              <div className="max-h-60 overflow-y-auto space-y-0.5">
                {projects.map((proj) => {
                  const isSelected = currentProject?.id === proj.id;
                  return (
                    <button
                      key={proj.id}
                      onClick={() => {
                        setCurrentProject(proj);
                        setDropdownOpen(false);
                      }}
                      className={`flex w-full items-center justify-between px-2.5 py-2 rounded-lg text-xs font-mono text-left transition-colors cursor-pointer ${
                        isSelected
                          ? 'bg-cyan-950/50 text-cyan-300 font-semibold'
                          : 'text-slate-300 hover:bg-slate-800/60'
                      }`}
                    >
                      <span className="truncate">{proj.name}</span>
                      {isSelected && <Check className="h-3.5 w-3.5 text-cyan-400 shrink-0" />}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Right Telemetry & Actions */}
      <div className="flex items-center gap-3 md:gap-4">
        {/* Backend Health Pulse */}
        <div className="hidden sm:flex items-center gap-2 rounded-full border border-slate-800/80 bg-slate-900/60 px-2.5 py-1 text-[11px] font-mono text-slate-400">
          <span
            className={`h-2 w-2 rounded-full ${
              healthOk === true
                ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]'
                : healthOk === false
                ? 'bg-rose-400 shadow-[0_0_8px_rgba(248,113,113,0.8)]'
                : 'bg-amber-400 animate-ping'
            }`}
          />
          <span>API {healthOk ? 'Connected' : 'Offline'}</span>
        </div>

        {/* Quick Run Scan CTA */}
        <button
          onClick={() => setIsScanModalOpen(true)}
          className="flex items-center gap-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 px-3.5 py-1.5 text-xs font-bold text-slate-950 transition-all shadow-md shadow-cyan-950/50 hover:shadow-cyan-500/20 cursor-pointer"
        >
          <Play className="h-3.5 w-3.5 fill-current" />
          <span className="hidden sm:inline">Launch Scan</span>
          <span className="sm:hidden">Scan</span>
        </button>
      </div>
    </header>
  );
};
