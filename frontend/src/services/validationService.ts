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
  getValidationSummary: async (): Promise<ValidationSummary | null> => {
    try {
      return await api.get<ValidationSummary>('/validation/summary');
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
