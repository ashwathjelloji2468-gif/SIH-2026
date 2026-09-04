import React, { useState } from 'react';
import { X, Play, Loader2, FolderSearch, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useProject } from '../../context/ProjectContext';
import { scanService } from '../../services/scanService';
import { useNavigate } from 'react-router-dom';

export const ScanModal: React.FC = () => {
  const { isScanModalOpen, setIsScanModalOpen, currentProject, refreshLatestScan } = useProject();
  const navigate = useNavigate();

  // Suggest reasonable target path based on current project
  const defaultPath = currentProject?.name.includes('cryptography')
    ? '/Users/jashwath/.gemini/antigravity/scratch/cloned_repos/cryptography/src/cryptography'
    : currentProject?.name.includes('paramiko')
    ? '/Users/jashwath/.gemini/antigravity/scratch/cloned_repos/paramiko/paramiko'
    : currentProject?.name.includes('demo-bank')
    ? '/Users/jashwath/.gemini/antigravity/scratch/SIH-2026/test_apps/demo-bank'
    : '/Users/jashwath/.gemini/antigravity/scratch/cloned_repos/cryptography/src/cryptography';

  const [targetPath, setTargetPath] = useState<string>(defaultPath);
  const [scanType, setScanType] = useState<string>('source');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean>(false);

  if (!isScanModalOpen) return null;

  const handleStartScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentProject) return;

    setLoading(true);
    setError(null);

    try {
      await scanService.startScan(currentProject.id, {
        target_path: targetPath,
        scan_type: scanType,
      });
      setSuccess(true);
      await refreshLatestScan();
      setTimeout(() => {
        setIsScanModalOpen(false);
        setSuccess(false);
        navigate('/scan');
      }, 800);
    } catch (err: any) {
      setError(err.message || 'Failed to dispatch scan job.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
      <div className="relative w-full max-w-lg rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-2xl">
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-cyan-950/70 border border-cyan-800/50 text-cyan-400">
              <FolderSearch className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-slate-100">Dispatch Cryptographic Scan</h2>
              <p className="text-xs text-slate-400">Target Project: <span className="text-cyan-300 font-mono">{currentProject?.name || 'None'}</span></p>
            </div>
          </div>
          <button
            onClick={() => setIsScanModalOpen(false)}
            className="text-slate-400 hover:text-slate-200 p-1 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="mb-4 flex items-center gap-2.5 p-3 rounded-lg bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="mb-4 flex items-center gap-2.5 p-3 rounded-lg bg-emerald-950/40 border border-emerald-800/60 text-xs text-emerald-300">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>Scan job dispatched! Redirecting to scan console...</span>
          </div>
        )}

        <form onSubmit={handleStartScan} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Source Code Target Directory Path
            </label>
            <input
              type="text"
              required
              value={targetPath}
              onChange={(e) => setTargetPath(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-900/90 border border-slate-800 text-slate-200 text-xs font-mono focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
              placeholder="/absolute/path/to/source/repo"
            />
            <p className="mt-1 text-[11px] text-slate-500 font-mono">
              AST & regex detectors will recursively inspect cryptographic primitives.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Scan Type
              </label>
              <select
                value={scanType}
                onChange={(e) => setScanType(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-cyan-500"
              >
                <option value="source">Full Source Code (AST + Regex)</option>
                <option value="dependency">Dependencies & Manifests</option>
                <option value="binary">Binary / Certificate Assets</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Rule Engine
              </label>
              <input
                type="text"
                disabled
                value="NIST-PQC 2026.1.0"
                className="w-full px-3 py-2 rounded-lg bg-slate-900/50 border border-slate-800 text-slate-400 text-xs font-mono select-none"
              />
            </div>
          </div>

          <div className="pt-3 flex items-center justify-end gap-3 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setIsScanModalOpen(false)}
              className="px-4 py-2 rounded-lg border border-slate-800 text-slate-300 text-xs hover:bg-slate-900 transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || success}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-slate-950 font-semibold text-xs tracking-wide transition-all shadow-lg shadow-cyan-950/40 cursor-pointer"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Dispatching...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  <span>Run Scan</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
