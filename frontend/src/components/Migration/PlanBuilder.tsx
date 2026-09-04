import React, { useState } from 'react';
import { GitFork, Loader2, Sparkles, AlertCircle } from 'lucide-react';
import { useProject } from '../../context/ProjectContext';
import { migrationService } from '../../services/migrationService';
import { MigrationPlan, TestingRequirement } from '../../types';

interface PlanBuilderProps {
  onPlanCreated: (plan: MigrationPlan) => void;
}

export const PlanBuilder: React.FC<PlanBuilderProps> = ({ onPlanCreated }) => {
  const { currentProject } = useProject();
  const [name, setName] = useState<string>('PQC Modernization Phase 1 — Hybrid KEM/DSA');
  const [vendorDeps, setVendorDeps] = useState<number>(2);
  const [pkiDeps, setPkiDeps] = useState<number>(3);
  const [cryptoAgility, setCryptoAgility] = useState<number>(0.65);
  const [testingLevel, setTestingLevel] = useState<TestingRequirement>('HIGH');
  const [engineers, setEngineers] = useState<number>(4);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreatePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentProject) return;

    setLoading(true);
    setError(null);

    try {
      const plan = await migrationService.createPlan(currentProject.id, {
        name,
        vendor_dependency_count: vendorDeps,
        pki_cert_dependency_count: pkiDeps,
        crypto_agility_score: cryptoAgility,
        testing_requirement_level: testingLevel,
        engineering_capacity_developers: engineers,
      });
      onPlanCreated(plan);
    } catch (err: any) {
      setError(err.message || 'Failed to generate migration plan.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-xl space-y-6">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-cyan-950/70 border border-cyan-800/50 text-cyan-400">
            <GitFork className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-slate-100">Post-Quantum Migration Planner</h3>
            <p className="text-xs text-slate-400">Algorithmic effort estimation based on discovery findings & agility posture</p>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-rose-950/50 border border-rose-800/60 text-xs text-rose-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleCreatePlan} className="space-y-4">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5">Migration Plan Title</label>
          <input
            type="text"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-xs font-mono focus:outline-none focus:border-cyan-500"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Third-Party Vendor Dependencies: <span className="text-cyan-300 font-mono font-bold">{vendorDeps}</span>
            </label>
            <input
              type="range"
              min={0}
              max={15}
              value={vendorDeps}
              onChange={(e) => setVendorDeps(Number(e.target.value))}
              className="w-full accent-cyan-400 cursor-pointer"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              PKI & Certificate Dependencies: <span className="text-cyan-300 font-mono font-bold">{pkiDeps}</span>
            </label>
            <input
              type="range"
              min={0}
              max={20}
              value={pkiDeps}
              onChange={(e) => setPkiDeps(Number(e.target.value))}
              className="w-full accent-cyan-400 cursor-pointer"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Current Crypto-Agility Score: <span className="text-cyan-300 font-mono font-bold">{Math.round(cryptoAgility * 100)}%</span>
            </label>
            <input
              type="range"
              min={0.1}
              max={1.0}
              step={0.05}
              value={cryptoAgility}
              onChange={(e) => setCryptoAgility(Number(e.target.value))}
              className="w-full accent-cyan-400 cursor-pointer"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Testing Requirement Rigor</label>
            <select
              value={testingLevel}
              onChange={(e) => setTestingLevel(e.target.value as TestingRequirement)}
              className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-cyan-500"
            >
              <option value="BASIC">BASIC (Unit tests only)</option>
              <option value="STANDARD">STANDARD (Unit + functional)</option>
              <option value="HIGH">HIGH (FIPS validation + fuzzing)</option>
              <option value="STRICT">STRICT (Formal verification + continuous regression)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Engineering Capacity (Developers): <span className="text-cyan-300 font-mono font-bold">{engineers} devs</span>
            </label>
            <input
              type="range"
              min={1}
              max={20}
              value={engineers}
              onChange={(e) => setEngineers(Number(e.target.value))}
              className="w-full accent-cyan-400 cursor-pointer"
            />
          </div>
        </div>

        <div className="pt-3 flex justify-end">
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs tracking-wide shadow-lg shadow-cyan-950/50 cursor-pointer"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Generating Quantified Plan...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Synthesize Migration Roadmap</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
