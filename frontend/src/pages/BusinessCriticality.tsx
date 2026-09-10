import React, { useState } from 'react';
import { Sliders, Calculator, ShieldAlert, Info, RotateCcw, Cpu, CheckCircle2 } from 'lucide-react';

interface FactorDefinition {
  id: string;
  name: string;
  weight: number;
  description: string;
}

const FACTORS: FactorDefinition[] = [
  { id: 'dataSensitivity', name: 'Data Sensitivity', weight: 0.15, description: 'Classification level of processed or stored data (Public to Secret).' },
  { id: 'dataShelfLife', name: 'Data Shelf-Life', weight: 0.10, description: 'Duration for which confidentiality must be maintained.' },
  { id: 'confidentialityImpact', name: 'Confidentiality Impact', weight: 0.15, description: 'Impact level if encrypted data is compromised or decrypted.' },
  { id: 'integrityImpact', name: 'Integrity Impact', weight: 0.10, description: 'Impact of unauthorized data modification or signature forgery.' },
  { id: 'availabilityImpact', name: 'Availability Impact', weight: 0.10, description: 'System downtime and service interruption exposure.' },
  { id: 'regulatoryExposure', name: 'Regulatory Exposure', weight: 0.15, description: 'Compliance penalties, audit breaches, and regulatory fines.' },
  { id: 'financialImpact', name: 'Financial Impact', weight: 0.15, description: 'Direct financial loss, transaction liability, and breach costs.' },
  { id: 'reputationalImpact', name: 'Reputational Impact', weight: 0.10, description: 'Customer trust loss, brand damage, and public disclosure impact.' },
];

