import { api } from './api';
import { CryptoAsset, Evidence, CoverageReport, CryptoPurpose } from '../types';

export const inventoryService = {
  getProjectInventory: async (projectId: string): Promise<CryptoAsset[]> => {
    return api.get<CryptoAsset[]>(`/projects/${projectId}/inventory`);
  },

  getProjectCoverage: async (projectId: string): Promise<CoverageReport> => {
    return api.get<CoverageReport>(`/projects/${projectId}/coverage`);
  },

  getProjectUnknowns: async (projectId: string): Promise<CryptoAsset[]> => {
    return api.get<CryptoAsset[]>(`/projects/${projectId}/unknowns`);
  },

  getAsset: async (assetId: string): Promise<CryptoAsset> => {
    return api.get<CryptoAsset>(`/assets/${assetId}`);
  },

  getAssetEvidence: async (assetId: string): Promise<Evidence[]> => {
    return api.get<Evidence[]>(`/assets/${assetId}/evidence`);
  },

  getAssetHistory: async (assetId: string): Promise<{ asset_id: string; history: any[] }> => {
    return api.get<{ asset_id: string; history: any[] }>(`/assets/${assetId}/history`);
  },

  reviewUnknownAsset: async (
    assetId: string, 
    data: { algorithm_name?: string; purpose?: CryptoPurpose; action: 'RESOLVE' | 'REJECT' }
  ): Promise<CryptoAsset> => {
    return api.post<CryptoAsset>(`/assets/${assetId}/review`, data);
  },
};
