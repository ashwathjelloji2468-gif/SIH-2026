import { api } from './api';
import { CBOMCycloneDX } from '../types';

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
