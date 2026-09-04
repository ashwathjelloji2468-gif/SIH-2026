import React, { useState } from 'react';
import { Copy, Check, FileCode } from 'lucide-react';

interface CodeSnippetProps {
  sourceFile: string;
  lineNumber?: number | null;
  excerpt?: string | null;
  detectorName?: string;
  detectorVersion?: string;
}

export const CodeSnippet: React.FC<CodeSnippetProps> = ({
  sourceFile,
  lineNumber,
  excerpt,
  detectorName,
  detectorVersion,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (excerpt) {
      navigator.clipboard.writeText(excerpt);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const lines = excerpt ? excerpt.split('\n') : [];
  const startLine = lineNumber ? Math.max(1, lineNumber - Math.floor(lines.length / 2)) : 1;

  return (
    <div className="rounded-lg border border-slate-800 bg-[#0B0F19] overflow-hidden">
      {/* Header bar */}
      <div className="flex items-center justify-between px-3 py-2 bg-slate-900/80 border-b border-slate-800 text-xs text-slate-400">
        <div className="flex items-center gap-2 font-mono truncate">
          <FileCode className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
          <span className="text-slate-200 truncate">{sourceFile}</span>
          {lineNumber && (
            <span className="text-cyan-400 font-semibold bg-cyan-950/60 px-1.5 py-0.5 rounded border border-cyan-800/40">
              Line {lineNumber}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3 shrink-0">
          {detectorName && (
            <span className="text-[11px] text-slate-500 font-mono hidden md:inline">
              Detector: <span className="text-slate-300">{detectorName}</span>
              {detectorVersion && ` v${detectorVersion}`}
            </span>
          )}
          {excerpt && (
            <button
              onClick={handleCopy}
              className="flex items-center gap-1 text-slate-400 hover:text-cyan-300 transition-colors cursor-pointer"
              title="Copy snippet"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Code Viewer */}
      <div className="p-3 overflow-x-auto text-xs font-mono text-slate-200">
        {lines.length > 0 ? (
          <table className="w-full border-collapse">
            <tbody>
              {lines.map((line, idx) => {
                const currentLineNum = startLine + idx;
                const isTargetLine = lineNumber ? currentLineNum === lineNumber : false;
                return (
                  <tr
                    key={idx}
                    className={isTargetLine ? 'bg-cyan-950/40 text-cyan-200 font-semibold' : 'hover:bg-slate-900/30'}
                  >
                    <td className="pr-4 select-none text-slate-600 text-right w-10 font-mono text-[11px]">
                      {currentLineNum}
                    </td>
                    <td className="whitespace-pre pl-2 border-l border-slate-800/60">
                      {line || ' '}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <div className="text-slate-500 italic py-2 text-center">
            No code excerpt available for this finding.
          </div>
        )}
      </div>
    </div>
  );
};
