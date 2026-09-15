import { api } from './api';

export interface ProjectBusinessCriticality {
  project_id: string;
  project_name: string;
  system_criticality: string;
  user_override: string | null;
  effective_criticality: string;
  adjustment_reason: string | null;
  is_overridden: boolean;
  factor_ratings: Record<string, number>;
  scores: {
    wis: number;
    exposure_multiplier: number;
    raw_score: number;
    normalized_score: number;
    calculated_label: string;
  };
  assets_summary: Array<{
    asset_id: string;
    asset_name: string;
    algorithm_name: string;
    system_criticality: string;
    effective_planning_criticality: string;
    adjustment_reason: string | null;
    is_overridden: boolean;
  }>;
  updated_at: string | null;
}

export const businessCriticalityService = {
  getProjectBusinessCriticality: async (projectId: string): Promise<ProjectBusinessCriticality> => {
    return api.get<ProjectBusinessCriticality>(`/projects/${projectId}/business-criticality`);
  },

  updateProjectBusinessCriticality: async (
    projectId: string,
    payload: {
      factor_ratings?: Record<string, number>;
      user_override?: string | null;
      adjustment_reason?: string | null;
      revert_override?: boolean;
    }
  ): Promise<ProjectBusinessCriticality> => {
    return api.put<ProjectBusinessCriticality>(`/projects/${projectId}/business-criticality`, payload);
  },

  overrideBusinessCriticality: async (
    projectId: string,
    overrideValue: string,
    reason: string
  ): Promise<ProjectBusinessCriticality> => {
    return api.post<ProjectBusinessCriticality>(`/projects/${projectId}/business-criticality/override`, {
      user_override: overrideValue,
      adjustment_reason: reason,
    });
  },

  revertBusinessCriticality: async (projectId: string): Promise<ProjectBusinessCriticality> => {
    return api.post<ProjectBusinessCriticality>(`/projects/${projectId}/business-criticality/revert`);
  },
};
