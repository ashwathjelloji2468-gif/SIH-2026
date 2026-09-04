import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderGit2,
  ScanSearch,
  Binary,
  ShieldAlert,
  GitFork,
  FileSpreadsheet,
  Sliders,
  Clock,
  ExternalLink,
} from 'lucide-react';
import { useProject } from '../../context/ProjectContext';

export const Sidebar: React.FC = () => {
  const { currentProject } = useProject();

  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Projects', path: '/projects', icon: FolderGit2 },
    { name: 'Scan Console', path: '/scan', icon: ScanSearch },
    { name: 'Inventory & Evidence', path: '/inventory', icon: Binary },
    { name: 'Risk & Mosca', path: '/risk', icon: ShieldAlert },
    { name: 'Migration & Sandbox', path: '/migration', icon: GitFork },
    { name: 'Reports & CBOM', path: '/reports', icon: FileSpreadsheet },
    { name: 'Settings & Audit', path: '/settings', icon: Sliders },
  ];

  // Mosca threat countdown: Target 2033
  const currentYear = new Date().getFullYear();
  const targetHorizonYear = 2033;
  const yearsRemaining = Math.max(0, targetHorizonYear - currentYear);

  return (
    <aside className="w-64 shrink-0 hidden md:flex flex-col border-r border-slate-800 bg-[#070A12] min-h-[calc(100vh-4rem)] p-3">
      {/* Navigation links */}
      <nav className="space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 shadow-sm font-semibold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.name}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Spacer */}
      <div className="mt-auto pt-6"></div>

      {/* Threat Horizon Widget */}
      <div className="rounded-xl border border-rose-900/40 bg-gradient-to-b from-rose-950/20 to-slate-900/50 p-3.5 mb-2">
        <div className="flex items-center justify-between text-xs text-rose-400 font-semibold mb-1">
          <div className="flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-rose-400 animate-pulse" />
            <span>Threat Horizon</span>
          </div>
          <span className="font-mono text-[11px] bg-rose-950/80 px-1.5 py-0.2 rounded border border-rose-800/50">
            {targetHorizonYear}
          </span>
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed mb-2">
          CRQC capability anticipated in <span className="text-slate-200 font-bold font-mono">~{yearsRemaining} years</span>. Harvest Now Decrypt Later (HNDL) is active today.
        </p>
        <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
          <div
            className="bg-gradient-to-r from-cyan-500 via-amber-500 to-rose-500 h-full rounded-full"
            style={{ width: `${Math.min(100, Math.max(10, (1 - yearsRemaining / 12) * 100))}%` }}
          />
        </div>
      </div>

      {/* NIST Standards Quick Link */}
      <div className="px-3 py-2 text-[10px] text-slate-500 flex items-center justify-between font-mono">
        <span>NIST FIPS 203/204/205</span>
        <span className="text-cyan-400">ACTIVE</span>
      </div>
    </aside>
  );
};
