import React, { useState } from 'react';
import { Play, Loader2, CheckCircle2, XCircle, AlertTriangle, HelpCircle, Terminal, ShieldCheck, Clock } from 'lucide-react';
import { validationService } from '../../services/validationService';
import { ValidationRun } from '../../types';

interface ValidationRunnerProps {
  planId?: string;
  projectId?: string;
  scanId?: string;
}

export const ValidationRunner: React.FC<ValidationRunnerProps> = ({ planId, projectId, scanId }) => {
  const [validationRun, setValidationRun] = useState<ValidationRun | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleRunValidation = async () => {
    setLoading(true);
    setError(null);
    try {
      let res: ValidationRun;
      if (projectId) {
        res = await validationService.runBuildValidation(projectId, scanId);
      } else if (planId) {
        res = await validationService.runValidation(planId);
      } else {
        setError('No project or plan context available for validation.');
        return;
      }
      setValidationRun(res);
    } catch (err: any) {
      setError(err.message || 'Validation suite execution failed.');
    } finally {
      setLoading(false);
    }
  };

  const renderStatusBadge = (status?: string) => {
    const s = (status || '').toUpperCase();
    if (s === 'PASSED' || s === 'PASS' || s === 'SUCCESS') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-emerald-950/80 border border-emerald-700 text-emerald-300">
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>PASS</span>
        </span>
      );
    }
    if (s === 'FAILED' || s === 'FAIL') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-rose-950/80 border border-rose-700 text-rose-300">
          <XCircle className="w-3.5 h-3.5" />
          <span>FAIL</span>
        </span>
      );
    }
    if (s === 'TIMEOUT') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-amber-950/80 border border-amber-700 text-amber-300">
          <Clock className="w-3.5 h-3.5" />
          <span>TIMEOUT</span>
        </span>
      );
    }
    if (s === 'NOT_CONFIGURED') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-slate-900 border border-slate-700 text-slate-300">
          <HelpCircle className="w-3.5 h-3.5" />
          <span>NOT CONFIGURED</span>
        </span>
      );
    }
    if (s === 'NOT_SUPPORTED') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-slate-900 border border-slate-700 text-slate-400">
          <HelpCircle className="w-3.5 h-3.5" />
          <span>NOT SUPPORTED</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-rose-950/80 border border-rose-800 text-rose-300">
        <AlertTriangle className="w-3.5 h-3.5" />
        <span>{s || 'ERROR'}</span>
      </span>
    );
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-xl space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-emerald-400 font-mono text-xs uppercase tracking-wider font-semibold mb-1">
            <ShieldCheck className="w-4 h-4" />
            <span>Actual Build Execution Pipeline</span>
          </div>
          <h3 className="text-base font-bold text-slate-100">Deterministic Build Validation Engine</h3>
          <p className="text-xs text-slate-400">
            Discovers repository build system, executes allowlisted commands, and collects real process telemetry.
          </p>
        </div>

        <button
          onClick={handleRunValidation}
          disabled={loading}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-slate-950 font-bold text-xs shadow-md shadow-emerald-950/50 cursor-pointer transition-all shrink-0 font-mono"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Executing Build Pipeline...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-current" />
              <span>Run Build Validation</span>
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-rose-950/50 border border-rose-800/60 text-xs text-rose-300 font-mono flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {validationRun ? (
        <div className="space-y-4">
          {/* Header Telemetry Row */}
          <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-xl bg-slate-900/60 border border-slate-800 font-mono text-xs">
            <div className="flex items-center gap-3">
              <span className="text-slate-400">Build Status:</span>
              {renderStatusBadge(validationRun.status)}
            </div>

            <div className="flex items-center gap-4 text-slate-300 text-[11px]">
              <div>
                <span className="text-slate-500">Framework: </span>
                <span className="text-cyan-300 font-bold">{validationRun.framework || 'Detected from repo'}</span>
              </div>
              <div>
                <span className="text-slate-500">Exit Code: </span>
                <span className={validationRun.exit_code === 0 ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                  {validationRun.exit_code !== undefined && validationRun.exit_code !== null ? validationRun.exit_code : 'N/A'}
                </span>
              </div>
              <div>
                <span className="text-slate-500">Duration: </span>
                <span className="text-slate-200">
                  {validationRun.duration_ms !== undefined && validationRun.duration_ms !== 0
                    ? `${validationRun.duration_ms} ms`
                    : `${validationRun.duration} s`}
                </span>
              </div>
            </div>
          </div>

          {/* Test Status Indicators */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center gap-2.5">
              {validationRun.build_passed ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              ) : (
                <XCircle className="w-4 h-4 text-rose-400 shrink-0" />
              )}
              <div className="text-xs font-mono">
                <div className="text-slate-400 text-[10px]">Build Result</div>
                <div className={validationRun.build_passed ? 'text-emerald-300 font-bold' : 'text-rose-300 font-bold'}>
                  {validationRun.build_passed ? 'PASSED' : validationRun.status}
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
                <div className="text-slate-400 text-[10px]">Syntax & Readiness</div>
                <div className={validationRun.unit_tests_passed ? 'text-emerald-300 font-bold' : 'text-rose-300 font-bold'}>
                  {validationRun.unit_tests_passed ? 'VERIFIED' : 'PENDING'}
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
                <div className="text-slate-400 text-[10px]">PQC Kat Markers</div>
                <div className={validationRun.crypto_tests_passed ? 'text-emerald-300 font-bold' : 'text-rose-300 font-bold'}>
                  {validationRun.crypto_tests_passed ? 'VERIFIED' : 'PENDING'}
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
                <span>Build Telemetry & Logs Stream</span>
              </div>
              <pre className="p-4 text-[11px] font-mono text-slate-300 whitespace-pre-wrap max-h-60 overflow-y-auto leading-relaxed selection:bg-cyan-900/50">
                {validationRun.logs}
              </pre>
            </div>
          )}
        </div>
      ) : (
        <div className="py-8 text-center text-xs text-slate-500 rounded-xl border border-dashed border-slate-800 bg-slate-950/40 font-mono">
          Click "Run Build Validation" to execute deterministic build system detection and process execution.
        </div>
      )}
    </div>
  );
};
