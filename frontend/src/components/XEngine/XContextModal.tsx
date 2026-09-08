import React, { useState, useEffect } from 'react';
import { X, Clock, Building2, Sliders, CheckCircle2, RotateCcw, FolderPlus, Trash2 } from 'lucide-react';
import { ProjectXContextResponse, XContextUpdateInput } from '../../types/xEngine';
import { DOMAIN_BASELINES_LIST, getDomainBaselineByKey } from '../../config/domainBaselines';

interface XContextModalProps {
  isOpen: boolean;
  onClose: () => void;
  xContext?: ProjectXContextResponse | null;
  onSave: (input: XContextUpdateInput) => Promise<void>;
}

export const XContextModal: React.FC<XContextModalProps> = ({
  isOpen,
  onClose,
  xContext,
  onSave
}) => {
  const [selectedX, setSelectedX] = useState<number | null>(xContext?.user_x_years ?? null);
  const [customXInput, setCustomXInput] = useState<string>(xContext?.user_x_years ? String(xContext.user_x_years) : '');
  const [selectedDomain, setSelectedDomain] = useState<string>(xContext?.user_domain || xContext?.x_result?.domain || '');
  const [folderPath, setFolderPath] = useState<string>('');
  const [folderX, setFolderX] = useState<string>('10');
  const [folderNotes, setFolderNotes] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  useEffect(() => {
    if (xContext) {
      setSelectedX(xContext.user_x_years ?? null);
      setCustomXInput(xContext.user_x_years ? String(xContext.user_x_years) : '');
      setSelectedDomain(xContext.user_domain || xContext.x_result?.domain || '');
    }
  }, [xContext, isOpen]);

  if (!isOpen) return null;

  const presetValues = [5, 10, 15, 20, 30, 50];

  const handleSelectPreset = (years: number) => {
    setSelectedX(years);
    setCustomXInput(String(years));
  };

  const handleSave = async (clearOverride: boolean = false) => {
    setIsSubmitting(true);
    try {
      let finalUserX: number | null = null;
      if (!clearOverride && selectedX !== null) {
        finalUserX = selectedX;
      }

      let fPath: string | null = null;
      let fX: number | null = null;
      let fNotes: string | null = null;

      if (folderPath.trim()) {
        fPath = folderPath.trim();
        fX = parseInt(folderX, 10) || 10;
        fNotes = folderNotes.trim() || 'Folder context adjustment';
      }

      await onSave({
        user_x_years: finalUserX,
        user_domain: selectedDomain || null,
        folder_path: fPath,
        folder_x_years: fX,
        folder_notes: fNotes,
        clear_user_x: clearOverride
      });

      onClose();
    } catch (err) {
      console.error('Failed to update X Context', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const domainBaselineInfo = selectedDomain ? getDomainBaselineByKey(selectedDomain) : null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl relative overflow-hidden max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-cyan-950/60 border border-cyan-500/30 rounded-xl text-cyan-400">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">Adjust Confidentiality Horizon (X)</h3>
              <p className="text-xs text-slate-400">
                Set organizational requirement or industry domain baseline for data confidentiality protection.
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

        {/* Form Body */}
        <div className="space-y-6 mt-6">
          {/* Preset Buttons */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Select Confidentiality Horizon (Years)
            </label>
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
              {presetValues.map(v => (
                <button
                  key={v}
                  type="button"
                  onClick={() => handleSelectPreset(v)}
                  className={`py-2.5 px-3 rounded-lg border font-mono font-bold text-sm transition-all flex flex-col items-center justify-center ${
                    selectedX === v
                      ? 'bg-cyan-500/20 border-cyan-500 text-cyan-300 shadow-lg shadow-cyan-500/10'
                      : 'bg-slate-950/50 border-slate-800 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <span>{v}y</span>
                </button>
              ))}
            </div>
          </div>

          {/* Custom Input */}
          <div className="flex items-center gap-3">
            <div className="flex-1">
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Custom Years Input
              </label>
              <input
                type="number"
                min="1"
                max="100"
                value={customXInput}
                onChange={e => {
                  setCustomXInput(e.target.value);
                  const val = parseInt(e.target.value, 10);
                  setSelectedX(isNaN(val) ? null : val);
                }}
                placeholder="e.g. 15"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white font-mono text-sm focus:border-cyan-500/50 outline-none"
              />
            </div>
            {selectedX !== null && (
              <button
                type="button"
                onClick={() => handleSave(true)}
                title="Revert to system/domain estimate"
                className="mt-5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Revert to System Estimate</span>
              </button>
            )}
          </div>

          {/* Industry Domain Selection */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Building2 className="w-4 h-4 text-cyan-400" />
              <span>Industry / Domain Baseline</span>
            </label>
            <select
              value={selectedDomain}
              onChange={e => setSelectedDomain(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2.5 text-white text-sm focus:border-cyan-500/50 outline-none"
            >
              <option value="">-- Unclassified / Auto-Detect --</option>
              {DOMAIN_BASELINES_LIST.map(b => (
                <option key={b.key} value={b.key}>
                  {b.title} ({b.baseline_x_years} Years Baseline)
                </option>
              ))}
            </select>
            {domainBaselineInfo && (
              <div className="mt-2 p-3 bg-slate-950/60 border border-slate-800 rounded-lg text-xs text-slate-400">
                <span className="font-semibold text-emerald-400">{domainBaselineInfo.title}:</span> {domainBaselineInfo.description} (Compliance: {domainBaselineInfo.compliance_references.join(', ')})
              </div>
            )}
          </div>

          {/* Folder-level Context Adjustment */}
          <div className="pt-4 border-t border-slate-800">
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <FolderPlus className="w-4 h-4 text-cyan-400" />
              <span>Add Folder / Module Context Override</span>
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              <input
                type="text"
                placeholder="Folder path (e.g. services/payment)"
                value={folderPath}
                onChange={e => setFolderPath(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white font-mono text-xs focus:border-cyan-500/50 outline-none"
              />
              <input
                type="number"
                min="1"
                placeholder="Years (e.g. 10)"
                value={folderX}
                onChange={e => setFolderX(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white font-mono text-xs focus:border-cyan-500/50 outline-none"
              />
              <input
                type="text"
                placeholder="Notes (e.g. PCI-DSS scope)"
                value={folderNotes}
                onChange={e => setFolderNotes(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white text-xs focus:border-cyan-500/50 outline-none"
              />
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-end gap-3 mt-8 pt-4 border-t border-slate-800">
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
            className="px-6 py-2.5 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-sm rounded-xl transition-all shadow-lg shadow-cyan-500/20"
          >
            {isSubmitting ? 'Saving...' : 'Apply X Context'}
          </button>
        </div>
      </div>
    </div>
  );
};
