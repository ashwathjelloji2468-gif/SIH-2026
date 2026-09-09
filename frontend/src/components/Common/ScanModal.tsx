import React, { useState } from 'react';
import { X, Play, Loader2, FolderSearch, AlertCircle, CheckCircle2, GitBranch, Folder, Upload, Box } from 'lucide-react';
import { useProject } from '../../context/ProjectContext';
import { scanService } from '../../services/scanService';
import { useNavigate } from 'react-router-dom';

export type InputMode = 'git' | 'local' | 'binary' | 'container';

export const ScanModal: React.FC = () => {
  const { isScanModalOpen, setIsScanModalOpen, currentProject, refreshLatestScan } = useProject();
  const navigate = useNavigate();

  const defaultLocalPath = currentProject?.name.includes('cryptography')
    ? '/Users/jashwath/.gemini/antigravity/scratch/cloned_repos/cryptography/src/cryptography'
    : currentProject?.name.includes('paramiko')
    ? '/Users/jashwath/.gemini/antigravity/scratch/cloned_repos/paramiko/paramiko'
    : currentProject?.name.includes('demo-bank')
    ? '/Users/jashwath/.gemini/antigravity/scratch/SIH-2026/test_apps/demo-bank'
    : '/Users/jashwath/.gemini/antigravity/scratch/SIH-2026/test_apps/demo-bank';

  const [inputMode, setInputMode] = useState<InputMode>('local');
  const [gitUrl, setGitUrl] = useState<string>('https://github.com/pyca/cryptography.git');
  const [localPath, setLocalPath] = useState<string>(defaultLocalPath);
  const [containerImage, setContainerImage] = useState<string>('ubuntu:latest');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

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
      if (inputMode === 'binary') {
        if (!selectedFile) {
          throw new Error('Please select a binary file to upload.');
        }
        await scanService.uploadBinaryAndScan(currentProject.id, selectedFile);
      } else {
        let target = localPath;
        let sType = 'source';

        if (inputMode === 'git') {
          if (!gitUrl.trim()) throw new Error('Please enter a valid Git repository URL.');
          target = gitUrl.trim();
          sType = 'git';
        } else if (inputMode === 'container') {
          if (!containerImage.trim()) throw new Error('Please enter a container image name/tag.');
          target = containerImage.trim();
          sType = 'container';
        } else {
          if (!localPath.trim()) throw new Error('Please enter a local target path.');
          target = localPath.trim();
          sType = 'source';
        }

        await scanService.startScan(currentProject.id, {
          target_path: target,
          scan_type: sType,
        });
      }

      setSuccess(true);
      await refreshLatestScan();
      setTimeout(() => {
        setIsScanModalOpen(false);
        setSuccess(false);
        navigate('/inventory');
      }, 800);
    } catch (err: any) {
      setError(err.message || 'Failed to dispatch scan job.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
      <div className="relative w-full max-w-xl rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-2xl space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-cyan-950/70 border border-cyan-800/50 text-cyan-400">
              <FolderSearch className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-slate-100 font-mono">New Scan / Discover Cryptographic Assets</h2>
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
          <div className="flex items-center gap-2.5 p-3 rounded-lg bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="flex items-center gap-2.5 p-3 rounded-lg bg-emerald-950/40 border border-emerald-800/60 text-xs text-emerald-300">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>Scan job dispatched! Redirecting to Live Inventory...</span>
          </div>
        )}

        {/* Input Mode Tabs */}
        <div className="grid grid-cols-4 gap-2 p-1 rounded-xl bg-slate-900 border border-slate-800 text-xs font-mono">
          <button
            type="button"
            onClick={() => setInputMode('git')}
            className={`flex items-center justify-center gap-1.5 py-2 rounded-lg transition-all cursor-pointer ${
              inputMode === 'git' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 font-semibold' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <GitBranch className="w-3.5 h-3.5" />
            <span>Git URL</span>
          </button>

          <button
            type="button"
            onClick={() => setInputMode('local')}
            className={`flex items-center justify-center gap-1.5 py-2 rounded-lg transition-all cursor-pointer ${
              inputMode === 'local' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 font-semibold' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Folder className="w-3.5 h-3.5" />
            <span>Local Path</span>
          </button>

          <button
            type="button"
            onClick={() => setInputMode('binary')}
            className={`flex items-center justify-center gap-1.5 py-2 rounded-lg transition-all cursor-pointer ${
              inputMode === 'binary' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 font-semibold' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Binary Upload</span>
          </button>

          <button
            type="button"
            onClick={() => setInputMode('container')}
            className={`flex items-center justify-center gap-1.5 py-2 rounded-lg transition-all cursor-pointer ${
              inputMode === 'container' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 font-semibold' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Box className="w-3.5 h-3.5" />
            <span>Container</span>
          </button>
        </div>

        {/* Input Form */}
        <form onSubmit={handleStartScan} className="space-y-4">
          {/* Mode 1: Git URL */}
          {inputMode === 'git' && (
            <div className="space-y-1.5">
              <label className="block text-xs font-medium text-slate-300">
                Git Repository HTTPS / SSH URL
              </label>
              <input
                type="text"
                required
                value={gitUrl}
                onChange={(e) => setGitUrl(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900/90 border border-slate-800 text-slate-200 text-xs font-mono focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                placeholder="https://github.com/org/repository.git"
              />
              <p className="text-[11px] text-slate-500 font-mono">
                Engine will clone the repository shallowly and execute SourceScanner, DependencyScanner & AST analysis.
              </p>
            </div>
          )}

          {/* Mode 2: Local Path */}
          {inputMode === 'local' && (
            <div className="space-y-1.5">
              <label className="block text-xs font-medium text-slate-300">
                Local Source Directory / File Path
              </label>
              <input
                type="text"
                required
                value={localPath}
                onChange={(e) => setLocalPath(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900/90 border border-slate-800 text-slate-200 text-xs font-mono focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                placeholder="/absolute/path/to/source/repository"
              />
              <p className="text-[11px] text-slate-500 font-mono">
                PythonCryptoVisitor AST parser and deterministic regex engines will scan target directory or file.
              </p>
            </div>
          )}

          {/* Mode 3: Binary Upload */}
          {inputMode === 'binary' && (
            <div className="space-y-2">
              <label className="block text-xs font-medium text-slate-300">
                Upload Compiled Binary or X.509 Certificate File
              </label>
              <div className="p-6 border-2 border-dashed border-slate-800 hover:border-cyan-500/50 rounded-xl bg-slate-900/50 text-center transition-colors">
                <input
                  type="file"
                  id="binary-file-upload"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  className="hidden"
                />
                <label htmlFor="binary-file-upload" className="cursor-pointer space-y-2 block">
                  <Upload className="w-8 h-8 text-cyan-400 mx-auto" />
                  <div className="text-xs font-mono text-slate-200">
                    {selectedFile ? (
                      <span className="text-cyan-300 font-semibold">{selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)</span>
                    ) : (
                      <span>Click to select binary (.so, .dll, .exe, .bin, .crt, .pem)</span>
                    )}
                  </div>
                  <div className="text-[11px] text-slate-500">
                    BinaryScanner & CertificateScanner will analyze symbols, embedded keys, & cert parameters.
                  </div>
                </label>
              </div>
            </div>
          )}

          {/* Mode 4: Container Image */}
          {inputMode === 'container' && (
            <div className="space-y-1.5">
              <label className="block text-xs font-medium text-slate-300">
                Container Image Name / Tag
              </label>
              <input
                type="text"
                required
                value={containerImage}
                onChange={(e) => setContainerImage(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900/90 border border-slate-800 text-slate-200 text-xs font-mono focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                placeholder="ubuntu:latest or redis:alpine"
              />
              <p className="text-[11px] text-slate-500 font-mono">
                ContainerScanner will inspect image layers for embedded cryptographic primitives & SSL libraries.
              </p>
            </div>
          )}

          {/* Engine Info */}
          <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl text-xs text-slate-400 flex items-center justify-between font-mono">
            <span>Engine Rule Set: <strong className="text-cyan-300">NIST PQC 2026.1.0</strong></span>
            <span>Detectors: <strong className="text-slate-200">7 Active Real Scanners</strong></span>
          </div>

          {/* Buttons */}
          <div className="pt-3 flex items-center justify-end gap-3 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setIsScanModalOpen(false)}
              className="px-4 py-2 rounded-xl border border-slate-800 text-slate-300 text-xs hover:bg-slate-900 transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || success}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-slate-950 font-semibold text-xs tracking-wide transition-all shadow-lg shadow-cyan-950/40 cursor-pointer"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Scanning Target...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  <span>Run Discovery Scan</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
