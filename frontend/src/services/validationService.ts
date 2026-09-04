import { api } from './api';
import { ValidationRun } from '../types';

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
};
