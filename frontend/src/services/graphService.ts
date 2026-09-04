import { api } from './api';
import { ProjectGraph, AssetImpact } from '../types';

export const graphService = {
  getProjectGraph: async (projectId: string): Promise<ProjectGraph> => {
    return api.get<ProjectGraph>(`/projects/${projectId}/graph`);
  },

  getAssetImpact: async (assetId: string): Promise<AssetImpact> => {
    return api.get<AssetImpact>(`/assets/${assetId}/impact`);
  },

  simulateAssetImpact: async (assetId: string): Promise<AssetImpact> => {
    return api.post<AssetImpact>(`/assets/${assetId}/impact/simulate`);
  },
};
