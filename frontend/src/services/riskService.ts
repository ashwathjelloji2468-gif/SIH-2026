import { api } from './api';
import { RiskSummary, RiskAssessment, ThreatScenario } from '../types';

export const riskService = {
  getRiskSummary: async (projectId: string): Promise<RiskSummary> => {
    return api.get<RiskSummary>(`/projects/${projectId}/risk/summary`);
  },

  assessProjectRisk: async (
    projectId: string,
    params?: {
      threat_scenario_id?: string;
      quantum_threat_horizon_year?: number;
      data_sensitivity_score?: number;
      business_criticality_score?: number;
    }
  ): Promise<RiskAssessment[]> => {
    return api.post<RiskAssessment[]>(`/projects/${projectId}/risk/assess`, params || {});
  },

  getAssetRisk: async (assetId: string): Promise<RiskAssessment> => {
    return api.get<RiskAssessment>(`/assets/${assetId}/risk`);
  },

  getAssetRiskExplanation: async (assetId: string): Promise<{ asset_id: string; explanation: string }> => {
    return api.get<{ asset_id: string; explanation: string }>(`/assets/${assetId}/risk/explanation`);
  },

  listThreatScenarios: async (): Promise<ThreatScenario[]> => {
    return api.get<ThreatScenario[]>('/scenarios');
  },

  createThreatScenario: async (scenario: Partial<ThreatScenario>): Promise<ThreatScenario> => {
    return api.post<ThreatScenario>('/scenarios', scenario);
  },

  getScenarioImpact: async (scenarioId: string): Promise<{ scenario_id: string; impact_summary: string }> => {
    return api.get<{ scenario_id: string; impact_summary: string }>(`/scenarios/${scenarioId}/impact`);
  },
};
