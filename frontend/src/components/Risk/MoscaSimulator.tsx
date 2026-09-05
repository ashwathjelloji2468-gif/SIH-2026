import React, { useState, useEffect } from 'react';
import { AlertTriangle, ShieldCheck, Sliders, Info, RotateCcw, Plus, Loader2, Sparkles } from 'lucide-react';
import { ThreatScenario } from '../../types';
import { riskService } from '../../services/riskService';

interface MoscaSimulatorProps {
  scenarios?: ThreatScenario[];
  onScenarioSelect?: (scenario: ThreatScenario) => void;
}

export const MoscaSimulator: React.FC<MoscaSimulatorProps> = ({ scenarios: initialScenarios = [] }) => {
  const currentYear = new Date().getFullYear();

  // State for Mosca inputs
  const [xLifetime, setXLifetime] = useState<number>(10); // Data shelf-life in years
  const [yMigration, setYMigration] = useState<number>(3); // Migration duration in years
  const [zHorizonYear, setZHorizonYear] = useState<number>(2033); // CRQC arrival year
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('moderate');
  const [scenarios, setScenarios] = useState<ThreatScenario[]>(initialScenarios);
  const [backendImpact, setBackendImpact] = useState<string | null>(null);
  const [impactLoading, setImpactLoading] = useState<boolean>(false);

  // Custom scenario creation state
  const [customModalOpen, setCustomModalOpen] = useState<boolean>(false);
  const [customName, setCustomName] = useState<string>('Enterprise Banking Confidentiality Horizon');
  const [customZ, setCustomZ] = useState<number>(2031);
  const [customX, setCustomX] = useState<number>(12);
  const [customY, setCustomY] = useState<number>(4);

  // Load backend scenarios if not provided
  useEffect(() => {
    if (scenarios.length === 0) {
      riskService.listThreatScenarios().then((data) => {
        if (data && data.length > 0) {
          setScenarios(data);
          handleSelectScenario(data[0]);
        }
      }).catch(console.error);
    }
  }, []);

  const handleSelectScenario = async (scen: ThreatScenario) => {
    setSelectedScenarioId(scen.id);
    if (scen.data_lifetime_years) setXLifetime(scen.data_lifetime_years);
    if (scen.migration_time_years) setYMigration(scen.migration_time_years);
    if (scen.quantum_threat_horizon_year) setZHorizonYear(scen.quantum_threat_horizon_year);

    setImpactLoading(true);
    try {
      const imp = await riskService.getScenarioImpact(scen.id);
      setBackendImpact(imp.impact_summary);
    } catch {
      setBackendImpact(null);
    } finally {
      setImpactLoading(false);
    }
  };

  const handleCreateCustom = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const created = await riskService.createThreatScenario({
        name: customName,
        scenario_type: 'CUSTOM',
        quantum_threat_horizon_year: customZ,
        data_lifetime_years: customX,
        migration_time_years: customY,
        description: 'User-defined organizational threat scenario',
      });
      setScenarios([...scenarios, created]);
      setSelectedScenarioId(created.id);
      setXLifetime(customX);
      setYMigration(customY);
      setZHorizonYear(customZ);
      setCustomModalOpen(false);
    } catch (err) {
      console.error('Failed to create custom scenario:', err);
    }
  };

  const yearsUntilZ = Math.max(0, zHorizonYear - currentYear);
  const totalRequiredYears = xLifetime + yMigration;
  const isBreached = totalRequiredYears > yearsUntilZ;
  const gapYears = Math.abs(totalRequiredYears - yearsUntilZ);

  return (
    <div className="rounded-3xl border border-slate-800 bg-[#0B0F19] p-6 sm:p-8 lg:p-10 shadow-2xl space-y-8">
      {/* Header & Threat Scenario Presets */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-6 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs font-semibold uppercase tracking-wider mb-1">
            <Sliders className="w-4 h-4" />
            <span>Interactive Mosca Theorem Engine</span>
          </div>
          <h2 className="text-2xl font-bold font-mono text-slate-100">Quantum Urgency & Shelf-Life Gap Simulator</h2>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Evaluate whether your cryptographic data protection timeline will be breached prior to completed post-quantum migration.
          </p>
        </div>

        {/* Backend Scenarios Selector */}
        <div className="flex flex-wrap items-center gap-2 shrink-0">
          <div className="flex items-center gap-1.5 bg-slate-900 p-1 rounded-xl border border-slate-800 font-mono text-xs">
            {scenarios.map((scen) => {
              const isSelected = selectedScenarioId.toLowerCase() === scen.id.toLowerCase();
              return (
                <button
                  key={scen.id}
                  onClick={() => handleSelectScenario(scen)}
                  className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer capitalize ${
                    isSelected
                      ? 'bg-cyan-950/80 text-cyan-300 font-bold border border-cyan-800/80 shadow-xs'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {scen.name || scen.id}
                </button>
              );
            })}
          </div>

          <button
            onClick={() => setCustomModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-800 bg-slate-900/60 hover:bg-slate-800 text-slate-300 text-xs font-mono font-medium transition-colors cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5 text-cyan-400" />
            <span>Custom</span>
          </button>
        </div>
      </div>

      {/* Main Interactive Controls & Visual Feedback */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Sliders (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Slider X: Data Protection Lifetime */}
          <div className="space-y-2 rounded-2xl bg-[#080C16] border border-slate-800/90 p-4.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-slate-200 flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
                <span>X: Data Protection Lifetime (Confidentiality Shelf-Life)</span>
              </label>
              <span className="font-mono text-sm font-bold text-cyan-400 bg-cyan-950/70 px-2.5 py-0.5 rounded-full border border-cyan-800/60">
                {xLifetime} Years
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Years that customer records, financial ledgers, or secrets must remain confidential.
            </p>
            <input
              type="range"
              min={1}
              max={30}
              value={xLifetime}
              onChange={(e) => setXLifetime(Number(e.target.value))}
              className="w-full accent-cyan-400 cursor-pointer h-1.5 bg-slate-900 rounded-lg"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>1 Year (Transient Tokens)</span>
              <span>15 Years (Financial / PII)</span>
              <span>30 Years (Defense / Health)</span>
            </div>
          </div>

          {/* Slider Y: Migration Time */}
          <div className="space-y-2 rounded-2xl bg-[#080C16] border border-slate-800/90 p-4.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-slate-200 flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-blue-400" />
                <span>Y: Migration Time (Upgrade & Agility Execution)</span>
              </label>
              <span className="font-mono text-sm font-bold text-blue-400 bg-blue-950/70 px-2.5 py-0.5 rounded-full border border-blue-800/60">
                {yMigration} Years
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Time to refactor code, reissue PKI certs, update protocol dependencies, and test.
            </p>
            <input
              type="range"
              min={1}
              max={10}
              value={yMigration}
              onChange={(e) => setYMigration(Number(e.target.value))}
              className="w-full accent-blue-400 cursor-pointer h-1.5 bg-slate-900 rounded-lg"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>1 Year (Agile Service)</span>
              <span>5 Years (Multi-Tier Enterprise)</span>
              <span>10 Years (Legacy Infrastructure)</span>
            </div>
          </div>

          {/* Slider Z: Quantum Threat Horizon Year */}
          <div className="space-y-2 rounded-2xl bg-[#080C16] border border-slate-800/90 p-4.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-slate-200 flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-purple-400" />
                <span>Z: Quantum Threat Horizon (CRQC Realization Year)</span>
              </label>
              <span className="font-mono text-sm font-bold text-purple-400 bg-purple-950/70 px-2.5 py-0.5 rounded-full border border-purple-800/60">
                Year {zHorizonYear} ({yearsUntilZ}y remaining)
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Projected arrival year of a Cryptanalytically Relevant Quantum Computer running Shor's Algorithm.
            </p>
            <input
              type="range"
              min={currentYear}
              max={2045}
              value={zHorizonYear}
              onChange={(e) => setZHorizonYear(Number(e.target.value))}
              className="w-full accent-purple-400 cursor-pointer h-1.5 bg-slate-900 rounded-lg"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>{currentYear} (Immediate)</span>
              <span>2033 (NIST Recommended Target)</span>
              <span>2045 (Distal Horizon)</span>
            </div>
          </div>
        </div>

        {/* Outcome Display Gauge (5 cols) */}
        <div className="lg:col-span-5 flex flex-col justify-between rounded-2xl border border-slate-800 bg-[#080C16] p-6 space-y-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase tracking-wider text-slate-400">Inequality Outcome</span>
              <span
                className={`text-xs px-3 py-0.5 rounded-full border font-mono font-bold uppercase ${
                  isBreached
                    ? 'bg-rose-950 text-rose-300 border-rose-700 animate-pulse'
                    : 'bg-emerald-950 text-emerald-300 border-emerald-700'
                }`}
              >
                {isBreached ? 'DEADLINE BREACH' : 'CONTROLLED HORIZON'}
              </span>
            </div>

            {/* Formula Status */}
            <div className="rounded-xl bg-[#0B0F19] border border-slate-800/90 p-4 font-mono text-center shadow-inner">
              <div className="text-[11px] text-slate-400 mb-1 font-sans">Condition: X + Y &gt; Z</div>
              <div className="text-2xl font-extrabold tracking-wide">
                <span className="text-cyan-400">{xLifetime}y</span> + <span className="text-blue-400">{yMigration}y</span>{' '}
                <span className={isBreached ? 'text-rose-400 font-black text-2xl' : 'text-emerald-400'}>
                  {isBreached ? '>' : '≤'}
                </span>{' '}
                <span className="text-purple-400">{yearsUntilZ}y</span>
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                {totalRequiredYears} Total Years Required vs {yearsUntilZ} Years Until CRQC
              </div>
            </div>

            {/* Impact Explanation */}
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-2">
              <div className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                {isBreached ? <AlertTriangle className="w-4 h-4 text-rose-400" /> : <ShieldCheck className="w-4 h-4 text-emerald-400" />}
                <span>{isBreached ? 'Harvest Now, Decrypt Later (HNDL) Exposure:' : 'Protection Margin:'}</span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed font-sans">
                {isBreached ? (
                  <>
                    Your data protection shelf-life exceeds the quantum threat horizon by{' '}
                    <strong className="text-rose-400 font-mono font-bold">{gapYears} year(s)</strong>. Adversaries recording ciphertext today can decrypt customer data upon CRQC arrival in {zHorizonYear}.
                  </>
                ) : (
                  <>
                    Your infrastructure maintains a safety buffer of{' '}
                    <strong className="text-emerald-400 font-mono font-bold">{gapYears} year(s)</strong> before sensitive data becomes exposed. Continue active PQC migration planning.
                  </>
                )}
              </p>
            </div>

            {backendImpact && (
              <div className="text-[11px] font-mono text-cyan-300 bg-cyan-950/40 p-2.5 rounded-xl border border-cyan-800/50">
                <strong>Backend Impact Engine:</strong> {backendImpact}
              </div>
            )}
          </div>

          {/* Timeline Visual Bar */}
          <div className="space-y-2 pt-2 border-t border-slate-800/80">
            <div className="flex justify-between text-[11px] font-mono text-slate-400">
              <span>Required: {totalRequiredYears}y</span>
              <span>Available: {yearsUntilZ}y</span>
            </div>
            <div className="w-full bg-slate-900 h-2.5 rounded-full overflow-hidden p-0.5 border border-slate-800">
              <div
                className={`h-full rounded-full transition-all duration-300 ${
                  isBreached
                    ? 'bg-gradient-to-r from-orange-500 via-rose-500 to-red-600'
                    : 'bg-gradient-to-r from-teal-500 to-emerald-400'
                }`}
                style={{ width: `${Math.min(100, Math.round((totalRequiredYears / Math.max(1, yearsUntilZ)) * 70))}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Assumptions & Scientific Sources Disclosure */}
      <div className="rounded-2xl border border-[#22D3EE]/30 bg-[#1E293B] p-6 space-y-4 shadow-xl">
        <div className="flex items-center gap-2 text-xs font-mono font-bold text-[#22D3EE] uppercase tracking-wider">
          <Info className="w-4 h-4 text-[#22D3EE]" />
          <span>Scientific Modeling & Variable Assumptions (Dr. Michele Mosca Theorem)</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
          <div className="p-3.5 rounded-xl bg-[#0B1120] border border-slate-700/60 space-y-1">
            <span className="text-[#22D3EE] font-bold block">X: Data Protection Lifetime</span>
            <p className="text-[#94A3B8] text-[11px] font-sans">
              <strong>Source:</strong> Enterprise Data Retention Policy & NIST Special Publication 800-88. Defines how long confidential data remains sensitive.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-[#0B1120] border border-slate-700/60 space-y-1">
            <span className="text-blue-400 font-bold block">Y: Estimated Migration Time</span>
            <p className="text-[#94A3B8] text-[11px] font-sans">
              <strong>Source:</strong> NIST PQC Agility & Transition Guidelines. Duration required to refactor AST code, reissue PKI certs, and test dependencies.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-[#0B1120] border border-slate-700/60 space-y-1">
            <span className="text-purple-400 font-bold block">Z: Quantum Threat Horizon</span>
            <p className="text-[#94A3B8] text-[11px] font-sans">
              <strong>Source:</strong> Dr. Michele Mosca (University of Waterloo) & NIST IR 8413. Projected arrival year of Cryptanalytically Relevant Quantum Computers (CRQC).
            </p>
          </div>
        </div>
      </div>

      {/* Custom Threat Scenario Modal */}
      {customModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-bold font-mono text-slate-100">Create Custom Threat Scenario</h3>
            <p className="text-xs text-slate-400">Define an organizational threat horizon for compliance modeling</p>

            <form onSubmit={handleCreateCustom} className="space-y-4 font-mono text-xs">
              <div>
                <label className="block text-slate-300 mb-1">Scenario Name</label>
                <input
                  type="text"
                  required
                  value={customName}
                  onChange={(e) => setCustomName(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1">Data Lifetime (X years): {customX}y</label>
                <input
                  type="range"
                  min={1}
                  max={30}
                  value={customX}
                  onChange={(e) => setCustomX(Number(e.target.value))}
                  className="w-full accent-cyan-400 cursor-pointer"
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1">Migration Duration (Y years): {customY}y</label>
                <input
                  type="range"
                  min={1}
                  max={10}
                  value={customY}
                  onChange={(e) => setCustomY(Number(e.target.value))}
                  className="w-full accent-blue-400 cursor-pointer"
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1">Threat Horizon Year (Z): {customZ}</label>
                <input
                  type="range"
                  min={currentYear}
                  max={2045}
                  value={customZ}
                  onChange={(e) => setCustomZ(Number(e.target.value))}
                  className="w-full accent-purple-400 cursor-pointer"
                />
              </div>

              <div className="pt-3 flex justify-end gap-3 border-t border-slate-800 font-sans">
                <button
                  type="button"
                  onClick={() => setCustomModalOpen(false)}
                  className="px-4 py-2 rounded-xl border border-slate-800 text-slate-300 text-xs hover:bg-slate-900 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs shadow-md shadow-cyan-950/50 cursor-pointer"
                >
                  Save Scenario
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
