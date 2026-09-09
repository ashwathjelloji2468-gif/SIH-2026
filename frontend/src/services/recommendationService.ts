import { api } from './api';
import { Recommendation } from '../types';

export interface RecommendationSummaryResponse {
  project_id: string;
  total_recommendations: number;
  total_assets: number;
  category_summary: {
    pqc_replacement_count: number;
    hybrid_count: number;
    retain_crypto_count: number;
    manual_review_count: number;
    no_action_required_count: number;
  };
  algorithm_counts: Record<string, number>;
  priority_counts: {
    CRITICAL: number;
    HIGH: number;
    MODERATE: number;
    LOW: number;
  };
  recommendations: Recommendation[];
}

export const recommendationService = {
  getAssetRecommendations: async (assetId: string): Promise<Recommendation[]> => {
    return api.get<Recommendation[]>(`/assets/${assetId}/recommendations`);
  },

  evaluateAssetRecommendation: async (assetId: string): Promise<{ asset_id: string; recommendations: Recommendation[] }> => {
    return api.post<{ asset_id: string; recommendations: Recommendation[] }>(`/assets/${assetId}/recommendations/evaluate`);
  },

  getProjectRecommendations: async (projectId: string): Promise<Recommendation[]> => {
    return api.get<Recommendation[]>(`/projects/${projectId}/recommendations`);
  },

  getProjectRecommendationSummary: async (projectId: string): Promise<RecommendationSummaryResponse> => {
    return api.get<RecommendationSummaryResponse>(`/projects/${projectId}/recommendations/summary`);
  },

  getPqcCatalog: async (): Promise<Record<string, any>> => {
    return api.get<Record<string, any>>('/knowledge/pqc');
  },

  getStandardsRegistry: async (): Promise<Record<string, any>> => {
    return api.get<Record<string, any>>('/knowledge/standards');
  },
};
