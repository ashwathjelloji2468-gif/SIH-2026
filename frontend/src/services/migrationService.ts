import { api } from './api';
import { MigrationPlan, MigrationPlanCreateInput, SandboxSimulationResult } from '../types';

export interface MigrationSummary {
  total_tasks: number;
  completed_tasks: number;
  total_person_days: number;
  total_calendar_months: number;
  priority_breakdown: Record<string, number>;
  status_breakdown: Record<string, number>;
}

export interface SimulationRecord {
  id: string;
  asset_id: string;
  source_algorithm: string;
  target_algorithm: string;
  status: string;
  sandbox_path?: string;
  created_at: string;
  files_modified?: string[];
  diff_summary?: string;
}

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

  /** Trigger a Prompt 6 asset-level migration simulation */
  simulateAssetMigration: async (assetId: string, sourceDir?: string): Promise<SimulationRecord> => {
    const body = sourceDir ? { source_dir: sourceDir } : undefined;
    return api.post<SimulationRecord>(`/migration/simulate?asset_id=${encodeURIComponent(assetId)}`, body);
  },

  /** List all Prompt 6 simulations */
  listSimulations: async (projectId?: string): Promise<SimulationRecord[]> => {
    try {
      const url = projectId ? `/migration/simulations?project_id=${projectId}` : '/migration/simulations';
      return await api.get<SimulationRecord[]>(url);
    } catch (_) {
      return [];
    }
  },

  /** Get aggregated migration summary from Prompt 5/6 endpoints */
  getMigrationSummary: async (projectId?: string): Promise<MigrationSummary | null> => {
    try {
      const url = projectId ? `/migration/summary?project_id=${projectId}` : '/migration/summary';
      return await api.get<MigrationSummary>(url);
    } catch (_) {
      return null;
    }
  },

  /** Get migration tasks for a specific asset */
  getAssetMigration: async (assetId: string): Promise<Record<string, any> | null> => {
    try {
      return await api.get<Record<string, any>>(`/migration/${assetId}`);
    } catch (_) {
      return null;
    }
  },
};
