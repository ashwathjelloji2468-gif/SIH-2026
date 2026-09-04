import React, { useState } from 'react';
import { X, CheckCircle2, AlertTriangle, Loader2 } from 'lucide-react';
import { CryptoAsset, CryptoPurpose } from '../../types';
import { inventoryService } from '../../services/inventoryService';

interface UnknownReviewModalProps {
  asset: CryptoAsset | null;
  onClose: () => void;
  onReviewed: () => void;
}

export const UnknownReviewModal: React.FC<UnknownReviewModalProps> = ({
  asset,
  onClose,
  onReviewed,
}) => {
  const [algorithmName, setAlgorithmName] = useState<string>(asset?.algorithm_name === 'UNKNOWN_ALGORITHM' ? 'AES' : (asset?.algorithm_name || ''));
  const [purpose, setPurpose] = useState<CryptoPurpose>(asset?.purpose || 'ENCRYPTION');
  const [action, setAction] = useState<'RESOLVE' | 'REJECT'>('RESOLVE');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!asset) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await inventoryService.reviewUnknownAsset(asset.id, {
        algorithm_name: action === 'RESOLVE' ? algorithmName : undefined,
        purpose: action === 'RESOLVE' ? purpose : undefined,
        action,
      });
      onReviewed();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to submit review.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-2xl">
        <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-amber-950/70 border border-amber-800/50 text-amber-400">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-100">Review Unclassified Cryptography</h3>
              <p className="text-xs text-slate-400">Human-in-the-Loop Cryptographic Verification</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200 p-1 cursor-pointer">
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-rose-950/50 border border-rose-800/60 text-xs text-rose-300">
            {error}
          </div>
        )}

        <div className="mb-4 rounded-xl border border-slate-800 bg-slate-950/60 p-3.5 space-y-2 text-xs font-mono">
          <div className="text-slate-400">File: <span className="text-slate-200">{asset.location}</span></div>
          <div className="text-slate-400">Line: <span className="text-cyan-300">{asset.line_number || 'N/A'}</span></div>
          <div className="text-slate-400">Flagged Reason: <span className="text-amber-300">{asset.unknown_reason || 'Pattern matched generic crypto interface or unclassified wrapper'}</span></div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Review Action</label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setAction('RESOLVE')}
                className={`px-3 py-2 rounded-lg border text-xs font-medium cursor-pointer transition-colors ${
                  action === 'RESOLVE'
                    ? 'bg-cyan-950/60 border-cyan-500 text-cyan-300'
                    : 'bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-800'
                }`}
              >
                Resolve to Known Primitive
              </button>
              <button
                type="button"
                onClick={() => setAction('REJECT')}
                className={`px-3 py-2 rounded-lg border text-xs font-medium cursor-pointer transition-colors ${
                  action === 'REJECT'
                    ? 'bg-rose-950/60 border-rose-500 text-rose-300'
                    : 'bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-800'
                }`}
              >
                Reject / False Positive
              </button>
            </div>
          </div>

          {action === 'RESOLVE' && (
            <>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Identified Algorithm</label>
                <input
                  type="text"
                  required
                  value={algorithmName}
                  onChange={(e) => setAlgorithmName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-xs font-mono focus:outline-none focus:border-cyan-500"
                  placeholder="e.g. AES, RSA, ECDSA, SHA-256"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Primary Purpose</label>
                <select
                  value={purpose}
                  onChange={(e) => setPurpose(e.target.value as CryptoPurpose)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-cyan-500"
                >
                  <option value="ENCRYPTION">ENCRYPTION (Data at rest / in transit)</option>
                  <option value="SIGNATURE">SIGNATURE (Digital signatures / integrity)</option>
                  <option value="KEY_ESTABLISHMENT">KEY ESTABLISHMENT (Key exchange / KEM)</option>
                  <option value="HASHING">HASHING (Digest / HMAC)</option>
                  <option value="AUTHENTICATION">AUTHENTICATION (Session / tokens)</option>
                </select>
              </div>
            </>
          )}

          <div className="pt-3 flex items-center justify-end gap-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg border border-slate-800 text-slate-300 text-xs hover:bg-slate-900 cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-xs tracking-wide shadow-md shadow-cyan-950/50 cursor-pointer"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Confirm Classification</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
