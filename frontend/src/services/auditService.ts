import { api } from './api';
import { AuditEvent, HealthResponse } from '../types';

export const auditService = {
  getSystemHealth: async (): Promise<HealthResponse> => {
    return api.get<HealthResponse>('/health');
  },

  getProjectAuditTrail: async (projectId: string, skip = 0, limit = 100): Promise<AuditEvent[]> => {
    return api.get<AuditEvent[]>(`/projects/${projectId}/audit?skip=${skip}&limit=${limit}`);
  },
};
