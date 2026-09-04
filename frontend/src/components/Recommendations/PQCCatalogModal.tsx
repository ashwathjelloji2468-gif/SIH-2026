import React, { useState, useEffect } from 'react';
import { X, BookOpen, ShieldCheck, Loader2 } from 'lucide-react';
import { recommendationService } from '../../services/recommendationService';

interface PQCCatalogModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const PQCCatalogModal: React.FC<PQCCatalogModalProps> = ({ isOpen, onClose }) => {
  const [catalog, setCatalog] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    if (!isOpen) return;
    const fetchCatalog = async () => {
      try {
        const data = await recommendationService.getPqcCatalog();
        setCatalog(data);
      } catch (err) {
        console.error('Failed to load PQC catalog:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchCatalog();
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
      <div className="w-full max-w-3xl rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-2xl max-h-[85vh] flex flex-col">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-cyan-950/70 border border-cyan-800/50 text-cyan-400">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-slate-100">NIST PQC Standards Reference Catalog</h2>
              <p className="text-xs text-slate-400">Official FIPS 203, FIPS 204, and FIPS 205 Standardized Algorithms</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200 p-1 cursor-pointer">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-4 my-4">
          {loading ? (
            <div className="flex items-center justify-center py-12 text-xs text-slate-400">
              <Loader2 className="w-5 h-5 animate-spin text-cyan-400 mr-2" />
              <span>Loading NIST PQC standards catalog...</span>
            </div>
          ) : (
            Object.entries(catalog).map(([name, item]) => (
              <div
                key={name}
                className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span className="text-base font-bold font-mono text-cyan-300">{name}</span>
                    <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800/60 text-cyan-400">
                      {item.standard_code}
                    </span>
                  </div>
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/60 font-semibold uppercase">
                    {item.status?.replace('_', ' ') || 'FINAL STANDARD'}
                  </span>
                </div>

                <div className="text-xs text-slate-300 font-medium">{item.full_name}</div>

                <div className="text-xs text-slate-400 space-y-1 font-mono bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
                  <div>
                    <span className="text-slate-500">Variants: </span>
                    <span className="text-slate-200 font-semibold">
                      {Array.isArray(item.variants) ? item.variants.join(', ') : item.variants}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500">Key & Signature Footprint: </span>
                    <span className="text-slate-300">{item.key_size_notes}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Performance Characteristics: </span>
                    <span className="text-slate-300">{item.performance_notes}</span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="pt-3 border-t border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
