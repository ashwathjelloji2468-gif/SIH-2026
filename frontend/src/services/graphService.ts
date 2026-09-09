import { api } from './api';
import { ProjectGraph, AssetImpact, ScanGraph, BlastRadiusResult, TopBlastRadiusSummary } from '../types';

export const graphService = {
  getScanGraph: async (scanId: string): Promise<ScanGraph> => {
    return api.get<ScanGraph>(`/scans/${scanId}/graph`, { timeoutMs: 60000 });
  },

  buildScanGraph: async (scanId: string): Promise<ScanGraph> => {
    return api.post<ScanGraph>(`/scans/${scanId}/build-graph`, undefined, { timeoutMs: 90000 });
  },

  getNodeBlastRadius: async (nodeId: string, scanId?: string, maxHops: number = 3): Promise<BlastRadiusResult> => {
    const params = new URLSearchParams();
    if (scanId) params.append('scan_id', scanId);
    params.append('max_hops', maxHops.toString());
    return api.get<BlastRadiusResult>(`/nodes/${nodeId}/blast-radius?${params.toString()}`, { timeoutMs: 60000 });
  },

  getProjectTopBlastRadius: async (projectId: string): Promise<TopBlastRadiusSummary> => {
    return api.get<TopBlastRadiusSummary>(`/projects/${projectId}/blast-radius/top`, { timeoutMs: 60000 });
  },

  getGraphDownloadUrl: (scanId: string): string => {
    const baseUrl = api.getBaseUrl();
    return `${baseUrl}/scans/${scanId}/graph/download`;
  },

  // Legacy Methods
  getProjectGraph: async (projectId: string): Promise<ProjectGraph> => {
    return api.get<ProjectGraph>(`/projects/${projectId}/graph`, { timeoutMs: 60000 });
  },

  getAssetImpact: async (assetId: string): Promise<AssetImpact> => {
    return api.get<AssetImpact>(`/assets/${assetId}/impact`, { timeoutMs: 60000 });
  },

  simulateAssetImpact: async (assetId: string): Promise<AssetImpact> => {
    return api.post<AssetImpact>(`/assets/${assetId}/impact/simulate`, undefined, { timeoutMs: 60000 });
  },
};
