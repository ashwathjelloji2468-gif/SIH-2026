import React, { useState } from 'react';
import { AlertTriangle, ShieldCheck, Sliders, Info, RotateCcw, Bookmark } from 'lucide-react';
import { ThreatScenario } from '../../types';

interface MoscaSimulatorProps {
  scenarios?: ThreatScenario[];
  onScenarioSelect?: (scenario: ThreatScenario) => void;
}

export const MoscaSimulator: React.FC<MoscaSimulatorProps> = ({ scenarios = [] }) => {
  const currentYear = new Date().getFullYear();

  // State for Mosca inputs
  const [xLifetime, setXLifetime] = useState<number>(10); // Data shelf-life in years
  const [yMigration, setYMigration] = useState<number>(3); // Migration duration in years
  const [zHorizonYear, setZHorizonYear] = useState<number>(2033); // CRQC arrival year
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('MODERATE');

  const yearsUntilZ = Math.max(0, zHorizonYear - currentYear);
  const totalRequiredYears = xLifetime + yMigration;
  const isBreached = totalRequiredYears > yearsUntilZ;
  const gapYears = Math.abs(totalRequiredYears - yearsUntilZ);

  // Scenario presets
  const applyPreset = (type: 'CONSERVATIVE' | 'MODERATE' | 'AGGRESSIVE') => {
    setSelectedScenarioId(type);
    if (type === 'CONSERVATIVE') {
      setZHorizonYear(2029);
      setXLifetime(12);
      setYMigration(4);
    } else if (type === 'MODERATE') {
      setZHorizonYear(2033);
      setXLifetime(10);
      setYMigration(3);
    } else if (type === 'AGGRESSIVE') {
      setZHorizonYear(2038);
      setXLifetime(7);
      setYMigration(2);
    }
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 md:p-8 shadow-2xl space-y-8">
      {/* Header & Scenario Presets */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs font-semibold uppercase tracking-wider mb-1">
            <Sliders className="w-4 h-4" />
            <span>Interactive Mosca Theorem Model</span>
          </div>
          <h2 className="text-xl font-bold text-slate-100">Quantum Urgency & Shelf-Life Gap Simulator</h2>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Evaluate whether your cryptographic data protection timeline will be compromised prior to completed post-quantum migration.
          </p>
        </div>

        {/* Preset Selector Buttons */}
        <div className="flex items-center gap-2 bg-slate-900/80 p-1 rounded-xl border border-slate-800 shrink-0 font-mono text-xs">
          <button
            onClick={() => applyPreset('CONSERVATIVE')}
            className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
              selectedScenarioId === 'CONSERVATIVE'
                ? 'bg-rose-950/80 text-rose-300 font-semibold border border-rose-800/80'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Conservative (2029)
          </button>
          <button
            onClick={() => applyPreset('MODERATE')}
            className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
              selectedScenarioId === 'MODERATE'
                ? 'bg-cyan-950/80 text-cyan-300 font-semibold border border-cyan-800/80'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Moderate (2033)
          </button>
          <button
            onClick={() => applyPreset('AGGRESSIVE')}
            className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
              selectedScenarioId === 'AGGRESSIVE'
                ? 'bg-purple-950/80 text-purple-300 font-semibold border border-purple-800/80'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Aggressive (2038)
          </button>
        </div>
      </div>

      {/* Main Interactive Controls & Visual Feedback */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Sliders (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Slider X: Data Protection Lifetime */}
          <div className="space-y-2 rounded-xl bg-slate-900/40 border border-slate-800/80 p-4">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-cyan-400" />
                <span>X: Data Protection Lifetime (Shelf-Life)</span>
              </label>
              <span className="font-mono text-sm font-bold text-cyan-400 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/50">
                {xLifetime} Years
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              How many years must sensitive customer, banking, or medical records remain confidential?
            </p>
            <input
              type="range"
              min={1}
              max={30}
              value={xLifetime}
              onChange={(e) => setXLifetime(Number(e.target.value))}
              className="w-full accent-cyan-400 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>1 Year (Transient)</span>
              <span>15 Years (Financial)</span>
              <span>30 Years (Gov / Health)</span>
            </div>
          </div>

          {/* Slider Y: Migration Time */}
          <div className="space-y-2 rounded-xl bg-slate-900/40 border border-slate-800/80 p-4">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-blue-400" />
                <span>Y: Migration Time (Upgrade Execution)</span>
              </label>
              <span className="font-mono text-sm font-bold text-blue-400 bg-blue-950/60 px-2 py-0.5 rounded border border-blue-800/50">
                {yMigration} Years
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Years required to refactor code, update PKI certificates, deploy PQC libraries, and achieve agility.
            </p>
            <input
              type="range"
              min={1}
              max={10}
              value={yMigration}
              onChange={(e) => setYMigration(Number(e.target.value))}
              className="w-full accent-blue-400 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>1 Year (Agile Microservice)</span>
              <span>5 Years (Complex System)</span>
              <span>10 Years (Legacy Mainframe)</span>
            </div>
          </div>

          {/* Slider Z: Quantum Threat Horizon Year */}
          <div className="space-y-2 rounded-xl bg-slate-900/40 border border-slate-800/80 p-4">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-purple-400" />
                <span>Z: Quantum Threat Horizon (CRQC Arrival)</span>
              </label>
              <span className="font-mono text-sm font-bold text-purple-400 bg-purple-950/60 px-2 py-0.5 rounded border border-purple-800/50">
                Year {zHorizonYear} ({yearsUntilZ}y remaining)
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Projected year a quantum computer breaks RSA-2048 and ECC via Shor's Algorithm.
            </p>
            <input
              type="range"
              min={currentYear}
              max={2045}
              value={zHorizonYear}
              onChange={(e) => setZHorizonYear(Number(e.target.value))}
              className="w-full accent-purple-400 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>{currentYear} (Immediate)</span>
              <span>2033 (NIST Target)</span>
              <span>2045 (Distant)</span>
            </div>
          </div>
        </div>

        {/* Outcome Display Gauge (5 cols) */}
        <div className="lg:col-span-5 flex flex-col justify-between rounded-xl border border-slate-800 bg-slate-950/70 p-6 space-y-6">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase tracking-wider text-slate-400">Inequality Outcome</span>
              <span
                className={`text-xs px-2.5 py-0.5 rounded-full border font-mono font-bold uppercase ${
                  isBreached
                    ? 'bg-rose-950 text-rose-300 border-rose-700 animate-pulse'
                    : 'bg-emerald-950 text-emerald-300 border-emerald-700'
                }`}
              >
                {isBreached ? 'CRITICAL EXPOSURE' : 'SAFE TIMELINE'}
              </span>
            </div>

            {/* Formula Status */}
            <div className="rounded-lg bg-slate-900 border border-slate-800 p-4 font-mono text-center">
              <div className="text-xs text-slate-400 mb-1 font-sans">Condition: X + Y &gt; Z</div>
              <div className="text-xl font-extrabold">
                <span className="text-cyan-400">{xLifetime}</span> + <span className="text-blue-400">{yMigration}</span>{' '}
                <span className={isBreached ? 'text-rose-400 font-black' : 'text-emerald-400'}>
                  {isBreached ? '>' : '≤'}
                </span>{' '}
                <span className="text-purple-400">{yearsUntilZ}</span>
              </div>
              <div className="text-xs text-slate-400 mt-1">
                {totalRequiredYears} Total Years vs {yearsUntilZ} Years Available
              </div>
            </div>

            <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-800 space-y-2">
              <div className="text-xs font-semibold text-slate-200">
                {isBreached ? 'Harvest Now, Decrypt Later (HNDL) Risk:' : 'Protection Status:'}
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                {isBreached ? (
                  <>
                    Your security requirements exceed the threat horizon by{' '}
                    <strong className="text-rose-400 font-mono">{gapYears} year(s)</strong>. Adversarial eavesdropping today will yield decrypted cleartext upon CRQC realization in {zHorizonYear}.
                  </>
                ) : (
                  <>
                    Your system maintains a safety margin of{' '}
                    <strong className="text-emerald-400 font-mono">{gapYears} year(s)</strong> before data confidentiality is compromised.
                  </>
                )}
              </p>
            </div>
          </div>

          {/* Timeline Visual Bar */}
          <div className="space-y-2">
            <div className="flex justify-between text-[11px] font-mono text-slate-400">
              <span>Required: {totalRequiredYears}y</span>
              <span>Available: {yearsUntilZ}y</span>
            </div>
            <div className="w-full bg-slate-900 h-3 rounded-full overflow-hidden p-0.5 border border-slate-800">
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

      {/* Assumptions & Sources Disclaimer */}
      <div className="rounded-xl border border-slate-800/80 bg-slate-900/30 p-4 flex items-start gap-3 text-xs text-slate-400">
        <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <span className="font-semibold text-slate-200">Scientific Methodology & Limitations:</span>
          <p className="leading-relaxed">
            The Mosca Theorem (formulated by Dr. Michele Mosca, Institute for Quantum Computing) does not predict an exact quantum arrival date. Rather, it calculates risk boundaries based on engineering estimates, key size, and cryptographic agility. Quantum threat horizon estimates are derived from NIST IR 8413 and Cloud Security Alliance (CSA) Quantum-Safe working groups.
          </p>
        </div>
      </div>
    </div>
  );
};
