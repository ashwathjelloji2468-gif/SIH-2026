import React from 'react';
import { GitFork, ArrowRight, ShieldCheck, ChevronRight, AlertCircle } from 'lucide-react';
import { CryptoAsset, Recommendation } from '../../types';

interface TopMigrationPrioritiesCardProps {
  assets: CryptoAsset[];
  recommendations: Map<string, Recommendation[]>;
  loading: boolean;
  onSelectAsset: (asset: CryptoAsset) => void;
}

const PQC_MAP: Record<string, string> = {
  'RSA': 'ML-DSA-65 (NIST FIPS 204)',
  'RSA-2048': 'ML-DSA-65 (NIST FIPS 204)',
  'RSA-4096': 'ML-DSA-87 (NIST FIPS 204)',
  'ECDSA': 'ML-DSA-65 (NIST FIPS 204)',
  'ECDSA-P256': 'ML-DSA-65 (NIST FIPS 204)',
  'ECDSA-P384': 'ML-DSA-87 (NIST FIPS 204)',
  'ECDH': 'ML-KEM-768 Hybrid (NIST FIPS 203)',
  'ECDH-P256': 'ML-KEM-768 Hybrid (NIST FIPS 203)',
  'X25519': 'ML-KEM-768 Hybrid (NIST FIPS 203)',
  'ED25519': 'ML-DSA-65 (NIST FIPS 204)',
  'DSA': 'ML-DSA-65 (NIST FIPS 204)',
  'DH': 'ML-KEM-768 Hybrid (NIST FIPS 203)',
  'AES-128': 'AES-256-GCM (Retain)',
  'AES-256': 'AES-256-GCM (Retain)',
  'AES': 'AES-256-GCM (Retain)',
  'SHA-256': 'SHA-256 (Retain)',
  'SHA-384': 'SHA-384 (Retain)',
  'SHA-512': 'SHA-512 (Retain)',
  'SHA': 'Retain',
  'HMAC': 'Retain',
};

function getPqcTarget(asset: CryptoAsset, recs: Recommendation[]): string {
  if (recs && recs.length > 0) return recs[0].target_pqc_candidate;
  const alg = asset.algorithm_name?.toUpperCase() || '';
  for (const [key, val] of Object.entries(PQC_MAP)) {
    if (alg.includes(key.toUpperCase())) return val;
  }
  return 'Manual Review Required';
}

const PURPOSE_WEIGHT: Record<string, number> = {
  KEY_ESTABLISHMENT: 1,
  DIGITAL_SIGNATURE: 2,
  AUTHENTICATION: 2,
  SIGNATURE: 2,
  ENCRYPTION: 3,
  HASHING: 4,
  MAC: 5,
};

export const TopMigrationPrioritiesCard: React.FC<TopMigrationPrioritiesCardProps> = ({
  assets,
  recommendations,
  loading,
  onSelectAsset,
}) => {
  if (loading) {
    return (
      <div className="rounded-xl border border-slate-800 bg-[#0B0F19] p-6 shadow-xl animate-pulse space-y-4">
        <div className="h-4 bg-slate-800 rounded w-1/3 mb-4" />
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-16 bg-slate-800/40 rounded-xl" />
        ))}
      </div>
    );
  }

  // Filter and sort assets by priority
  const sortedAssets = [...assets]
    .filter((a) => String(a.quantum_safety) === 'VULNERABLE' || String(a.quantum_safety) === 'QUANTUM_VULNERABLE' || String(a.quantum_safety) === 'UNKNOWN')
    .sort((a, b) => {
      // 1. Quantum Vulnerable assets first
      const isVulnA = String(a.quantum_safety) === 'VULNERABLE' || String(a.quantum_safety) === 'QUANTUM_VULNERABLE';
      const isVulnB = String(b.quantum_safety) === 'VULNERABLE' || String(b.quantum_safety) === 'QUANTUM_VULNERABLE';
      if (isVulnA && !isVulnB) return -1;
      if (!isVulnA && isVulnB) return 1;

      // 2. Purpose priority weight (KEY_ESTABLISHMENT > DIGITAL_SIGNATURE > ENCRYPTION)
      const weightA = PURPOSE_WEIGHT[a.purpose] || 99;
      const weightB = PURPOSE_WEIGHT[b.purpose] || 99;
      if (weightA !== weightB) return weightA - weightB;

      // 3. Name comparison
      return (a.name || '').localeCompare(b.name || '');
    })
    .slice(0, 5);

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0B0F19] p-6 shadow-xl space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <GitFork className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-semibold text-slate-100">Top Migration Priorities</h3>
        </div>
        <span className="text-[10px] font-mono text-slate-400 bg-slate-900 border border-slate-800 px-2.5 py-0.5 rounded-full">
          {sortedAssets.length} Action Items
        </span>
      </div>

      {/* Priority Rows */}
      {sortedAssets.length === 0 ? (
        <div className="py-12 text-center text-xs text-slate-500 font-mono space-y-2">
          <ShieldCheck className="w-8 h-8 text-emerald-400 mx-auto opacity-60" />
          <div className="text-slate-300 font-semibold">No migration priorities available for this repository yet.</div>
          <div className="text-slate-500 text-[11px]">Run a cryptographic scan to discover inventory assets.</div>
        </div>
      ) : (
        <div className="space-y-2.5">
          {sortedAssets.map((asset, idx) => {
            const recs = recommendations.get(asset.id) || [];
            const targetPqc = getPqcTarget(asset, recs);
            const rankStr = String(idx + 1).padStart(2, '0');

            return (
              <button
                key={asset.id}
                type="button"
                onClick={() => onSelectAsset(asset)}
                aria-label={`View migration priority details for ${asset.name}`}
                className="w-full text-left p-3 rounded-xl bg-slate-900/40 border border-slate-800/60 hover:bg-slate-800/50 hover:border-cyan-500/40 transition-all group cursor-pointer focus:outline-none focus:ring-1 focus:ring-cyan-500/50"
              >
                <div className="flex items-center justify-between gap-3">
                  {/* Left: Rank & Details */}
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <span className="text-xs font-mono font-bold text-cyan-400/80 bg-cyan-950/60 border border-cyan-800/60 px-2 py-1 rounded-md shrink-0">
                      {rankStr}
                    </span>

                    <div className="space-y-0.5 min-w-0">
                      <div className="text-xs font-bold font-mono text-slate-100 group-hover:text-cyan-300 transition-colors truncate">
                        {asset.name}
                      </div>
                      <div className="flex items-center gap-2 text-[11px] font-mono text-slate-400">
                        <span className="text-rose-300">{asset.algorithm_name}</span>
                        <ArrowRight className="w-3 h-3 text-cyan-500 shrink-0" />
                        <span className="text-emerald-300 truncate">{targetPqc}</span>
                      </div>
                    </div>
                  </div>

                  {/* Right: Badge & Action Chevron */}
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full border bg-amber-950/60 border-amber-800/60 text-amber-300 font-semibold">
                      Quantum-Vulnerable (Unassessed)
                    </span>
                    <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-cyan-400 group-hover:translate-x-0.5 transition-all" />
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};
