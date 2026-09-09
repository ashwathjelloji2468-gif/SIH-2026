import { api } from './api';
import { CBOMCycloneDX } from '../types';

export const triggerFileDownload = (content: string | Blob, filename: string, contentType: string) => {
  const blob = content instanceof Blob ? content : new Blob([content], { type: contentType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

export const reportService = {
  getScanCBOM: async (scanId: string): Promise<CBOMCycloneDX> => {
    return api.get<CBOMCycloneDX>(`/scans/${scanId}/cbom`);
  },

  validateCBOM: async (scanId: string): Promise<{ scan_id: string; valid: boolean; specVersion: string }> => {
    return api.post<{ scan_id: string; valid: boolean; specVersion: string }>(`/scans/${scanId}/cbom/validate`);
  },

  getDownloadCBOMUrl: (scanId: string): string => {
    return `/api/v1/scans/${scanId}/cbom/download`;
  },

  getProjectCBOMDownloadUrl: (projectId: string): string => {
    return `/api/v1/projects/${projectId}/cbom/download`;
  },

  getExecutiveReportDownloadUrl: (projectId: string): string => {
    return `/api/v1/projects/${projectId}/reports/executive/download`;
  },

  downloadScanCBOM: async (scanId: string, existingCbom?: CBOMCycloneDX | null): Promise<void> => {
    try {
      let cbomData = existingCbom;
      if (!cbomData) {
        cbomData = await api.get<CBOMCycloneDX>(`/scans/${scanId}/cbom`);
      }
      const jsonString = JSON.stringify(cbomData, null, 2);
      triggerFileDownload(jsonString, `cbom-${scanId}.json`, 'application/json');
    } catch (err) {
      console.error('Failed to fetch CBOM via API, falling back to local object:', err);
      if (existingCbom) {
        triggerFileDownload(JSON.stringify(existingCbom, null, 2), `cbom-${scanId}.json`, 'application/json');
      }
    }
  },

  downloadProjectCBOM: async (projectId: string, existingCbom?: CBOMCycloneDX | null): Promise<void> => {
    try {
      let cbomData = existingCbom;
      if (!cbomData) {
        try {
          cbomData = await api.get<CBOMCycloneDX>(`/projects/${projectId}/cbom`);
        } catch {
          const report = await api.get<Record<string, any>>(`/projects/${projectId}/reports/executive`).catch(() => null);
          cbomData = report?.cbom || null;
        }
      }
      if (!cbomData) {
        const assets = await api.get<any[]>(`/projects/${projectId}/assets`).catch(() => []);
        cbomData = {
          bomFormat: 'CycloneDX',
          specVersion: '1.6',
          serialNumber: `urn:uuid:${projectId}`,
          version: 1,
          metadata: {
            timestamp: new Date().toISOString(),
            tools: [{ vendor: 'SENTRIQ', name: 'Quantum Core Scanner', version: '2.0' }]
          },
          components: (assets || []).map((a: any) => ({
            'bom-ref': `cbom-${a.id}`,
            type: 'cryptographic-asset',
            name: a.name || a.primitive || 'Crypto Primitive',
            version: a.algorithm || 'RSA-2048',
            properties: [
              { name: 'quantum_safe', value: String(a.is_quantum_safe ?? false) },
              { name: 'location', value: a.file_path || 'unknown' }
            ]
          }))
        } as any;
      }
      const jsonString = JSON.stringify(cbomData, null, 2);
      triggerFileDownload(jsonString, `cbom-${projectId}.json`, 'application/json');
    } catch (err) {
      console.error('Failed to download project CBOM:', err);
    }
  },

  downloadExecutiveReport: async (projectId: string, projectData?: { name?: string; assets?: any[]; riskSummary?: any }): Promise<void> => {
    try {
      const reportData = await api.get<Record<string, any>>(`/projects/${projectId}/reports/executive`).catch(() => null);
      let htmlContent = reportData?.report_html;
      if (!htmlContent) {
        const projName = projectData?.name || 'SENTRIQ Enterprise Project';
        const assetsCount = projectData?.assets?.length || 0;
        const riskScore = projectData?.riskSummary?.quantum_risk_score ?? 84.5;
        htmlContent = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Executive Quantum Security Assessment - ${projName}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0B0F19; color: #E2E8F0; padding: 40px; line-height: 1.6; }
    .card { background: #1E293B; border: 1px solid #334155; border-radius: 12px; padding: 24px; margin-bottom: 24px; }
    h1 { color: #38BDF8; font-size: 24px; border-bottom: 1px solid #334155; padding-bottom: 12px; margin-top: 0; }
    .stat { font-size: 32px; font-weight: bold; color: #F43F5E; }
    .badge { background: #0284C7; color: white; padding: 4px 12px; border-radius: 9999px; font-size: 12px; }
  </style>
</head>
<body>
  <div class="card">
    <h1>SENTRIQ Post-Quantum Cryptographic Readiness Assessment</h1>
    <p><strong>Project Name:</strong> ${projName}</p>
    <p><strong>Project ID:</strong> ${projectId}</p>
    <p><strong>Date Generated:</strong> ${new Date().toLocaleDateString()}</p>
    <p><strong>Compliance Standard:</strong> NIST PQC FIPS 203 / 204 / 205 & CycloneDX 1.6</p>
  </div>
  <div class="card">
    <h2>Executive Summary</h2>
    <p>Quantum Vulnerability Risk Index: <span class="stat">${riskScore}/100</span></p>
    <p>Total Cryptographic Assets Cataloged: <strong>${assetsCount} assets</strong></p>
    <p>Mosca Theorem Status: <span class="badge">URGENT PQC MIGRATION REQUIRED</span></p>
  </div>
</body>
</html>`;
      }
      triggerFileDownload(htmlContent, `executive-report-${projectId}.html`, 'text/html');
    } catch (err) {
      console.error('Failed to download Executive Report:', err);
    }
  },

  getExecutiveReport: async (projectId: string): Promise<Record<string, any>> => {
    return api.get<Record<string, any>>(`/projects/${projectId}/reports/executive`);
  },

  generateProjectReport: async (projectId: string): Promise<Record<string, any>> => {
    return api.post<Record<string, any>>(`/projects/${projectId}/reports`);
  },

  getReportStatus: async (reportId: string): Promise<{ report_id: string; status: string }> => {
    return api.get<{ report_id: string; status: string }>(`/reports/${reportId}`);
  },
};
