import React, { useState, useEffect } from 'react';
import { X, Hourglass, CheckCircle2, RotateCcw, ShieldCheck } from 'lucide-react';
import { ProjectYContextResponse, YContextUpdateInput, YScenarioKey } from '../../types/yEngine';
import { MIGRATION_SCENARIOS_LIST } from '../../config/migrationScenarios';

interface YContextModalProps {
  isOpen: boolean;
  onClose: () => void;
  yContext?: ProjectYContextResponse | null;
  onSave: (input: YContextUpdateInput) => Promise<void>;
}

export const YContextModal: React.FC<YContextModalProps> = ({
  isOpen,
  onClose,
  yContext,
  onSave
}) => {
  const [selectedScenario, setSelectedScenario] = useState<YScenarioKey>(
    yContext?.user_y_scenario || yContext?.y_result?.scenario || 'STANDARD'
  );
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  useEffect(() => {
    if (yContext) {
      setSelectedScenario(yContext.user_y_scenario || yContext.y_result?.scenario || 'STANDARD');
    }
  }, [yContext, isOpen]);

  if (!isOpen) return null;

  const handleSave = async (clearOverride: boolean = false) => {
    setIsSubmitting(true);
    try {
      await onSave({
        user_y_scenario: clearOverride ? null : selectedScenario,
        clear_user_y: clearOverride
      });
      onClose();
    } catch (err) {
      console.error('Failed to update Y Context', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl relative overflow-hidden max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-blue-950/60 border border-blue-500/30 rounded-xl text-blue-400">
              <Hourglass className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">Migration Planning Scenario (Y)</h3>
              <p className="text-xs text-slate-400">
                Select a standardized migration planning assumption based on application architecture and infrastructure complexity.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Radio Options */}
        <div className="space-y-3 mt-6">
          {MIGRATION_SCENARIOS_LIST.map(scen => {
            const isSelected = selectedScenario === scen.key;
            return (
              <div
                key={scen.key}
                onClick={() => setSelectedScenario(scen.key)}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  isSelected
                    ? 'bg-blue-950/30 border-blue-500/60 shadow-lg shadow-blue-500/10'
                    : 'bg-slate-950/50 border-slate-800/80 hover:border-slate-700'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-5 h-5 rounded-full border flex items-center justify-center transition-all ${
                      isSelected ? 'border-blue-400 bg-blue-500 text-slate-950' : 'border-slate-700'
                    }`}>
                      {isSelected && <CheckCircle2 className="w-4 h-4" />}
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white flex items-center gap-2">
                        <span>{scen.title}</span>
                        {scen.key === 'STANDARD' && (
                          <span className="text-[10px] uppercase font-mono px-2 py-0.5 bg-blue-500/20 text-blue-300 rounded border border-blue-500/30">
                            MVP Default
                          </span>
                        )}
                      </h4>
                      <p className="text-xs text-slate-300 mt-1 leading-relaxed">{scen.description}</p>
                      <p className="text-[11px] text-slate-500 mt-1.5">{scen.details}</p>
                    </div>
                  </div>
                  <span className="font-mono text-lg font-extrabold text-blue-400 shrink-0 ml-3">
                    {scen.value} YRS
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between mt-8 pt-4 border-t border-slate-800">
          <button
            type="button"
            onClick={() => handleSave(true)}
            className="text-xs text-slate-400 hover:text-white flex items-center gap-1.5 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Revert to Standard Default (10y)</span>
          </button>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-semibold text-slate-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="button"
              disabled={isSubmitting}
              onClick={() => handleSave(false)}
              className="px-6 py-2.5 bg-blue-500 hover:bg-blue-400 text-slate-950 font-bold text-sm rounded-xl transition-all shadow-lg shadow-blue-500/20"
            >
              {isSubmitting ? 'Saving...' : 'Apply Scenario (Y)'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
