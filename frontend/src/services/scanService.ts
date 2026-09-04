import { api } from './api';
import { Scan, ScanCreateInput } from '../types';

export const scanService = {
  startScan: async (projectId: string, input: ScanCreateInput): Promise<Scan> => {
    return api.post<Scan>(`/projects/${projectId}/scans`, {
      target_path: input.target_path,
      scan_type: input.scan_type || 'source',
    });
  },

  getProjectScans: async (projectId: string, skip = 0, limit = 100): Promise<Scan[]> => {
    return api.get<Scan[]>(`/projects/${projectId}/scans?skip=${skip}&limit=${limit}`);
  },

  getScan: async (scanId: string): Promise<Scan> => {
    return api.get<Scan>(`/scans/${scanId}`);
  },

  cancelScan: async (scanId: string): Promise<Scan> => {
    return api.post<Scan>(`/scans/${scanId}/cancel`);
  },

  rerunScan: async (scanId: string): Promise<Scan> => {
    return api.post<Scan>(`/scans/${scanId}/rerun`);
  },
};
