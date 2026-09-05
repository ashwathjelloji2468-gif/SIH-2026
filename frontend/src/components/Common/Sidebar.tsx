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
  ShieldCheck,
  ChevronRight,
  ExternalLink,
} from 'lucide-react';
import { useProject } from '../../context/ProjectContext';

export const Sidebar: React.FC = () => {
  const { currentProject } = useProject();

  const navigationSections = [
    {
      title: 'Discovery & Inventory',
      items: [
        { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
        { name: 'Repositories', path: '/projects', icon: FolderGit2 },
        { name: 'Scan Console', path: '/scan', icon: ScanSearch },
        { name: 'Inventory & Evidence', path: '/inventory', icon: Binary },
      ],
    },
    {
      title: 'Risk & Threat Science',
      items: [
        { name: 'Risk & Mosca Theorem', path: '/risk', icon: ShieldAlert },
      ],
    },
    {
      title: 'Transition & Action',
      items: [
        { name: 'Migration & Sandbox', path: '/migration', icon: GitFork },
      ],
    },
    {
      title: 'Governance & Compliance',
      items: [
        { name: 'CBOM & Reports', path: '/reports', icon: FileSpreadsheet },
        { name: 'Telemetry & Audit', path: '/settings', icon: Sliders },
      ],
    },
  ];

  const currentYear = new Date().getFullYear();
  const targetHorizonYear = 2033;
  const yearsRemaining = Math.max(0, targetHorizonYear - currentYear);

  return (
    <aside className="w-64 shrink-0 hidden md:flex flex-col border-r border-slate-800/80 bg-[#06080F] min-h-[calc(100vh-4rem)] p-3.5 space-y-6">
      {/* Navigation Sections */}
      <nav className="space-y-5">
        {navigationSections.map((section) => (
          <div key={section.title} className="space-y-1">
            <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-500 font-mono">
              {section.title}
            </div>
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    end={item.path === '/'}
                    className={({ isActive }) =>
                      `group flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-all ${
                        isActive
                          ? 'bg-cyan-950/50 text-cyan-300 border border-cyan-800/60 font-semibold shadow-xs'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50 border border-transparent'
                      }`
                    }
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className="w-4 h-4 shrink-0 transition-transform group-hover:scale-105" />
                      <span>{item.name}</span>
                    </div>
                    <ChevronRight className="w-3.5 h-3.5 text-slate-600 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </NavLink>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Threat Horizon Alert Widget */}
      <div className="rounded-2xl border border-rose-950/70 bg-gradient-to-b from-rose-950/20 to-slate-950/60 p-4 space-y-2.5">
        <div className="flex items-center justify-between text-xs text-rose-400 font-semibold">
          <div className="flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-rose-400 animate-pulse" />
            <span className="font-mono text-[11px] uppercase tracking-wider">Threat Horizon</span>
          </div>
          <span className="font-mono text-xs font-bold bg-rose-950 text-rose-300 px-1.5 py-0.2 rounded border border-rose-800/60">
            {targetHorizonYear}
          </span>
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed font-sans">
          Quantum cryptanalysis capabilities estimated in <strong className="text-slate-200 font-mono">~{yearsRemaining} years</strong>. <em>Harvest Now, Decrypt Later (HNDL)</em> interception is active today.
        </p>
        <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden p-0.2 border border-slate-800">
          <div
            className="bg-gradient-to-r from-cyan-500 via-amber-500 to-rose-500 h-full rounded-full"
            style={{ width: `${Math.min(100, Math.max(15, (1 - yearsRemaining / 12) * 100))}%` }}
          />
        </div>
      </div>

      {/* PQC Compliance Standard Footer */}
      <div className="px-3 py-1.5 rounded-xl bg-slate-900/40 border border-slate-800/80 flex items-center justify-between text-[10px] font-mono text-slate-500">
        <div className="flex items-center gap-1.5">
          <ShieldCheck className="w-3 h-3 text-cyan-400" />
          <span>NIST FIPS 203/204/205</span>
        </div>
        <span className="text-emerald-400 font-bold">READY</span>
      </div>
    </aside>
  );
};
