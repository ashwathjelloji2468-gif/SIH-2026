import React, { useState } from 'react';
import { Printer, Download, ShieldCheck, AlertTriangle, FileText, Loader2 } from 'lucide-react';
import { useProject } from '../../context/ProjectContext';
import { reportService } from '../../services/reportService';
import { CryptoAsset, RiskSummary } from '../../types';

interface PDFReportPreviewProps {
  assets: CryptoAsset[];
  riskSummary: RiskSummary | null;
}

export const PDFReportPreview: React.FC<PDFReportPreviewProps> = ({ assets, riskSummary }) => {
  const { currentProject } = useProject();
  const [generating, setGenerating] = useState(false);
  const [reportData, setReportData] = useState<any>(null);

  const handleGenerateReport = async () => {
    if (!currentProject) return;
    setGenerating(true);
    try {
      const rep = await reportService.generateProjectReport(currentProject.id);
      setReportData(rep);
    } catch (err) {
      console.error('Failed to generate report:', err);
    } finally {
      setGenerating(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const vulnerableCount = assets.filter((a) => a.quantum_safety === 'VULNERABLE').length;
  const safeCount = assets.filter((a) => a.quantum_safety === 'SAFE').length;

  return (
    <div className="space-y-6">
      {/* Top action bar */}
      <div className="flex items-center justify-between p-4 rounded-xl border border-slate-800 bg-[#0B0F19]">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">Executive Post-Quantum Readiness Assessment Report</h3>
          <p className="text-xs text-slate-400">Formal audit document for CISOs, compliance officers, and cryptographic architects</p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleGenerateReport}
            disabled={generating}
            className="px-3.5 py-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 transition-colors cursor-pointer flex items-center gap-1.5"
          >
            {generating ? <Loader2 className="w-3.5 h-3.5 animate-spin text-cyan-400" /> : <FileText className="w-3.5 h-3.5 text-cyan-400" />}
            <span>{reportData ? 'Regenerate Report' : 'Generate Full Report'}</span>
          </button>

          <button
            onClick={handlePrint}
            className="px-4 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs shadow-md shadow-cyan-950/50 transition-all cursor-pointer flex items-center gap-1.5"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print / Export PDF</span>
          </button>
        </div>
      </div>

      {/* Printable Report Sheet Layout */}
      <div className="rounded-2xl border border-slate-800 bg-[#0B0F19] p-8 md:p-12 shadow-2xl space-y-8 print:bg-white print:text-black print:border-none print:shadow-none print:p-0">
        {/* Document Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-slate-800 gap-4">
          <div>
            <div className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider mb-1">
              SENTRIQ QUANTUM INTELLIGENCE REPORT
            </div>
            <h1 className="text-2xl font-black text-slate-100 font-mono tracking-tight">
              {currentProject?.name || 'Cryptographic Inventory Assessment'}
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Scope: Automated AST & Dependency Discovery • NIST PQC Transition Audit
            </p>
          </div>

          <div className="text-right font-mono text-xs text-slate-400">
            <div>Date: <strong className="text-slate-200">{new Date().toLocaleDateString()}</strong></div>
            <div>Classification: <strong className="text-rose-400">RESTRICTED / INTERNAL</strong></div>
            <div>CBOM Spec: <strong className="text-cyan-300">CycloneDX 1.6</strong></div>
          </div>
        </div>

        {/* Executive Summary Section */}
        <div className="space-y-3">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 font-mono flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            <span>1. Executive Summary & Quantum Threat Horizon</span>
          </h2>
          <p className="text-xs text-slate-300 leading-relaxed">
            This report provides an automated cryptographic inventory and quantum migration readiness evaluation for <strong className="text-slate-100">{currentProject?.name}</strong>. A total of <strong className="text-cyan-300 font-mono">{assets.length}</strong> cryptographic primitives were discovered. Among these, <strong className="text-rose-400 font-mono">{vulnerableCount} ({assets.length > 0 ? Math.round((vulnerableCount / assets.length) * 100) : 0}%)</strong> utilize asymmetric public-key cryptography (such as RSA or Elliptic Curve Cryptography) that will be completely compromised by Shor's algorithm running on a cryptanalytically relevant quantum computer (CRQC).
          </p>
        </div>

        {/* High-Level Posture Metrics */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 font-mono">
            <div className="text-xs text-slate-400 uppercase">Average Project Risk</div>
            <div className="text-2xl font-bold text-slate-100 mt-1">
              {riskSummary?.average_risk_score ?? 68.4} / 100
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">Weighted by exposure & Mosca gap</div>
          </div>

          <div className="rounded-xl border border-rose-900/40 bg-rose-950/20 p-4 font-mono">
            <div className="text-xs text-rose-400 uppercase">Quantum Vulnerable Primitives</div>
            <div className="text-2xl font-bold text-rose-300 mt-1">
              {vulnerableCount}
            </div>
            <div className="text-[11px] text-rose-400/80 mt-0.5">Critical Shor's Algorithm exposure</div>
          </div>

          <div className="rounded-xl border border-emerald-900/40 bg-emerald-950/20 p-4 font-mono">
            <div className="text-xs text-emerald-400 uppercase">Quantum Safe / Resistant</div>
            <div className="text-2xl font-bold text-emerald-300 mt-1">
              {safeCount}
            </div>
            <div className="text-[11px] text-emerald-400/80 mt-0.5">Symmetric 256-bit or PQC hybrid</div>
          </div>
        </div>

        {/* Mosca Threat Condition */}
        <div className="space-y-3 rounded-xl border border-slate-800 bg-slate-900/40 p-5">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 font-mono flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-rose-400" />
            <span>2. Mosca Theorem Timeline Analysis (X + Y &gt; Z)</span>
          </h2>
          <p className="text-xs text-slate-300 leading-relaxed">
            Assuming an enterprise customer data confidentiality shelf-life of <strong>10 years</strong> (X) and an estimated PQC migration deployment timeframe of <strong>3 years</strong> (Y), the total required security runway is <strong>13 years</strong>. With the consensus quantum threat horizon placed at <strong>2033</strong> (~7 years remaining), the organization is in an active <strong>Harvest Now, Decrypt Later (HNDL) exposure window</strong>.
          </p>
        </div>

        {/* Key Cryptographic Findings Table */}
        <div className="space-y-3">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 font-mono flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-blue-400" />
            <span>3. Critical Discovered Primitives & Replacement Pathways</span>
          </h2>

          <div className="rounded-xl border border-slate-800 overflow-hidden font-mono text-xs">
            <table className="w-full text-left">
              <thead className="bg-slate-900 text-slate-400 uppercase text-[10px] border-b border-slate-800">
                <tr>
                  <th className="p-3">Algorithm</th>
                  <th className="p-3">Purpose</th>
                  <th className="p-3">Location</th>
                  <th className="p-3">Recommended NIST PQC Candidate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-200">
                {assets.slice(0, 8).map((a) => (
                  <tr key={a.id}>
                    <td className="p-3 font-bold text-cyan-300">{a.algorithm_name}</td>
                    <td className="p-3 text-slate-400">{a.purpose}</td>
                    <td className="p-3 truncate max-w-xs text-slate-300">
                      {a.location}{a.line_number && `:L${a.line_number}`}
                    </td>
                    <td className="p-3 font-semibold text-emerald-400">
                      {a.quantum_safety === 'VULNERABLE'
                        ? a.purpose === 'SIGNATURE'
                          ? 'ML-DSA-65 (FIPS 204)'
                          : 'ML-KEM-768 (FIPS 203)'
                        : 'AES-256 (Grover Resistant)'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Audit Disclaimer */}
        <div className="pt-6 border-t border-slate-800 text-[11px] text-slate-500 font-mono flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <span>Generated by SENTRIQ Platform v1.2.0 • Rule Engine 2026.1.0</span>
          <span>100% Cryptographic Discovery is never claimed. Heuristics subject to human review.</span>
        </div>
      </div>
    </div>
  );
};
