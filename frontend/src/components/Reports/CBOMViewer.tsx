import React, { useState } from 'react';
import { Download, CheckCircle2, AlertTriangle, FileCode, Copy, Check, Loader2 } from 'lucide-react';
import { CBOMCycloneDX } from '../../types';
import { reportService } from '../../services/reportService';

interface CBOMViewerProps {
  scanId: string;
  cbom: CBOMCycloneDX | null;
}

export const CBOMViewer: React.FC<CBOMViewerProps> = ({ scanId, cbom }) => {
  const [copied, setCopied] = useState(false);
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<{ valid: boolean; specVersion: string } | null>(null);

  const jsonString = cbom ? JSON.stringify(cbom, null, 2) : '';

  const handleCopy = () => {
    if (jsonString) {
      navigator.clipboard.writeText(jsonString);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleValidate = async () => {
    setValidating(true);
    try {
      const res = await reportService.validateCBOM(scanId);
      setValidationResult({ valid: res.valid, specVersion: res.specVersion });
    } catch (err) {
      setValidationResult({ valid: false, specVersion: '1.6' });
    } finally {
      setValidating(false);
    }
  };

  const handleDownload = () => {
    window.open(reportService.getDownloadCBOMUrl(scanId), '_blank');
  };

  if (!cbom) {
    return (
      <div className="p-8 text-center text-xs text-slate-500 rounded-xl border border-slate-800 bg-[#0B0F19]">
        No CycloneDX 1.6 CBOM found for the selected scan. Run a scan to generate a cryptographic bill of materials.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-800 bg-[#0B0F19] overflow-hidden shadow-2xl">
      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 bg-slate-900/80 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <FileCode className="w-5 h-5 text-cyan-400" />
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold font-mono text-slate-100">CycloneDX CBOM Specification</span>
              <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/60">
                v{cbom.specVersion || '1.6'}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-mono">
              Components: {cbom.components ? cbom.components.length : 0} cryptographic assets cataloged
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {validationResult && (
            <div
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-mono ${
                validationResult.valid
                  ? 'bg-emerald-950/60 border-emerald-800/80 text-emerald-300'
                  : 'bg-rose-950/60 border-rose-800/80 text-rose-300'
              }`}
            >
              {validationResult.valid ? (
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              ) : (
                <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
              )}
              <span>{validationResult.valid ? 'CycloneDX 1.6 Compliant' : 'Validation Error'}</span>
            </div>
          )}

          <button
            onClick={handleValidate}
            disabled={validating}
            className="px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 transition-colors cursor-pointer flex items-center gap-1.5"
          >
            {validating ? <Loader2 className="w-3.5 h-3.5 animate-spin text-cyan-400" /> : <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />}
            <span>Validate Spec</span>
          </button>

          <button
            onClick={handleCopy}
            className="px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 transition-colors cursor-pointer flex items-center gap-1.5"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>

          <button
            onClick={handleDownload}
            className="px-3.5 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs shadow-md shadow-cyan-950/50 transition-all cursor-pointer flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download CBOM JSON</span>
          </button>
        </div>
      </div>

      {/* JSON Viewer */}
      <div className="p-4 max-h-[500px] overflow-y-auto bg-[#0B0F19] text-xs font-mono text-cyan-200/90 leading-relaxed">
        <pre className="whitespace-pre-wrap">{jsonString}</pre>
      </div>
    </div>
  );
};
