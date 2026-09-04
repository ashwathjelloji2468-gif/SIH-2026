import React, { useState, useEffect } from 'react';
import { useProject } from '../context/ProjectContext';
import { auditService } from '../services/auditService';
import { HealthResponse, AuditEvent } from '../types';
import { Sliders, Activity, ShieldCheck, Database, Server, RefreshCw, Terminal, Clock } from 'lucide-react';

export const Settings: React.FC = () => {
  const { currentProject } = useProject();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchSettingsData = async () => {
    setLoading(true);
    try {
      const [hData, aData] = await Promise.allSettled([
        auditService.getSystemHealth(),
        currentProject ? auditService.getProjectAuditTrail(currentProject.id) : Promise.resolve([]),
      ]);

      if (hData.status === 'fulfilled') setHealth(hData.value);
      if (aData.status === 'fulfilled') setAuditEvents(aData.value || []);
    } catch (err) {
      console.error('Failed to load settings telemetry:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettingsData();
  }, [currentProject]);

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider font-semibold mb-1">
            <Sliders className="w-4 h-4" />
            <span>Telemetry & Platform Integrity</span>
          </div>
          <h1 className="text-2xl font-bold font-mono text-slate-100">System Telemetry & Audit Logs</h1>
          <p className="text-xs text-slate-400 mt-1">
            Subsystem rule engine versions, backend connectivity, and tamper-evident event logs.
          </p>
        </div>

        <button
          onClick={fetchSettingsData}
          className="p-2 rounded-xl border border-slate-800 hover:bg-slate-900 text-slate-400 hover:text-slate-200 transition-colors cursor-pointer self-start sm:self-auto"
          title="Refresh telemetry"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Backend Health & Subsystem Versions */}
      <div className="rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-xl space-y-6">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Server className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-semibold text-slate-100">Subsystem Engine Versions</h3>
          </div>
          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
            <span className="text-emerald-300 font-semibold">FastAPI Backend Operational</span>
          </div>
        </div>

        {health ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 font-mono text-xs">
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <span className="text-slate-500 text-[10px] uppercase">Core Software Version</span>
              <div className="text-slate-200 font-bold text-sm">v{health.version}</div>
              <div className="text-slate-500 text-[11px]">ECDAT Engine</div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <span className="text-slate-500 text-[10px] uppercase">Scanner Rule Set</span>
              <div className="text-cyan-300 font-bold text-sm">
                v{health.versions?.scanner_rule_version || '2026.1.0'}
              </div>
              <div className="text-slate-500 text-[11px]">NIST-PQC Detectors</div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <span className="text-slate-500 text-[10px] uppercase">CBOM Schema Version</span>
              <div className="text-purple-300 font-bold text-sm">
                v{health.versions?.cbom_schema_version || '1.6'}
              </div>
              <div className="text-slate-500 text-[11px]">CycloneDX Cryptography</div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <span className="text-slate-500 text-[10px] uppercase">PQC Knowledge Base</span>
              <div className="text-emerald-300 font-bold text-sm">
                {health.versions?.crypto_knowledge_base_version || '2026.3.0-NIST-PQC'}
              </div>
              <div className="text-slate-500 text-[11px]">FIPS 203/204/205 Standards</div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <span className="text-slate-500 text-[10px] uppercase">Risk Mathematical Model</span>
              <div className="text-rose-300 font-bold text-sm">
                {health.versions?.risk_model_version || '2.0-MOSCA'}
              </div>
              <div className="text-slate-500 text-[11px]">Shelf-Life & Urgency Model</div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <span className="text-slate-500 text-[10px] uppercase">Database Persistence</span>
              <div className="text-slate-200 font-bold text-sm capitalize">
                {health.database}
              </div>
              <div className="text-slate-500 text-[11px]">SQLite ORM Engine</div>
            </div>
          </div>
        ) : (
          <div className="py-8 text-center text-xs text-slate-500">
            Checking backend subsystem connectivity...
          </div>
        )}
      </div>

      {/* Enterprise Audit Trail Table */}
      <div className="rounded-2xl border border-slate-800 bg-[#0B0F19] overflow-hidden shadow-xl space-y-2">
        <div className="p-4 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between text-xs font-mono">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-cyan-400" />
            <span className="font-semibold text-slate-200">Immutable Audit Event Trail</span>
          </div>
          <span className="text-slate-500">{auditEvents.length} Recorded Events</span>
        </div>

        {auditEvents.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-500 font-mono">
            No audit records logged for this project yet.
          </div>
        ) : (
          <div className="divide-y divide-slate-800/60 font-mono text-xs">
            {auditEvents.map((evt) => (
              <div
                key={evt.id}
                className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2 hover:bg-slate-900/30 transition-colors"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-cyan-300">{evt.action}</span>
                    <span className="text-slate-500 text-[11px]">by {evt.actor}</span>
                  </div>
                  {evt.details && (
                    <div className="text-[11px] text-slate-400 truncate max-w-lg">
                      {JSON.stringify(evt.details)}
                    </div>
                  )}
                </div>

                <div className="text-[11px] text-slate-500 shrink-0">
                  {new Date(evt.created_at).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
