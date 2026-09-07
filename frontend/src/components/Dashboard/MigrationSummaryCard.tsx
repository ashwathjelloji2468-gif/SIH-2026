import React from 'react';
import { GitFork, ArrowRight, AlertTriangle, Shield } from 'lucide-react';
import { CryptoAsset, Recommendation } from '../../types';

interface MigrationSummaryCardProps {
  assets: CryptoAsset[];
  recommendations: Map<string, Recommendation[]>;
  loading: boolean;
}

const PQC_MAP: Record<string, string> = {
  'RSA': 'ML-KEM-768 / ML-DSA-65',
  'RSA-2048': 'ML-DSA-65',
  'RSA-4096': 'ML-DSA-87',
  'ECDSA': 'ML-DSA-44',
  'ECDSA-P256': 'ML-DSA-44',
  'ECDSA-P384': 'ML-DSA-65',
  'ECDH': 'ML-KEM-768',
  'ECDH-P256': 'ML-KEM-768',
  'X25519': 'ML-KEM-768',
  'Ed25519': 'ML-DSA-44',
  'DSA': 'ML-DSA-44',
  'DH': 'ML-KEM-768',
  'AES-128': 'AES-256 (Retain)',
  'AES-256': 'Retain',
  'AES': 'Retain',
  'SHA-256': 'SHA-256 (Retain)',
  'SHA-384': 'SHA-384 (Retain)',
  'SHA-512': 'SHA-512 (Retain)',
  'SHA': 'Retain',
  'HMAC': 'Retain',
};

function getPqcTarget(asset: CryptoAsset, recs: Recommendation[]): string {
  if (recs.length > 0) return recs[0].target_pqc_candidate;
  const alg = asset.algorithm_name?.toUpperCase() || '';
  for (const [key, val] of Object.entries(PQC_MAP)) {
    if (alg.includes(key.toUpperCase())) return val;
  }
  return 'Manual Review';
}

const riskColors: Record<string, string> = {
  CRITICAL: 'text-rose-400 bg-rose-950/60 border-rose-800/60',
  HIGH: 'text-orange-400 bg-orange-950/60 border-orange-800/60',
  MEDIUM: 'text-amber-400 bg-amber-950/60 border-amber-800/60',
  LOW: 'text-emerald-400 bg-emerald-950/60 border-emerald-800/60',
  NEGLIGIBLE: 'text-slate-400 bg-slate-900/60 border-slate-700/60',
};

export const MigrationSummaryCard: React.FC<MigrationSummaryCardProps> = ({
  assets,
  recommendations,
  loading,
}) => {
  if (loading) {
    return (
      <div className="rounded-xl border border-slate-800 bg-[#0B0F19] p-6 shadow-xl animate-pulse">
        <div className="h-4 bg-slate-800 rounded w-1/3 mb-6" />
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-12 bg-slate-800/40 rounded-lg mb-2" />
        ))}
      </div>
    );
  }

  // Show only vulnerable assets sorted by priority
  const vulnerableAssets = assets
    .filter((a) => a.quantum_safety === 'VULNERABLE')
    .slice(0, 8);

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0B0F19] p-6 shadow-xl">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
        <div className="flex items-center gap-2">
          <GitFork className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-semibold text-slate-100">Top Migration Priorities</h3>
        </div>
        <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">
          {vulnerableAssets.length} quantum-vulnerable
        </span>
      </div>

      {vulnerableAssets.length === 0 ? (
        <div className="py-8 text-center text-xs text-slate-500 font-mono">
          <Shield className="w-6 h-6 text-emerald-400 mx-auto mb-2 opacity-70" />
          No quantum-vulnerable assets found. Scan to discover.
        </div>
      ) : (
        <div className="space-y-2">
          {/* Header */}
          <div className="grid grid-cols-12 gap-2 text-[10px] font-mono text-slate-500 uppercase tracking-wider px-3 pb-1">
            <span className="col-span-4">Asset</span>
            <span className="col-span-3">Current</span>
            <span className="col-span-3">PQC Target</span>
            <span className="col-span-2 text-right">Risk</span>
          </div>

          {vulnerableAssets.map((asset) => {
            const recs = recommendations.get(asset.id) || [];
            const target = getPqcTarget(asset, recs);
            const isRetain = target.includes('Retain');
            const isManual = target === 'Manual Review';

            return (
              <div
                key={asset.id}
                className="grid grid-cols-12 gap-2 items-center rounded-lg bg-slate-900/40 border border-slate-800/50 px-3 py-2.5 hover:bg-slate-800/40 transition-colors text-xs font-mono"
              >
                <div className="col-span-4 truncate text-slate-200" title={asset.name}>
                  {asset.name}
                </div>
                <div className="col-span-3 text-rose-300 truncate" title={asset.algorithm_name}>
                  {asset.algorithm_name}
                </div>
                <div className="col-span-3 flex items-center gap-1 truncate">
                  {!isRetain && !isManual && (
                    <ArrowRight className="w-3 h-3 text-cyan-500 shrink-0" />
                  )}
                  {isManual && (
                    <AlertTriangle className="w-3 h-3 text-amber-500 shrink-0" />
                  )}
                  <span
                    className={
                      isRetain
                        ? 'text-emerald-300'
                        : isManual
                        ? 'text-amber-300'
                        : 'text-cyan-300'
                    }
                    title={target}
                  >
                    {target}
                  </span>
                </div>
                <div className="col-span-2 flex justify-end">
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded-full border font-bold ${
                      riskColors['HIGH'] || riskColors['MEDIUM']
                    }`}
                  >
                    VULNERABLE
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
