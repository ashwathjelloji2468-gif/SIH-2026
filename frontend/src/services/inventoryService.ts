import { api } from './api';
import { CryptoAsset, Evidence, CoverageReport, CryptoPurpose } from '../types';

export const inventoryService = {
  getProjectInventory: async (projectId: string): Promise<CryptoAsset[]> => {
    const data = await api.get<CryptoAsset[]>(`/projects/${projectId}/inventory`);
    return Array.isArray(data) ? data : [];
  },

  getProjectCoverage: async (projectId: string): Promise<CoverageReport> => {
    const data = await api.get<CoverageReport>(`/projects/${projectId}/coverage`);
    if (data) return data;
    throw new Error('Coverage data unavailable');
  },

  getProjectUnknowns: async (projectId: string): Promise<CryptoAsset[]> => {
    const data = await api.get<CryptoAsset[]>(`/projects/${projectId}/unknowns`);
    return Array.isArray(data) ? data : [];
  },

  getAsset: async (assetId: string): Promise<CryptoAsset> => {
    return api.get<CryptoAsset>(`/assets/${assetId}`);
  },

  getAssetEvidence: async (assetId: string): Promise<Evidence[]> => {
    return api.get<Evidence[]>(`/assets/${assetId}/evidence`);
  },

  getAssetHistory: async (assetId: string): Promise<{ asset_id: string; history: any[] }> => {
    try {
      return await api.get<{ asset_id: string; history: any[] }>(`/assets/${assetId}/history`);
    } catch (_) {
      return { asset_id: assetId, history: [] };
    }
  },

  reviewUnknownAsset: async (
    assetId: string, 
    data: { algorithm_name?: string; purpose?: CryptoPurpose; action: 'RESOLVE' | 'REJECT' }
  ): Promise<CryptoAsset> => {
    return api.post<CryptoAsset>(`/assets/${assetId}/review`, data);
  },
};