export const BusinessCriticality: React.FC = () => {
  // Initial ratings set to match the exact Worked Example (4.60 WIS -> 4.22 Normalized)
  const [ratings, setRatings] = useState<Record<string, number>>({
    dataSensitivity: 5,
    dataShelfLife: 4,
    confidentialityImpact: 5,
    integrityImpact: 4,
    availabilityImpact: 4,
    regulatoryExposure: 5,
    financialImpact: 5,
    reputationalImpact: 4,
  });

  const [exposureRating, setExposureRating] = useState<number>(4);

  const handleRatingChange = (id: string, value: number) => {
    setRatings((prev) => ({ ...prev, [id]: value }));
  };

  const handleReset = () => {
    setRatings({
      dataSensitivity: 5,
      dataShelfLife: 4,
      confidentialityImpact: 5,
      integrityImpact: 4,
      availabilityImpact: 4,
      regulatoryExposure: 5,
      financialImpact: 5,
      reputationalImpact: 4,
    });
    setExposureRating(4);
  };

  // Calculations matching Worked Example formulas
  const contributions = FACTORS.map((f) => ({
    ...f,
    rating: ratings[f.id] ?? 0,
    contribution: (ratings[f.id] ?? 0) * f.weight,
  }));

  const wis = contributions.reduce((sum, item) => sum + item.contribution, 0);

  // Exposure Multiplier calculation: EM = 1.0 + 0.09375 * exposureRating (Rating 4 -> EM = 1.375)
  const exposureMultiplier = 1.0 + 0.09375 * exposureRating;
  const rawScore = wis * exposureMultiplier;
  const normalizedValue = Math.min(5.0, Number((rawScore / 1.5).toFixed(2)));

  const getCriticalityBadge = (val: number) => {
    if (val >= 4.0) return { label: 'CRITICAL', class: 'bg-rose-950/80 border-rose-700/80 text-rose-300' };
    if (val >= 3.0) return { label: 'HIGH', class: 'bg-orange-950/80 border-orange-700/80 text-orange-300' };
    if (val >= 2.0) return { label: 'MEDIUM', class: 'bg-amber-950/80 border-amber-700/80 text-amber-300' };
    return { label: 'LOW', class: 'bg-emerald-950/80 border-emerald-700/80 text-emerald-300' };
  };

  const badge = getCriticalityBadge(normalizedValue);

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider font-semibold mb-1">
            <Sliders className="w-4 h-4" />
            <span>Governance &amp; Compliance Framework</span>
          </div>
          <h1 className="text-2xl font-bold font-mono text-slate-100">Business Criticality Factors</h1>
          <p className="text-xs text-slate-400 mt-1">
            Interactive Weighted Impact Score (WIS) &amp; Exposure Multiplier (EM) demonstrator.
          </p>
        </div>

        <button
          onClick={handleReset}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 text-xs font-mono transition-colors cursor-pointer self-start sm:self-auto"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Reset Worked Example</span>
        </button>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="rounded-xl border border-cyan-800/60 bg-gradient-to-br from-cyan-950/40 via-[#0B0F19] to-[#0B0F19] p-4">
          <div className="text-[11px] font-mono text-cyan-400 uppercase tracking-wider">Weighted Impact (WIS)</div>
          <div className="text-2xl font-bold font-mono text-slate-100 mt-1">{wis.toFixed(2)} <span className="text-xs text-slate-500">/ 5.00</span></div>
          <p className="text-[10px] text-slate-400 mt-1 font-mono">Sum of factor ratings × weights</p>
        </div>

        <div className="rounded-xl border border-amber-800/60 bg-gradient-to-br from-amber-950/40 via-[#0B0F19] to-[#0B0F19] p-4">
          <div className="text-[11px] font-mono text-amber-400 uppercase tracking-wider">Exposure Multiplier</div>
          <div className="text-2xl font-bold font-mono text-amber-300 mt-1">{exposureMultiplier.toFixed(3)}x</div>
          <p className="text-[10px] text-slate-400 mt-1 font-mono">Rating {exposureRating} (EM = 1 + 0.09375×Rating)</p>
        </div>

        <div className="rounded-xl border border-purple-800/60 bg-gradient-to-br from-purple-950/40 via-[#0B0F19] to-[#0B0F19] p-4">
          <div className="text-[11px] font-mono text-purple-400 uppercase tracking-wider">Raw Score (WIS × EM)</div>
          <div className="text-2xl font-bold font-mono text-purple-300 mt-1">{rawScore.toFixed(3)}</div>
          <p className="text-[10px] text-slate-400 mt-1 font-mono">{wis.toFixed(2)} × {exposureMultiplier.toFixed(3)}</p>
        </div>

        <div className="rounded-xl border border-rose-800/60 bg-gradient-to-br from-rose-950/40 via-[#0B0F19] to-[#0B0F19] p-4">
          <div className="flex justify-between items-center">
            <span className="text-[11px] font-mono text-rose-400 uppercase tracking-wider">Normalized Score</span>
            <span className={`text-[10px] px-2 py-0.5 rounded font-mono font-bold border ${badge.class}`}>
              {badge.label}
            </span>
          </div>
          <div className="text-2xl font-bold font-mono text-slate-100 mt-1">{normalizedValue.toFixed(2)} <span className="text-xs text-slate-500">/ 5.00</span></div>
          <p className="text-[10px] text-slate-400 mt-1 font-mono">min(5, {rawScore.toFixed(3)} / 1.5) = {normalizedValue.toFixed(2)}</p>
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Interactive Factor Sliders */}
        <div className="lg:col-span-6 rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-xl space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h2 className="text-base font-bold font-mono text-slate-100 flex items-center gap-2">
              <Calculator className="w-4 h-4 text-cyan-400" />
              Factor Rating Sliders (0 – 5)
            </h2>
            <span className="text-xs font-mono text-slate-400">Total Weight: 100%</span>
          </div>

          <div className="space-y-4">
            {FACTORS.map((f) => {
              const ratingVal = ratings[f.id] ?? 0;
              const contribVal = (ratingVal * f.weight).toFixed(2);
              return (
                <div key={f.id} className="p-3 rounded-xl bg-[#06080F] border border-slate-800/80 space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="font-semibold text-slate-200">{f.name}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-slate-500 text-[11px]">Weight: {(f.weight * 100).toFixed(0)}%</span>
                      <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 font-bold">
                        Rating: {ratingVal}
                      </span>
                      <span className="text-emerald-400 font-bold text-[11px]">
                        +{contribVal}
                      </span>
                    </div>
                  </div>

                  {/* Segmented 0-5 Button Selector + Range Slider */}
                  <div className="space-y-2">
                    <div className="grid grid-cols-6 gap-1">
                      {[0, 1, 2, 3, 4, 5].map((num) => (
                        <button
                          key={num}
                          type="button"
                          onClick={() => handleRatingChange(f.id, num)}
                          className={`py-1 rounded text-xs font-mono font-bold transition-all cursor-pointer ${
                            ratingVal === num
                              ? 'bg-cyan-500 text-slate-950 shadow-md shadow-cyan-950/50'
                              : 'bg-slate-900 text-slate-400 border border-slate-800 hover:border-slate-700 hover:text-slate-200'
                          }`}
                        >
                          {num}
                        </button>
                      ))}
                    </div>

                    <input
                      type="range"
                      min={0}
                      max={5}
                      step={1}
                      value={ratingVal}
                      onChange={(e) => handleRatingChange(f.id, Number(e.target.value))}
                      className="w-full accent-cyan-400 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
                    />
                  </div>
                  <p className="text-[10px] text-slate-500">{f.description}</p>
                </div>
              );
            })}

            {/* Exposure Rating Slider */}
            <div className="p-3 rounded-xl bg-amber-950/20 border border-amber-800/40 space-y-2 pt-3">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="font-bold text-amber-300">Exposure Rating</span>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800 font-bold">
                    Rating: {exposureRating}
                  </span>
                  <span className="text-amber-400 font-bold text-[11px]">
                    EM = {exposureMultiplier.toFixed(3)}
                  </span>
                </div>
              </div>
              <div className="grid grid-cols-6 gap-1">
                {[0, 1, 2, 3, 4, 5].map((num) => (
                  <button
                    key={num}
                    type="button"
                    onClick={() => setExposureRating(num)}
                    className={`py-1 rounded text-xs font-mono font-bold transition-all cursor-pointer ${
                      exposureRating === num
                        ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-950/50'
                        : 'bg-slate-900 text-slate-400 border border-slate-800 hover:border-slate-700 hover:text-slate-200'
                    }`}
                  >
                    {num}
                  </button>
                ))}
              </div>
              <input
                type="range"
                min={0}
                max={5}
                step={1}
                value={exposureRating}
                onChange={(e) => setExposureRating(Number(e.target.value))}
                className="w-full accent-amber-400 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
              />
              <p className="text-[10px] text-slate-400">
                Application exposure multiplier based on deployment topology and network accessibility.
              </p>
            </div>
          </div>
        </div>

        {/* Right Column: Worked Example Output Table */}
        <div className="lg:col-span-6 rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-xl space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider font-semibold">Worked Example</span>
              <h2 className="text-base font-bold font-mono text-slate-100 mt-0.5">
                Payment-Processing Microservice Evaluation
              </h2>
            </div>
            <span className="px-2.5 py-1 text-xs font-mono rounded-md bg-cyan-950 border border-cyan-800 text-cyan-300 font-bold">
              WIS = {wis.toFixed(2)}
            </span>
          </div>

          {/* Formatted Worked Example Table */}
          <div className="rounded-xl border border-slate-800 overflow-hidden bg-[#06080F]">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-900/90 text-slate-400 border-b border-slate-800 uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Factor</th>
                  <th className="py-3 px-4 text-center">Rating</th>
                  <th className="py-3 px-4 text-center">Weight</th>
                  <th className="py-3 px-4 text-right">Contribution</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {contributions.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-900/40 transition-colors">
                    <td className="py-2.5 px-4 font-semibold text-slate-200">{item.name}</td>
                    <td className="py-2.5 px-4 text-center">
                      <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-cyan-300 font-bold">
                        {item.rating}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-center text-slate-400">{item.weight.toFixed(2)}</td>
                    <td className="py-2.5 px-4 text-right font-bold text-slate-100">
                      {item.contribution.toFixed(2)}
                    </td>
                  </tr>
                ))}

                {/* Summary Rows */}
                <tr className="bg-cyan-950/30 border-t-2 border-slate-700 font-bold">
                  <td className="py-3 px-4 text-cyan-300 text-sm">WIS</td>
                  <td className="py-3 px-4 text-center"></td>
                  <td className="py-3 px-4 text-center"></td>
                  <td className="py-3 px-4 text-right text-cyan-300 text-sm font-black">
                    {wis.toFixed(2)}
                  </td>
                </tr>

                <tr className="bg-slate-900/60">
                  <td className="py-3 px-4 text-slate-300 font-medium">Exposure rating</td>
                  <td className="py-3 px-4 text-center">
                    <span className="px-2 py-0.5 rounded bg-amber-950 border border-amber-800 text-amber-300 font-bold">
                      {exposureRating}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center text-slate-500">—</td>
                  <td className="py-3 px-4 text-right text-amber-300 font-bold">
                    EM = {exposureMultiplier.toFixed(3)}
                  </td>
                </tr>

                <tr className="bg-slate-900/80">
                  <td className="py-3 px-4 text-slate-200 font-medium">Raw Score</td>
                  <td className="py-3 px-4 text-center"></td>
                  <td className="py-3 px-4 text-center"></td>
                  <td className="py-3 px-4 text-right text-purple-300 font-bold">
                    {rawScore.toFixed(3)}
                  </td>
                </tr>

                <tr className="bg-rose-950/40 border-t border-rose-800/60 font-black">
                  <td className="py-3 px-4 text-rose-300 text-sm">Normalized</td>
                  <td className="py-3 px-4 text-center"></td>
                  <td className="py-3 px-4 text-center"></td>
                  <td className="py-3 px-4 text-right text-rose-300 text-sm">
                    min(5, { (rawScore / 1.5).toFixed(2) }) = <span className="underline">{normalizedValue.toFixed(2)}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Mathematical Formula Explanation Card */}
          <div className="p-4 rounded-xl border border-slate-800 bg-[#06080F] space-y-2">
            <h3 className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
              <Info className="w-4 h-4 text-cyan-400" />
              Mathematical Formula Reference
            </h3>
            <div className="space-y-1.5 text-xs font-mono text-slate-400 leading-relaxed">
              <p>
                <strong className="text-cyan-300">1. Weighted Impact Score (WIS):</strong> WIS = Σ (Rating_i × Weight_i)
              </p>
              <p>
                <strong className="text-amber-300">2. Exposure Multiplier (EM):</strong> EM = 1.0 + (0.09375 × ExposureRating)
              </p>
              <p>
                <strong className="text-purple-300">3. Raw Score:</strong> Raw Score = WIS × EM
              </p>
              <p>
                <strong className="text-rose-300">4. Normalized Score:</strong> Normalized Score = min(5.00, Raw Score / 1.5)
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BusinessCriticality;
