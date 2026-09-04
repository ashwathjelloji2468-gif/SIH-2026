import React from 'react';
import { Evidence } from '../../types';
import { CodeSnippet } from '../Common/CodeSnippet';
import { ConfidenceBadge } from '../Common/ConfidenceBadge';
import { StatusBadge } from '../Common/StatusBadge';
import { ShieldCheck, Info } from 'lucide-react';

interface EvidenceViewerProps {
  evidence: Evidence[];
}

export const EvidenceViewer: React.FC<EvidenceViewerProps> = ({ evidence }) => {
  if (!evidence || evidence.length === 0) {
    return (
      <div className="rounded-lg border border-slate-800 bg-slate-900/30 p-4 text-center text-xs text-slate-500">
        No cryptographic evidence records attached.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {evidence.map((item) => (
        <div
          key={item.id}
          className="rounded-xl border border-slate-800 bg-slate-900/50 p-4 space-y-3"
        >
          {/* Metadata header */}
          <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
            <div className="flex items-center gap-2">
              <StatusBadge type="evidence" value={item.evidence_type} />
              <span className="font-mono text-slate-300 font-medium truncate max-w-[200px] sm:max-w-xs">
                {item.source_file}
              </span>
              {item.line_number && (
                <span className="text-slate-500 font-mono">L:{item.line_number}</span>
              )}
            </div>
            <div className="flex items-center gap-3">
              <ConfidenceBadge score={item.confidence_score} />
              <span className="text-[11px] text-slate-500 font-mono">
                {new Date(item.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>

          {/* Code Snippet Viewer */}
          <CodeSnippet
            sourceFile={item.source_file}
            lineNumber={item.line_number}
            excerpt={item.excerpt}
            detectorName={item.detector_name}
            detectorVersion={item.detector_version}
          />

          {/* Provenance breakdown */}
          {item.provenance && Object.keys(item.provenance).length > 0 && (
            <div className="rounded-lg bg-[#070A12] border border-slate-800/80 p-3 text-[11px] font-mono text-slate-400 space-y-1">
              <div className="text-slate-300 font-semibold flex items-center gap-1.5 mb-1">
                <Info className="w-3.5 h-3.5 text-cyan-400" />
                <span>Detection Provenance</span>
              </div>
              {Object.entries(item.provenance).map(([k, v]) => (
                <div key={k} className="flex items-baseline justify-between border-b border-slate-900 pb-0.5">
                  <span className="text-slate-500">{k}:</span>
                  <span className="text-slate-300 text-right truncate max-w-xs">
                    {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};
