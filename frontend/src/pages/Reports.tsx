import React, { useState, useEffect } from 'react';
import { useProject } from '../context/ProjectContext';
import { reportService } from '../services/reportService';
import { inventoryService } from '../services/inventoryService';
import { riskService } from '../services/riskService';
import { scanService } from '../services/scanService';
import { CBOMCycloneDX, CryptoAsset, RiskSummary, Scan } from '../types';
import { CBOMViewer } from '../components/Reports/CBOMViewer';
import { PDFReportPreview } from '../components/Reports/PDFReportPreview';
import { PQCCatalogModal } from '../components/Recommendations/PQCCatalogModal';
import { FileSpreadsheet, FileText, BookOpen, RefreshCw } from 'lucide-react';

export const Reports: React.FC = () => {
  const { currentProject, latestScan } = useProject();
  const [activeTab, setActiveTab] = useState<'cbom' | 'pdf'>('cbom');
  const [cbom, setCbom] = useState<CBOMCycloneDX | null>(null);
  const [assets, setAssets] = useState<CryptoAsset[]>([]);
  const [riskSummary, setRiskSummary] = useState<RiskSummary | null>(null);
  const [scans, setScans] = useState<Scan[]>([]);
  const [selectedScanId, setSelectedScanId] = useState<string>('');
  const [pqcModalOpen, setPqcModalOpen] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchReportsData = async () => {
    if (!currentProject) {
      setCbom(null);
      setAssets([]);
      setRiskSummary(null);
      setScans([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const [scansData, invData, riskData] = await Promise.allSettled([
        scanService.getProjectScans(currentProject.id),
        inventoryService.getProjectInventory(currentProject.id),
        riskService.getRiskSummary(currentProject.id),
      ]);

      const loadedScans = scansData.status === 'fulfilled' ? scansData.value : [];
      setScans(loadedScans);
      if (invData.status === 'fulfilled') setAssets(invData.value || []);
      if (riskData.status === 'fulfilled') setRiskSummary(riskData.value || null);

      const targetScan = loadedScans[0];
      if (targetScan) {
        setSelectedScanId(targetScan.id);
        try {
          const cbomData = await reportService.getScanCBOM(targetScan.id);
          setCbom(cbomData);
        } catch (err) {
          console.warn('Could not load CBOM for scan:', err);
          setCbom(null);
        }
      } else {
        setCbom(null);
      }
    } catch (err) {
      console.error('Failed to load reports:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReportsData();
  }, [currentProject]);

  const handleScanChange = async (scanId: string) => {
    setSelectedScanId(scanId);
    try {
      const cbomData = await reportService.getScanCBOM(scanId);
      setCbom(cbomData);
    } catch {
      setCbom(null);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider font-semibold mb-1">
            <FileSpreadsheet className="w-4 h-4" />
            <span>Compliance & Artifacts</span>
          </div>
          <h1 className="text-2xl font-bold font-mono text-slate-100">Cryptographic BOM & Executive Reports</h1>
          <p className="text-xs text-slate-400 mt-1">
            CycloneDX 1.6 standard exports, formal verification audits, and printable executive summaries.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setPqcModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl border border-slate-800 bg-slate-900/80 hover:bg-slate-800 text-slate-300 text-xs font-medium transition-colors cursor-pointer"
          >
            <BookOpen className="w-4 h-4 text-cyan-400" />
            <span>NIST Standards Catalog</span>
          </button>

          <button
            onClick={fetchReportsData}
            className="p-2 rounded-xl border border-slate-800 hover:bg-slate-900 text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
            title="Refresh reports"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center justify-between border-b border-slate-800">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setActiveTab('cbom')}
            className={`pb-3 px-1 text-xs font-mono font-semibold transition-colors relative cursor-pointer flex items-center gap-2 ${
              activeTab === 'cbom'
                ? 'text-cyan-300 border-b-2 border-cyan-400'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileSpreadsheet className="w-4 h-4" />
            <span>CycloneDX 1.6 CBOM</span>
          </button>

          <button
            onClick={() => setActiveTab('pdf')}
            className={`pb-3 px-1 text-xs font-mono font-semibold transition-colors relative cursor-pointer flex items-center gap-2 ${
              activeTab === 'pdf'
                ? 'text-cyan-300 border-b-2 border-cyan-400'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Executive Assessment Report</span>
          </button>
        </div>

        {activeTab === 'cbom' && scans.length > 0 && (
          <div className="flex items-center gap-2 text-xs font-mono pb-2">
            <span className="text-slate-500 hidden sm:inline">Scan:</span>
            <select
              value={selectedScanId}
              onChange={(e) => handleScanChange(e.target.value)}
              className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 text-xs focus:outline-none focus:border-cyan-500 cursor-pointer"
            >
              {scans.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.id.slice(0, 8)} ({s.status}) - {new Date(s.created_at).toLocaleDateString()}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Tab Contents */}
      {activeTab === 'cbom' ? (
        <CBOMViewer scanId={selectedScanId} cbom={cbom} />
      ) : (
        <PDFReportPreview assets={assets} riskSummary={riskSummary} />
      )}

      {/* NIST Standards Modal */}
      <PQCCatalogModal
        isOpen={pqcModalOpen}
        onClose={() => setPqcModalOpen(false)}
      />
    </div>
  );
};
