import { api } from './api';
import type { QARSProjectResult, QARSAssetResponseWrapper, QARSAssetResult } from '../types';

export const qarsService = {
  /**
   * Fetches project-level QARS aggregate summary metrics and asset list.
   * Path: /projects/{projectId}/qars
   */
  getProjectQARS: async (projectId: string): Promise<QARSProjectResult> => {
    return api.get<QARSProjectResult>(`/projects/${projectId}/qars`);
  },

  /**
   * Fetches artifact-level QARS evaluation for a specific asset within a project.
   * Path: /projects/{projectId}/qars/assets/{assetId}
   */
  getAssetQARS: async (projectId: string, assetId: string): Promise<QARSAssetResult> => {
    const res = await api.get<QARSAssetResponseWrapper>(`/projects/${projectId}/qars/assets/${assetId}`);
    return res.data;
  },
};
