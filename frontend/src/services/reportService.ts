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

  getProjectCBOMDownloadUrl: (projectId: string, scanId?: string): string => {
    return scanId ? `/api/v1/projects/${projectId}/cbom/download?scan_id=${encodeURIComponent(scanId)}` : `/api/v1/projects/${projectId}/cbom/download`;
  },

  getExecutiveReportDownloadUrl: (projectId: string, scanId?: string): string => {
    return scanId ? `/api/v1/projects/${projectId}/reports/executive/download?scan_id=${encodeURIComponent(scanId)}` : `/api/v1/projects/${projectId}/reports/executive/download`;
  },

  getRiskReportDownloadUrl: (projectId: string, scanId?: string): string => {
    return scanId ? `/api/v1/projects/${projectId}/reports/risk/download?scan_id=${encodeURIComponent(scanId)}` : `/api/v1/projects/${projectId}/reports/risk/download`;
  },

  getCBOMPDFDownloadUrl: (scanId: string): string => {
    return `/api/v1/scans/${scanId}/cbom/pdf/download`;
  },

  downloadScanCBOM: async (scanId: string): Promise<void> => {
    const cbomData = await api.get<CBOMCycloneDX>(`/scans/${scanId}/cbom`);
    const jsonString = JSON.stringify(cbomData, null, 2);
    triggerFileDownload(jsonString, `cbom-${scanId}.json`, 'application/json');
  },

  downloadProjectCBOM: async (projectId: string, scanId?: string): Promise<void> => {
    const url = scanId ? `/projects/${projectId}/cbom/download?scan_id=${encodeURIComponent(scanId)}` : `/projects/${projectId}/cbom/download`;
    const cbomData = await api.get<CBOMCycloneDX>(url);
    const jsonString = JSON.stringify(cbomData, null, 2);
    triggerFileDownload(jsonString, `cbom-${scanId || projectId}.json`, 'application/json');
  },

  downloadExecutiveReport: async (projectId: string, scanId?: string): Promise<void> => {
    const url = scanId ? `/projects/${projectId}/reports/executive?scan_id=${encodeURIComponent(scanId)}` : `/projects/${projectId}/reports/executive`;
    const reportData = await api.get<Record<string, any>>(url);
    const htmlContent = reportData?.report_html;
    if (!htmlContent) {
      throw new Error("Report generation failed: No content returned from server.");
    }
    triggerFileDownload(htmlContent, `executive-report-${projectId}.html`, 'text/html');
  },

  downloadRiskReport: async (projectId: string, scanId?: string): Promise<void> => {
    const url = scanId ? `/projects/${projectId}/reports/risk?scan_id=${encodeURIComponent(scanId)}` : `/projects/${projectId}/reports/risk`;
    const reportData = await api.get<Record<string, any>>(url);
    const htmlContent = reportData?.report_html;
    if (!htmlContent) {
      throw new Error("Risk report generation failed: No content returned from server.");
    }
    triggerFileDownload(htmlContent, `risk-report-${projectId}.html`, 'text/html');
  },

  getExecutiveReport: async (projectId: string, scanId?: string): Promise<Record<string, any>> => {
    const url = scanId ? `/projects/${projectId}/reports/executive?scan_id=${encodeURIComponent(scanId)}` : `/projects/${projectId}/reports/executive`;
    return api.get<Record<string, any>>(url);
  },

  getRiskReport: async (projectId: string, scanId?: string): Promise<Record<string, any>> => {
    const url = scanId ? `/projects/${projectId}/reports/risk?scan_id=${encodeURIComponent(scanId)}` : `/projects/${projectId}/reports/risk`;
    return api.get<Record<string, any>>(url);
  },

  generateProjectReport: async (projectId: string, scanId?: string): Promise<Record<string, any>> => {
    const url = scanId ? `/projects/${projectId}/reports?scan_id=${encodeURIComponent(scanId)}` : `/projects/${projectId}/reports`;
    return api.post<Record<string, any>>(url);
  },

  getReportStatus: async (reportId: string): Promise<{ report_id: string; status: string }> => {
    return api.get<{ report_id: string; status: string }>(`/reports/${reportId}`);
  },
};
