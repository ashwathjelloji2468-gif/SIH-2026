import React, { useState } from 'react';
import { Play, Loader2, Cpu, CheckCircle2, FileDiff, ShieldAlert } from 'lucide-react';
import { migrationService } from '../../services/migrationService';
import { SandboxSimulationResult } from '../../types';

interface SandboxSimulatorProps {
  planId: string;
}

export const SandboxSimulator: React.FC<SandboxSimulatorProps> = ({ planId }) => {
  const [pattern, setPattern] = useState<string>('RSA_TO_ML_KEM_HYBRID');
  const [simulationResult, setSimulationResult] = useState<SandboxSimulationResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleRunSimulation = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await migrationService.simulateTransformation(planId, pattern);
      setSimulationResult(res);
    } catch (err: any) {
      setError(err.message || 'Simulation execution failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-xl space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider font-semibold mb-1">
            <Cpu className="w-4 h-4" />
            <span>Isolated Sandbox Transformation</span>
          </div>
          <h3 className="text-base font-bold text-slate-100">Automated PQC Code Refactoring Simulation</h3>
          <p className="text-xs text-slate-400">
            Execute AST rewriting in a resource-constrained, network-isolated sandbox environment.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={pattern}
            onChange={(e) => setPattern(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs font-mono text-cyan-300 focus:outline-none focus:border-cyan-500 cursor-pointer"
          >
            <option value="RSA_TO_ML_KEM_HYBRID">RSA → ML-KEM Hybrid (FIPS 203)</option>
            <option value="ECDSA_TO_ML_DSA">ECDSA → ML-DSA (FIPS 204)</option>
            <option value="STATELESS_SLH_DSA">Fallback → SLH-DSA (FIPS 205)</option>
          </select>

          <button
            onClick={handleRunSimulation}
            disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-slate-950 font-bold text-xs shadow-md shadow-cyan-950/50 cursor-pointer transition-all"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Simulating...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                <span>Run Sandbox</span>
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-rose-950/50 border border-rose-800/60 text-xs text-rose-300">
          {error}
        </div>
      )}

      {/* Simulation Result Diff Viewer */}
      {simulationResult ? (
        <div className="rounded-xl border border-slate-800 bg-[#070A12] p-4 space-y-3 font-mono text-xs">
          <div className="flex items-center justify-between text-[11px] pb-2 border-b border-slate-800">
            <div className="flex items-center gap-2 text-emerald-400 font-semibold">
              <CheckCircle2 className="w-4 h-4" />
              <span>Status: {simulationResult.status}</span>
            </div>
            <span className="text-slate-400">
              Sandbox Path: <code className="text-cyan-300">{simulationResult.sandbox_path}</code>
            </span>
          </div>

          <div className="space-y-1">
            <div className="text-slate-400 font-sans text-xs font-semibold">Transformation Summary:</div>
            <p className="text-slate-300 leading-relaxed font-sans">
              {simulationResult.transformation.diff_summary}
            </p>
          </div>

          <div>
            <div className="text-slate-400 font-sans text-xs font-semibold mb-1">
              Modified Source Files ({simulationResult.transformation.files_modified.length}):
            </div>
            <div className="space-y-1">
              {simulationResult.transformation.files_modified.map((file, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 px-2.5 py-1.5 rounded bg-slate-900 border border-slate-800 text-slate-300"
                >
                  <FileDiff className="w-3.5 h-3.5 text-cyan-400" />
                  <span>{file}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="py-8 text-center text-xs text-slate-500 rounded-xl border border-dashed border-slate-800 bg-slate-950/40">
          Select a PQC pattern and click "Run Sandbox" to simulate safe automated code migration.
        </div>
      )}
    </div>
  );
};
