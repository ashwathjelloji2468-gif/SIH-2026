import { api } from './api';
import { RiskSummary, RiskAssessment, ThreatScenario } from '../types';

export const riskService = {
  getRiskSummary: async (projectId: string, options?: { skipCache?: boolean }): Promise<RiskSummary> => {
    const data = await api.get<RiskSummary>(`/projects/${projectId}/risk/summary`, options);
    if (data) return data;
    throw new Error('Risk summary unavailable');
  },

  assessProjectRisk: async (
    projectId: string,
    params?: {
      threat_scenario_id?: string;
      quantum_threat_horizon_year?: number;
      data_sensitivity_score?: number;
      business_criticality_score?: number;
      user_x_years?: number;
      user_domain?: string;
      user_y_scenario?: string;
    }
  ): Promise<RiskAssessment[]> => {
    return await api.post<RiskAssessment[]>(`/projects/${projectId}/risk/assess`, params || {}, { timeoutMs: 240000 });
  },

  getAssetRisk: async (assetId: string): Promise<RiskAssessment> => {
    return api.get<RiskAssessment>(`/assets/${assetId}/risk`);
  },

  getAssetRiskExplanation: async (assetId: string): Promise<{ asset_id: string; explanation: string }> => {
    return api.get<{ asset_id: string; explanation: string }>(`/assets/${assetId}/risk/explanation`);
  },

  listThreatScenarios: async (): Promise<ThreatScenario[]> => {
    const data = await api.get<ThreatScenario[]>('/scenarios');
    return Array.isArray(data) ? data : [];
  },

  createThreatScenario: async (scenario: Partial<ThreatScenario>): Promise<ThreatScenario> => {
    return api.post<ThreatScenario>('/scenarios', scenario);
  },

  getScenarioImpact: async (scenarioId: string): Promise<{ scenario_id: string; impact_summary: string }> => {
    return api.get<{ scenario_id: string; impact_summary: string }>(`/scenarios/${scenarioId}/impact`);
  },
};
