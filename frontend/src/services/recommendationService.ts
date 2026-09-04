import { api } from './api';
import { Recommendation } from '../types';

export const recommendationService = {
  getAssetRecommendations: async (assetId: string): Promise<Recommendation[]> => {
    return api.get<Recommendation[]>(`/assets/${assetId}/recommendations`);
  },

  evaluateAssetRecommendation: async (assetId: string): Promise<{ asset_id: string; recommendations: Recommendation[] }> => {
    return api.post<{ asset_id: string; recommendations: Recommendation[] }>(`/assets/${assetId}/recommendations/evaluate`);
  },

  getPqcCatalog: async (): Promise<Record<string, any>> => {
    return api.get<Record<string, any>>('/knowledge/pqc');
  },

  getStandardsRegistry: async (): Promise<Record<string, any>> => {
    return api.get<Record<string, any>>('/knowledge/standards');
  },
};
