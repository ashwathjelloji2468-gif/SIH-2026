import { api } from './api';
import { ValidationRun } from '../types';

export interface ValidationSummary {
  total_validations: number;
  passed: number;
  failed: number;
  error: number;
  in_progress: number;
  average_confidence: number;
  average_residual_risk: number;
}

export const validationService = {
  /** Execute real build validation for a project/repository */
  runBuildValidation: async (projectId: string, scanId?: string): Promise<ValidationRun> => {
    const url = scanId ? `/projects/${projectId}/validation/build?scan_id=${scanId}` : `/projects/${projectId}/validation/build`;
    return api.post<ValidationRun>(url);
  },

  /** Execute real unit-test validation for a project/repository */
  runTestValidation: async (projectId: string, scanId?: string): Promise<ValidationRun> => {
    const url = scanId ? `/projects/${projectId}/validation/tests?scan_id=${scanId}` : `/projects/${projectId}/validation/tests`;
    return api.post<ValidationRun>(url);
  },

  /** Execute Before/After Regression Validation for a project/repository */
  runRegressionValidation: async (
    projectId: string,
    params?: { scanId?: string; simulationId?: string; planId?: string }
  ): Promise<any> => {
    const searchParams = new URLSearchParams();
    if (params?.scanId) searchParams.append('scan_id', params.scanId);
    if (params?.simulationId) searchParams.append('simulation_id', params.simulationId);
    if (params?.planId) searchParams.append('migration_plan_id', params.planId);

    const queryStr = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return api.post<any>(`/projects/${projectId}/validation/regression${queryStr}`);
  },

  /** Execute Before/After CBOM Comparison Validation for a project/repository (Task #8) */
  runCBOMDiffValidation: async (
    projectId: string,
    params?: { scanId?: string; simulationId?: string; planId?: string }
  ): Promise<any> => {
    const searchParams = new URLSearchParams();
    if (params?.scanId) searchParams.append('scan_id', params.scanId);
    if (params?.simulationId) searchParams.append('simulation_id', params.simulationId);
    if (params?.planId) searchParams.append('migration_plan_id', params.planId);

    const queryStr = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return api.post<any>(`/projects/${projectId}/validation/cbom-diff${queryStr}`);
  },


  runValidation: async (planId: string): Promise<ValidationRun> => {
    return api.post<ValidationRun>(`/migration/plans/${planId}/validate`);
  },

  getValidationRun: async (validationId: string): Promise<ValidationRun> => {
    return api.get<ValidationRun>(`/validation/${validationId}`);
  },

  getValidationLogs: async (validationId: string): Promise<{ validation_id: string; logs: string }> => {
    return api.get<{ validation_id: string; logs: string }>(`/validation/${validationId}/logs`);
  },

  /** Validate a Prompt 6 simulation run */
  validateSimulation: async (simulationId: string): Promise<Record<string, any>> => {
    return api.post<Record<string, any>>(`/migration/simulations/${simulationId}/validate`);
  },

  /** Get aggregated validation summary across all runs */
  getValidationSummary: async (projectId?: string): Promise<ValidationSummary | null> => {
    try {
      const url = projectId ? `/validation/summary?project_id=${projectId}` : '/validation/summary';
      return await api.get<ValidationSummary>(url);
    } catch (_) {
      return null;
    }
  },

  /** Get validation for a specific simulation */
  getSimulationValidation: async (simulationId: string): Promise<Record<string, any> | null> => {
    try {
      return await api.get<Record<string, any>>(`/validation/simulation/${simulationId}`);
    } catch (_) {
      return null;
    }
  },
};
