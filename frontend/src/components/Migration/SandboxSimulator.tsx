import React, { useState } from 'react';
import { Play, Loader2, Cpu, CheckCircle2, FileDiff, ShieldAlert, ArrowRight, Code } from 'lucide-react';
import { migrationService } from '../../services/migrationService';
import { SandboxSimulationResult } from '../../types';

interface SandboxSimulatorProps {
  planId: string;
}

export const SandboxSimulator: React.FC<SandboxSimulatorProps> = ({ planId }) => {
  const [pattern, setPattern] = useState<string>('RSA_TO_ML_KEM_HYBRID');
  const [simulationResult, setSimulationResult] = useState<any | null>(null);
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
    <div className="rounded-3xl border border-slate-800 bg-[#0B0F19] p-6 sm:p-8 shadow-2xl space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider font-semibold mb-1">
            <Cpu className="w-4 h-4" />
            <span>Isolated Sandbox Transformation</span>
          </div>
          <h3 className="text-xl font-bold font-mono text-slate-100">Automated PQC Code Refactoring Simulation</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Execute AST rewriting in a resource-constrained, network-isolated sandbox environment.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <select
            value={pattern}
            onChange={(e) => setPattern(e.target.value)}
            className="px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs font-mono text-cyan-300 focus:outline-none focus:border-cyan-500 cursor-pointer"
          >
            <option value="RSA_TO_ML_KEM_HYBRID">RSA → ML-KEM-768 Hybrid (FIPS 203)</option>
            <option value="ECDSA_TO_ML_DSA">ECDSA → ML-DSA-65 Lattice (FIPS 204)</option>
          </select>

          <button
            onClick={handleRunSimulation}
            disabled={loading}
            className="inline-flex items-center gap-2 px-5 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-slate-950 font-bold text-xs shadow-md shadow-cyan-950/50 cursor-pointer transition-all active:scale-95 shrink-0"
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
        <div className="p-3.5 rounded-2xl bg-rose-950/50 border border-rose-800/60 text-xs text-rose-300">
          {error}
        </div>
      )}

      {/* Simulation Result Diff Viewer */}
      {simulationResult ? (
        <div className="rounded-2xl border border-slate-800 bg-[#06080F] p-5 space-y-4 font-mono text-xs">
          <div className="flex flex-wrap items-center justify-between text-[11px] pb-3 border-b border-slate-800/80 gap-2">
            <div className="flex items-center gap-2 text-emerald-400 font-bold">
              <CheckCircle2 className="w-4 h-4" />
              <span>Status: {simulationResult.status}</span>
            </div>
            <span className="text-slate-400 truncate max-w-md">
              Sandbox Dir: <code className="text-cyan-300">{simulationResult.sandbox_path}</code>
            </span>
          </div>

          <div className="space-y-1 font-sans">
            <div className="text-slate-400 text-xs font-semibold">Transformation Rationale:</div>
            <p className="text-slate-300 leading-relaxed text-xs">
              {simulationResult.transformation.diff_summary}
            </p>
          </div>

          {/* Side-by-Side Code Diff Viewer */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
            {/* Original Classical Snippet */}
            <div className="rounded-xl border border-rose-900/40 bg-rose-950/10 p-3.5 space-y-2">
              <div className="flex items-center justify-between text-rose-400 font-bold text-[11px]">
                <span>- Classical Implementation (Vulnerable)</span>
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 rounded bg-rose-950 border border-rose-900">
                  Original
                </span>
              </div>
              <pre className="p-2.5 rounded-lg bg-slate-950/80 text-rose-200/90 text-[11px] overflow-x-auto whitespace-pre leading-relaxed border border-rose-950">
                {simulationResult.transformation.original_snippet ||
                  'from cryptography.hazmat.primitives.asymmetric import rsa\nkey = rsa.generate_private_key(...) # RSA-2048'}
              </pre>
            </div>

            {/* Transformed PQC Snippet */}
            <div className="rounded-xl border border-emerald-900/40 bg-emerald-950/10 p-3.5 space-y-2">
              <div className="flex items-center justify-between text-emerald-400 font-bold text-[11px]">
                <span>+ NIST Standard PQC Implementation</span>
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 rounded bg-emerald-950 border border-emerald-900">
                  Transformed
                </span>
              </div>
              <pre className="p-2.5 rounded-lg bg-slate-950/80 text-emerald-200/90 text-[11px] overflow-x-auto whitespace-pre leading-relaxed border border-emerald-950">
                {simulationResult.transformation.transformed_snippet ||
                  'from pqcrypto.kem import ml_kem_768\npublic_key, secret_key = ml_kem_768.generate_keypair()'}
              </pre>
            </div>
          </div>

          <div className="pt-2">
            <div className="text-slate-400 font-sans text-xs font-semibold mb-1.5">
              Refactored Source Files ({simulationResult.transformation.files_modified?.length || 0}):
            </div>
            <div className="space-y-1">
              {simulationResult.transformation.files_modified?.map((file: string, idx: number) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-900/60 border border-slate-800 text-slate-300"
                >
                  <FileDiff className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                  <span className="truncate">{file}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="py-12 text-center text-xs text-slate-500 rounded-2xl border border-dashed border-slate-800 bg-[#06080F]/40 font-mono">
          Select a Post-Quantum pattern and click "Run Sandbox" to simulate safe automated code migration.
        </div>
      )}
    </div>
  );
};
