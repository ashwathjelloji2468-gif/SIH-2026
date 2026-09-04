import React, { useState, useEffect } from 'react';
import { useProject } from '../context/ProjectContext';
import { scanService } from '../services/scanService';
import { Scan as ScanType } from '../types';
import { StatusBadge } from '../components/Common/StatusBadge';
import { ScanSearch, Play, RefreshCw, XCircle, RotateCcw, Clock, Terminal, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Scan: React.FC = () => {
  const { currentProject, setIsScanModalOpen, refreshLatestScan } = useProject();
  const [scans, setScans] = useState<ScanType[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchScans = async () => {
    if (!currentProject) {
      setScans([]);
      setLoading(false);
      return;
    }
    try {
      const data = await scanService.getProjectScans(currentProject.id);
      // Sort newest first
      const sorted = [...data].sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
      setScans(sorted);
    } catch (err) {
      console.error('Failed to load project scans:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScans();
  }, [currentProject]);

  // Polling if any scan is RUNNING or QUEUED
  useEffect(() => {
    const hasActiveScan = scans.some((s) => s.status === 'RUNNING' || s.status === 'QUEUED');
    if (!hasActiveScan) return;

    const interval = setInterval(() => {
      fetchScans();
      refreshLatestScan();
    }, 2500);

    return () => clearInterval(interval);
  }, [scans, currentProject]);

  const handleCancelScan = async (scanId: string) => {
    setActionLoading(scanId);
    try {
      await scanService.cancelScan(scanId);
      await fetchScans();
      await refreshLatestScan();
    } catch (err) {
      console.error('Failed to cancel scan:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleRerunScan = async (scanId: string) => {
    setActionLoading(scanId);
    try {
      await scanService.rerunScan(scanId);
      await fetchScans();
      await refreshLatestScan();
    } catch (err) {
      console.error('Failed to rerun scan:', err);
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider font-semibold mb-1">
            <ScanSearch className="w-4 h-4" />
            <span>Orchestration Console</span>
          </div>
          <h1 className="text-2xl font-bold font-mono text-slate-100">Cryptographic Discovery Scans</h1>
          <p className="text-xs text-slate-400 mt-1">
            Target Project: <span className="text-cyan-300 font-mono">{currentProject?.name || 'None'}</span> • Rule Engine: <span className="font-mono text-slate-200">2026.1.0</span>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchScans}
            className="p-2 rounded-xl border border-slate-800 hover:bg-slate-900 text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
            title="Refresh scan history"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={() => setIsScanModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs shadow-md shadow-cyan-950/50 cursor-pointer transition-all"
          >
            <Play className="w-4 h-4 fill-current" />
            <span>Launch Scan</span>
          </button>
        </div>
      </div>

      {/* Scans List */}
      <div className="rounded-2xl border border-slate-800 bg-[#0B0F19] overflow-hidden shadow-xl">
        <div className="p-4 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between text-xs font-mono">
          <span className="font-semibold text-slate-200">Scan Execution History ({scans.length})</span>
          <span className="text-slate-500">Live Polling Active</span>
        </div>

        {scans.length === 0 ? (
          <div className="py-16 text-center text-xs text-slate-500 font-mono">
            No scans recorded for this repository. Click "Launch Scan" to start cryptographic discovery.
          </div>
        ) : (
          <div className="divide-y divide-slate-800/60 font-mono text-xs">
            {scans.map((scan) => {
              const isRunning = scan.status === 'RUNNING' || scan.status === 'QUEUED';
              return (
                <div
                  key={scan.id}
                  className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-slate-900/30 transition-colors"
                >
                  <div className="space-y-1.5 max-w-xl">
                    <div className="flex items-center gap-2.5">
                      <StatusBadge type="scan" value={scan.status} />
                      <span className="font-bold text-slate-200 truncate">{scan.target_path}</span>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-500">
                      <span>ID: {scan.id.slice(0, 8)}</span>
                      <span>•</span>
                      <span>Type: {scan.scan_type}</span>
                      <span>•</span>
                      <span>CBOM Spec: v{scan.cbom_version}</span>
                      <span>•</span>
                      <span>Rules: v{scan.scanner_rule_version}</span>
                    </div>

                    {scan.error_message && (
                      <div className="flex items-center gap-1.5 text-rose-400 text-[11px] mt-1 bg-rose-950/40 px-2 py-0.5 rounded border border-rose-900/40">
                        <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                        <span>{scan.error_message}</span>
                      </div>
                    )}
                  </div>

                  {/* Actions & Timestamps */}
                  <div className="flex items-center gap-4 shrink-0">
                    <div className="text-right text-[11px] text-slate-400">
                      <div>Created: {new Date(scan.created_at).toLocaleTimeString()}</div>
                      {scan.completed_at && (
                        <div className="text-slate-500">Done: {new Date(scan.completed_at).toLocaleTimeString()}</div>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      {isRunning ? (
                        <button
                          onClick={() => handleCancelScan(scan.id)}
                          disabled={actionLoading === scan.id}
                          className="px-3 py-1.5 rounded-lg border border-rose-800/70 bg-rose-950/50 hover:bg-rose-900/60 text-rose-300 text-xs font-sans font-semibold cursor-pointer transition-colors"
                        >
                          Cancel
                        </button>
                      ) : (
                        <>
                          <button
                            onClick={() => handleRerunScan(scan.id)}
                            disabled={actionLoading === scan.id}
                            className="p-2 rounded-lg border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-cyan-300 transition-colors cursor-pointer"
                            title="Rerun scan"
                          >
                            <RotateCcw className="w-3.5 h-3.5" />
                          </button>
                          <Link
                            to="/reports"
                            className="px-3 py-1.5 rounded-lg border border-cyan-800/60 bg-cyan-950/40 hover:bg-cyan-900/50 text-cyan-300 text-xs font-sans font-semibold transition-colors"
                          >
                            View CBOM
                          </Link>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
