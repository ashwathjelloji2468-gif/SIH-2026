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
  const [validationRun, setValidationRun] = useState<any | null>(null);
  const [loadingBuild, setLoadingBuild] = useState<boolean>(false);
  const [loadingTest, setLoadingTest] = useState<boolean>(false);
  const [loadingRegression, setLoadingRegression] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleRunBuildValidation = async () => {
    setLoadingBuild(true);
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
      setError(err.message || 'Build validation pipeline execution failed.');
    } finally {
      setLoadingBuild(false);
    }
  };

  const handleRunTestValidation = async () => {
    if (!projectId) {
      setError('Project context required for test validation.');
      return;
    }
    setLoadingTest(true);
    setError(null);
    try {
      const res = await validationService.runTestValidation(projectId, scanId);
      setValidationRun(res);
    } catch (err: any) {
      setError(err.message || 'Unit-test validation execution failed.');
    } finally {
      setLoadingTest(false);
    }
  };

  const handleRunRegressionValidation = async () => {
    if (!projectId) {
      setError('Project context required for regression validation.');
      return;
    }
    setLoadingRegression(true);
    setError(null);
    try {
      const res = await validationService.runRegressionValidation(projectId, { scanId, planId });
      setValidationRun(res);
    } catch (err: any) {
      setError(err.message || 'Regression validation pipeline failed.');
    } finally {
      setLoadingRegression(false);
    }
  };

  const renderStatusBadge = (status?: string) => {
    const s = (status || '').toUpperCase();
    if (s === 'PASSED' || s === 'PASS' || s === 'SUCCESS' || s === 'NO_REGRESSION') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-emerald-950/80 border border-emerald-700 text-emerald-300">
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>{s === 'NO_REGRESSION' ? 'NO REGRESSION' : 'PASS'}</span>
        </span>
      );
    }
    if (s === 'REGRESSION') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-rose-950/80 border border-rose-700 text-rose-300">
          <AlertTriangle className="w-3.5 h-3.5" />
          <span>REGRESSION</span>
        </span>
      );
    }
    if (s === 'IMPROVED') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-cyan-950/80 border border-cyan-700 text-cyan-300">
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>IMPROVED</span>
        </span>
      );
    }
    if (s === 'BASELINE_FAILED') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-amber-950/80 border border-amber-700 text-amber-300">
          <AlertTriangle className="w-3.5 h-3.5" />
          <span>BASELINE FAILED</span>
        </span>
      );
    }
    if (s === 'MIGRATION_FAILED') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-rose-950/80 border border-rose-800 text-rose-300">
          <XCircle className="w-3.5 h-3.5" />
          <span>MIGRATION FAILED</span>
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
            <span>Deterministic Sandbox Execution Engine</span>
          </div>
          <h3 className="text-base font-bold text-slate-100">Build, Test & Before/After Regression Pipeline</h3>
          <p className="text-xs text-slate-400">
            Discovers repository build/test systems, executes process commands, and performs deterministic regression validation.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={handleRunBuildValidation}
            disabled={loadingBuild || loadingTest || loadingRegression}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-slate-950 font-bold text-xs shadow-md shadow-emerald-950/50 cursor-pointer transition-all shrink-0 font-mono"
          >
            {loadingBuild ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Build...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Run Build</span>
              </>
            )}
          </button>

          {projectId && (
            <button
              onClick={handleRunTestValidation}
              disabled={loadingBuild || loadingTest || loadingRegression}
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-slate-950 font-bold text-xs shadow-md shadow-cyan-950/50 cursor-pointer transition-all shrink-0 font-mono"
            >
              {loadingTest ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Tests...</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Run Tests</span>
                </>
              )}
            </button>
          )}

          {projectId && (
            <button
              onClick={handleRunRegressionValidation}
              disabled={loadingBuild || loadingTest || loadingRegression}
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-purple-500 hover:bg-purple-400 disabled:opacity-50 text-slate-950 font-bold text-xs shadow-md shadow-purple-950/50 cursor-pointer transition-all shrink-0 font-mono"
            >
              {loadingRegression ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Regression Pipeline...</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Run Regression</span>
                </>
              )}
            </button>
          )}
        </div>
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
              <span className="text-slate-400">{validationRun.check_type || 'Execution'} Status:</span>
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

          {/* Test Metrics Breakdown (if available) */}
          {(validationRun.tests_total !== undefined && validationRun.tests_total !== null) && (
            <div className="grid grid-cols-4 gap-3 p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 font-mono text-center">
              <div>
                <div className="text-[10px] text-slate-400 uppercase">Total Tests</div>
                <div className="text-base font-bold text-slate-100">{validationRun.tests_total}</div>
              </div>
              <div>
                <div className="text-[10px] text-slate-400 uppercase">Passed</div>
                <div className="text-base font-bold text-emerald-400">{validationRun.tests_passed ?? 0}</div>
              </div>
              <div>
                <div className="text-[10px] text-slate-400 uppercase">Failed</div>
                <div className="text-base font-bold text-rose-400">{validationRun.tests_failed ?? 0}</div>
              </div>
              <div>
                <div className="text-[10px] text-slate-400 uppercase">Skipped</div>
                <div className="text-base font-bold text-amber-400">{validationRun.tests_skipped ?? 0}</div>
              </div>
            </div>
          )}

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
                <div className="text-slate-400 text-[10px]">Unit Test Execution</div>
                <div className={validationRun.unit_tests_passed ? 'text-emerald-300 font-bold' : 'text-rose-300 font-bold'}>
                  {validationRun.unit_tests_passed ? 'PASSED' : validationRun.status}
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

          {/* Regression Reasons List */}
          {validationRun.reasons && validationRun.reasons.length > 0 && (
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
              <div className="text-xs font-bold text-slate-200 font-mono uppercase tracking-wider flex items-center justify-between">
                <span>Regression Analysis Reasons</span>
                <span className={validationRun.regression_detected ? 'text-rose-400 font-bold' : 'text-emerald-400 font-bold'}>
                  {validationRun.regression_detected ? 'REGRESSION DETECTED' : 'NO REGRESSION DETECTED'}
                </span>
              </div>
              <ul className="space-y-1.5 text-xs font-mono text-slate-300">
                {validationRun.reasons.map((r: string, idx: number) => (
                  <li key={idx} className="flex items-start gap-2 bg-slate-950/40 p-2 rounded-lg border border-slate-800/80">
                    <span className={validationRun.regression_detected ? 'text-rose-400 font-bold' : 'text-cyan-400 font-bold'}>•</span>
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Before vs After Side-by-Side Comparison */}
          {(validationRun.before && validationRun.after) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* BEFORE Card */}
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3 font-mono text-xs">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <span className="text-slate-400 font-bold uppercase tracking-wider">BEFORE MIGRATION (Baseline)</span>
                  <span className="text-slate-500 text-[10px]">Untouched Source</span>
                </div>
                <div className="space-y-2 text-slate-300 text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Build Status:</span>
                    <span>{renderStatusBadge(validationRun.before.build?.status)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Test Status:</span>
                    <span>{renderStatusBadge(validationRun.before.tests?.status)}</span>
                  </div>
                  {validationRun.before.tests?.tests_total !== undefined && validationRun.before.tests?.tests_total !== null && (
                    <div className="flex justify-between text-slate-400">
                      <span>Tests Passed:</span>
                      <span className="text-emerald-400 font-bold">{validationRun.before.tests.tests_passed} / {validationRun.before.tests.tests_total}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* AFTER Card */}
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3 font-mono text-xs">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <span className="text-slate-400 font-bold uppercase tracking-wider">AFTER MIGRATION (Sandbox)</span>
                  <span className="text-slate-500 text-[10px]">Migrated Sandbox Copy</span>
                </div>
                <div className="space-y-2 text-slate-300 text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Build Status:</span>
                    <span>{renderStatusBadge(validationRun.after.build?.status)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Test Status:</span>
                    <span>{renderStatusBadge(validationRun.after.tests?.status)}</span>
                  </div>
                  {validationRun.after.tests?.tests_total !== undefined && validationRun.after.tests?.tests_total !== null && (
                    <div className="flex justify-between text-slate-400">
                      <span>Tests Passed:</span>
                      <span className="text-emerald-400 font-bold">{validationRun.after.tests.tests_passed} / {validationRun.after.tests.tests_total}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Validation Logs Console */}
          {validationRun.logs && (
            <div className="rounded-xl border border-slate-800 bg-[#0B0F19] overflow-hidden">
              <div className="flex items-center gap-2 px-3.5 py-2 bg-slate-900/80 border-b border-slate-800 text-xs text-slate-400 font-mono">
                <Terminal className="w-3.5 h-3.5 text-cyan-400" />
                <span>Process Telemetry & Real Logs Stream</span>
              </div>
              <pre className="p-4 text-[11px] font-mono text-slate-300 whitespace-pre-wrap max-h-60 overflow-y-auto leading-relaxed selection:bg-cyan-900/50">
                {validationRun.logs}
              </pre>
            </div>
          )}
        </div>
      ) : (
        <div className="py-8 text-center text-xs text-slate-500 rounded-xl border border-dashed border-slate-800 bg-slate-950/40 font-mono">
          Click "Run Build Validation" or "Run Test Validation" to execute deterministic process execution.
        </div>
      )}
    </div>
  );
};
