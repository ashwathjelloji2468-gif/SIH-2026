import { api } from './api';
import { MigrationPlan, MigrationPlanCreateInput, SandboxSimulationResult } from '../types';

export const migrationService = {
  createPlan: async (projectId: string, input: MigrationPlanCreateInput): Promise<MigrationPlan> => {
    return api.post<MigrationPlan>(`/projects/${projectId}/migration/plans`, input);
  },

  listPlans: async (projectId: string): Promise<MigrationPlan[]> => {
    return api.get<MigrationPlan[]>(`/projects/${projectId}/migration/plans`);
  },

  getPlan: async (planId: string): Promise<MigrationPlan> => {
    return api.get<MigrationPlan>(`/migration/plans/${planId}`);
  },

  recalculatePlan: async (planId: string): Promise<MigrationPlan> => {
    return api.post<MigrationPlan>(`/migration/plans/${planId}/recalculate`);
  },

  simulateTransformation: async (planId: string, pattern = 'RSA_TO_ML_KEM_HYBRID'): Promise<SandboxSimulationResult> => {
    return api.post<SandboxSimulationResult>(`/migration/plans/${planId}/simulate?pattern=${encodeURIComponent(pattern)}`);
  },
};
