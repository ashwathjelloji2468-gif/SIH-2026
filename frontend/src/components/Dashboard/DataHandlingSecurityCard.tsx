import React, { useState } from 'react';
import { ShieldCheck, CheckCircle2, ChevronDown, ChevronUp, Lock, FileCode, Terminal } from 'lucide-react';

interface SecurityClaim {
  id: string;
  title: string;
  description: string;
  sourceFile: string;
  evidence: string;
}

const VERIFIED_SECURITY_CLAIMS: SecurityClaim[] = [
  {
    id: 'sandbox',
    title: 'Isolated Sandbox Execution',
    description: 'AST code transformations execute strictly inside temporary, network-isolated sandbox environments.',
    sourceFile: 'backend/app/migration/sandbox.py',
    evidence: 'tempfile.TemporaryDirectory(prefix="sentriq_sim_...") with network_access=False',
  },
  {
    id: 'source-protection',
    title: 'Original Source Code Protected',
    description: 'Production source code files are copied to the sandbox; original repository files remain 100% untouched.',
    sourceFile: 'backend/app/migration/sandbox.py',
    evidence: 'shutil.copytree() copies tree to temp directory; zero write operations to source_path',
  },
  {
    id: 'allowlist',
    title: 'Allowlisted Validation Commands',
    description: 'Automated test harness executes pre-approved test runners without shell interpretation.',
    sourceFile: 'backend/app/validation/validator.py',
    evidence: 'ALLOWLISTED_COMMANDS = ["pytest", "python -m unittest", "npm test", "go test", "cargo test"]',
  },
  {
    id: 'shell-false',
    title: 'shell=False Process Spawning',
    description: 'Validation subprocesses execute as direct binary parameter vectors preventing command injection.',
    sourceFile: 'backend/app/validation/validator.py',
    evidence: 'subprocess.run(cmd_args, shell=False, timeout=30, capture_output=True)',
  },
  {
    id: 'path-traversal',
    title: 'Path Traversal Protection',
    description: 'Real-path boundary validation prevents directory traversal attempts outside sandbox boundaries.',
    sourceFile: 'backend/app/migration/sandbox.py',
    evidence: 'validate_path_within_sandbox() checks real_target.startswith(real_root)',
  },
  {
    id: 'resource-timeout',
    title: 'Execution Timeout & Resource Constraints',
    description: 'Enforced execution timeouts and memory/CPU bounds prevent runaway processes and starvation.',
    sourceFile: 'backend/app/migration/sandbox.py',
    evidence: 'SandboxConfig(timeout_seconds=60, cpu_limit_percent=50, memory_limit_mb=512)',
  },
  {
    id: 'cleanup',
    title: 'Ephemeral Workspace Cleanup',
    description: 'Temporary sandbox directories are automatically purged upon simulation completion.',
    sourceFile: 'backend/app/migration/sandbox.py',
    evidence: 'sandbox.cleanup() invokes self._temp_dir_obj.cleanup() in finally blocks',
  },
];

export const DataHandlingSecurityCard: React.FC = () => {
  const [showAudit, setShowAudit] = useState<boolean>(false);

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0B0F19] p-6 shadow-xl space-y-4">
      {/* Card Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <h3 className="text-sm font-semibold text-slate-100">Data Handling & Security</h3>
        </div>
        <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800/60 px-2 py-0.5 rounded-full font-medium">
          Verified Controls
        </span>
      </div>

      {/* Security Claims Grid */}
      <div className="space-y-2.5">
        {VERIFIED_SECURITY_CLAIMS.slice(0, 5).map((claim) => (
          <div
            key={claim.id}
            className="flex items-start gap-2.5 p-2 rounded-lg bg-slate-900/40 border border-slate-800/50"
          >
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <div className="space-y-0.5 min-w-0">
              <div className="text-xs font-mono font-semibold text-slate-200 truncate">
                {claim.title}
              </div>
              <div className="text-[11px] text-slate-400 leading-snug">
                {claim.description}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Accordion Audit Evidence Drawer Toggle */}
      <div className="pt-2 border-t border-slate-800/80">
        <button
          type="button"
          onClick={() => setShowAudit(!showAudit)}
          aria-expanded={showAudit}
          aria-label="Toggle security control evidence audit"
          className="w-full flex items-center justify-between text-xs font-mono text-cyan-400 hover:text-cyan-300 py-1 transition-colors cursor-pointer focus:outline-none focus:ring-1 focus:ring-cyan-500/50 rounded"
        >
          <span className="flex items-center gap-1.5">
            <Lock className="w-3.5 h-3.5 text-cyan-400" />
            <span>Code Enforcement Audit ({VERIFIED_SECURITY_CLAIMS.length} Claims)</span>
          </span>
          {showAudit ? (
            <ChevronUp className="w-4 h-4 text-cyan-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-cyan-400" />
          )}
        </button>

        {showAudit && (
          <div className="mt-3 p-3 rounded-lg bg-[#06080F] border border-slate-800 space-y-2 text-[11px] font-mono animate-in fade-in duration-200">
            <div className="text-slate-400 font-semibold uppercase tracking-wider text-[10px] pb-1 border-b border-slate-800">
              Implementation File Evidence
            </div>
            {VERIFIED_SECURITY_CLAIMS.map((c) => (
              <div key={c.id} className="space-y-0.5 pt-1">
                <div className="flex items-center justify-between text-slate-300">
                  <span className="text-cyan-300 font-semibold">{c.title}</span>
                  <span className="text-slate-500 text-[10px]">{c.sourceFile}</span>
                </div>
                <div className="text-slate-400 text-[10px] bg-slate-900/60 p-1.5 rounded border border-slate-800/60 break-all">
                  <code>{c.evidence}</code>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Minimal Persistence Notice */}
      <div className="text-[11px] text-slate-400 leading-tight pt-1 flex items-center justify-between">
        <span>Source is processed in memory & temp sandboxes with minimal telemetry storage.</span>
      </div>
    </div>
  );
};
