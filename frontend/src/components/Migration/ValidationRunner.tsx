import React, { useState } from 'react';
import { Play, Loader2, CheckCircle2, XCircle, Terminal, ShieldCheck } from 'lucide-react';
import { validationService } from '../../services/validationService';
import { ValidationRun } from '../../types';

interface ValidationRunnerProps {
  planId: string;
}

export const ValidationRunner: React.FC<ValidationRunnerProps> = ({ planId }) => {
  const [validationRun, setValidationRun] = useState<ValidationRun | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleRunValidation = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await validationService.runValidation(planId);
      setValidationRun(res);
    } catch (err: any) {
      setError(err.message || 'Validation suite execution failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-xl space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-emerald-400 font-mono text-xs uppercase tracking-wider font-semibold mb-1">
            <ShieldCheck className="w-4 h-4" />
            <span>Automated Verification Suite</span>
          </div>
          <h3 className="text-base font-bold text-slate-100">Cryptographic Validation & Regression Engine</h3>
          <p className="text-xs text-slate-400">
            Execute build compilation, test harnesses, and measure post-transformation residual risk.
          </p>
        </div>

        <button
          onClick={handleRunValidation}
          disabled={loading}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-slate-950 font-bold text-xs shadow-md shadow-emerald-950/50 cursor-pointer transition-all shrink-0"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Executing Test Harness...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-current" />
              <span>Run Validation Suite</span>
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-rose-950/50 border border-rose-800/60 text-xs text-rose-300">
          {error}
        </div>
      )}

      {validationRun ? (
        <div className="space-y-4">
          {/* Test Status Indicators */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center gap-2.5">
              {validationRun.build_passed ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              ) : (
                <XCircle className="w-4 h-4 text-rose-400 shrink-0" />
              )}
              <div className="text-xs font-mono">
                <div className="text-slate-400 text-[10px]">Build Passed</div>
                <div className={validationRun.build_passed ? 'text-emerald-300 font-bold' : 'text-rose-300 font-bold'}>
                  {validationRun.build_passed ? 'PASSED' : 'FAILED'}
                </div>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center gap-2.5">
              {validationRun.unit_tests_passed ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              ) : (
                <XCircle className="w-4 h-4 text-rose-400 shrink-0" />
              )}
              <div className="text-xs font-mono">
                <div className="text-slate-400 text-[10px]">Unit Tests</div>
                <div className={validationRun.unit_tests_passed ? 'text-emerald-300 font-bold' : 'text-rose-300 font-bold'}>
                  {validationRun.unit_tests_passed ? '100% OK' : 'FAILED'}
                </div>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center gap-2.5">
              {validationRun.crypto_tests_passed ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              ) : (
                <XCircle className="w-4 h-4 text-rose-400 shrink-0" />
              )}
              <div className="text-xs font-mono">
                <div className="text-slate-400 text-[10px]">PQC Kat Tests</div>
                <div className={validationRun.crypto_tests_passed ? 'text-emerald-300 font-bold' : 'text-rose-300 font-bold'}>
                  {validationRun.crypto_tests_passed ? 'VERIFIED' : 'FAILED'}
                </div>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center gap-2.5">
              <div className="text-xs font-mono">
                <div className="text-slate-400 text-[10px]">Residual Risk</div>
                <div className="text-cyan-300 font-bold text-sm">
                  {validationRun.residual_risk_score} / 100
                </div>
              </div>
            </div>
          </div>

          {/* Validation Logs Console */}
          {validationRun.logs && (
            <div className="rounded-xl border border-slate-800 bg-[#0B0F19] overflow-hidden">
              <div className="flex items-center gap-2 px-3.5 py-2 bg-slate-900/80 border-b border-slate-800 text-xs text-slate-400 font-mono">
                <Terminal className="w-3.5 h-3.5 text-cyan-400" />
                <span>Test Execution Stream</span>
              </div>
              <pre className="p-4 text-[11px] font-mono text-slate-300 whitespace-pre-wrap max-h-60 overflow-y-auto leading-relaxed">
                {validationRun.logs}
              </pre>
            </div>
          )}
        </div>
      ) : (
        <div className="py-8 text-center text-xs text-slate-500 rounded-xl border border-dashed border-slate-800 bg-slate-950/40">
          Click "Run Validation Suite" to execute automated unit, integration, and PQC KAT test verification.
        </div>
      )}
    </div>
  );
};
