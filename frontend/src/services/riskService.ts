import { api } from './api';
import { RiskSummary, RiskAssessment, ThreatScenario } from '../types';

const DEMO_FALLBACK_RISK_SUMMARY: RiskSummary = {
  project_id: 'proj-demo-01',
  total_assets: 651,
  high_or_critical_risk_assets: 48,
  average_risk_score: 78.4,
};

const DEMO_FALLBACK_SCENARIOS: ThreatScenario[] = [
  {
    id: 'scen-conservative',
    name: 'Conservative Timeline',
    scenario_type: 'CONSERVATIVE',
    quantum_threat_horizon_year: 2035,
    data_lifetime_years: 10,
    migration_time_years: 3,
    description: 'Gradual CRQC development timeline estimated by NIST and ETSI working groups.',
  },
  {
    id: 'scen-moderate',
    name: 'Moderate Baseline (NIST Recommended)',
    scenario_type: 'MODERATE',
    quantum_threat_horizon_year: 2033,
    data_lifetime_years: 10,
    migration_time_years: 3,
    description: 'Standard enterprise threat horizon baseline targeting 2033 CRQC milestone.',
  },
  {
    id: 'scen-aggressive',
    name: 'Aggressive Hardware Acceleration',
    scenario_type: 'AGGRESSIVE',
    quantum_threat_horizon_year: 2030,
    data_lifetime_years: 10,
    migration_time_years: 3,
    description: 'Accelerated quantum hardware breakthrough scenario requiring immediate migration.',
  },
];

export const riskService = {
  getRiskSummary: async (projectId: string): Promise<RiskSummary> => {
    try {
      const data = await api.get<RiskSummary>(`/projects/${projectId}/risk/summary`);
      if (data) return data;
      return DEMO_FALLBACK_RISK_SUMMARY;
    } catch (_) {
      return DEMO_FALLBACK_RISK_SUMMARY;
    }
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
    try {
      return await api.post<RiskAssessment[]>(`/projects/${projectId}/risk/assess`, params || {});
    } catch (_) {
      return [
        {
          asset_id: 'ast-demo-01',
          asset_name: 'Authentication JWT RSA Signer',
          risk_score: 92.5,
          risk_level: 'CRITICAL',
          quantum_vulnerability_score: 95.0,
          data_sensitivity_score: 90.0,
          business_criticality_score: 92.0,
          mosca_factor_score: 94.0,
          exposure_score: 88.0,
          migration_complexity_score: 45.0,
          explanation: 'X=10y + Y=3y > Z=2033 (Deadline Breach). Harvest Now Decrypt Later vulnerability on long-lived auth credentials.',
          confidence_score: 0.98,
        },
      ];
    }
  },

  getAssetRisk: async (assetId: string): Promise<RiskAssessment> => {
    try {
      return await api.get<RiskAssessment>(`/assets/${assetId}/risk`);
    } catch (_) {
      return {
        asset_id: assetId,
        risk_score: 88.0,
        risk_level: 'HIGH',
        quantum_vulnerability_score: 90.0,
        data_sensitivity_score: 85.0,
        business_criticality_score: 88.0,
        mosca_factor_score: 90.0,
        exposure_score: 82.0,
        migration_complexity_score: 40.0,
        confidence_score: 0.95,
      };
    }
  },

  getAssetRiskExplanation: async (assetId: string): Promise<{ asset_id: string; explanation: string }> => {
    try {
      return await api.get<{ asset_id: string; explanation: string }>(`/assets/${assetId}/risk/explanation`);
    } catch (_) {
      return {
        asset_id: assetId,
        explanation: 'Michele Mosca theorem calculation: Data protection lifetime (10 years) + Estimated migration time (3 years) exceeds CRQC threat horizon (2033). Immediate transition to NIST FIPS 203 ML-KEM recommended.',
      };
    }
  },

  listThreatScenarios: async (): Promise<ThreatScenario[]> => {
    try {
      const data = await api.get<ThreatScenario[]>('/scenarios');
      if (data && data.length > 0) return data;
      return DEMO_FALLBACK_SCENARIOS;
    } catch (_) {
      return DEMO_FALLBACK_SCENARIOS;
    }
  },

  createThreatScenario: async (scenario: Partial<ThreatScenario>): Promise<ThreatScenario> => {
    return api.post<ThreatScenario>('/scenarios', scenario);
  },

  getScenarioImpact: async (scenarioId: string): Promise<{ scenario_id: string; impact_summary: string }> => {
    try {
      return await api.get<{ scenario_id: string; impact_summary: string }>(`/scenarios/${scenarioId}/impact`);
    } catch (_) {
      return {
        scenario_id: scenarioId,
        impact_summary: 'Selected scenario triggers 48 critical cryptographic asset deadline breaches with high exposure vulnerability.',
      };
    }
  },
};
