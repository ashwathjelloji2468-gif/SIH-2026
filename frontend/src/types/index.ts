// SENTRIQ Types Definition matching Backend FastAPI /api/v1 Schemas

export type ScanStatus = 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';

export type AssetType = 'ALGORITHM' | 'PROTOCOL' | 'CERTIFICATE' | 'KEY' | 'LIBRARY' | 'UNKNOWN';

export type CryptoPurpose = 
  | 'ENCRYPTION'
  | 'SIGNATURE'
  | 'KEY_ESTABLISHMENT'
  | 'HASHING'
  | 'AUTHENTICATION'
  | 'UNKNOWN';

export type QuantumSafety = 'SAFE' | 'VULNERABLE' | 'TRANSITIONAL' | 'UNKNOWN';

export type RiskLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'NEGLIGIBLE';

export type EvidenceType = 'OBSERVED' | 'INFERRED' | 'DEPENDENCY' | 'CONFIGURATION';

export type ReviewStatus = 'PENDING' | 'RESOLVED' | 'REJECTED';

export type StandardStatus = 'FINAL_STANDARD' | 'DRAFT_STANDARD' | 'ROUND_4_CANDIDATE' | 'DEPRECATED';

export type ThreatScenarioType = 'CONSERVATIVE' | 'MODERATE' | 'AGGRESSIVE' | 'CUSTOM';

export type ValidationStatus = 'SUCCESS' | 'FAILED' | 'ERROR' | 'IN_PROGRESS';

export type TestingRequirement = 'BASIC' | 'STANDARD' | 'HIGH' | 'STRICT';

// System Health
export interface HealthResponse {
  status: string;
  version: string;
  database: string;
  versions: {
    ecdat_software_version?: string;
    scanner_rule_version?: string;
    cbom_schema_version?: string;
    crypto_knowledge_base_version?: string;
    risk_model_version?: string;
    threat_scenario_version?: string;
    [key: string]: string | undefined;
  };
  timestamp: string;
}

// Project
export interface Project {
  id: string;
  name: string;
  description?: string | null;
  repository_url?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreateInput {
  name: string;
  description?: string;
  repository_url?: string;
}

// Scan
export interface Scan {
  id: string;
  project_id: string;
  status: ScanStatus;
  target_path: string;
  scan_type: string;
  created_at: string;
  completed_at?: string | null;
  error_message?: string | null;
  cbom_version: string;
  scanner_rule_version: string;
}

export interface ScanCreateInput {
  target_path: string;
  scan_type?: string;
}

// Evidence
export interface Evidence {
  id: string;
  asset_id: string;
  evidence_type: EvidenceType;
  source_file: string;
  line_number?: number | null;
  detector_name: string;
  detector_version: string;
  excerpt?: string | null;
  confidence_score: number;
  provenance?: Record<string, any> | null;
  created_at: string;
}

// Crypto Asset
export interface CryptoAsset {
  id: string;
  scan_id: string;
  name: string;
  asset_type: AssetType;
  algorithm_name: string;
  key_size?: number | null;
  purpose: CryptoPurpose;
  location: string;
  line_number?: number | null;
  quantum_safety: QuantumSafety;
  is_unknown: boolean;
  unknown_reason?: string | null;
  review_status: ReviewStatus;
  created_at: string;
  evidence_items?: Evidence[];
}

// Coverage
export interface CategoryCoverage {
  category_name: string;
  scanned_count: number;
  coverage_percentage: number;
  notes: string;
}

export interface CoverageReport {
  project_id: string;
  overall_coverage_percentage: number;
  categories: CategoryCoverage[];
  total_assets_discovered: number;
  unknown_needs_review_count: number;
  disclaimer: string;
}

// Risk
export interface RiskSummary {
  project_id: string;
  total_assets: number;
  high_or_critical_risk_assets: number;
  average_risk_score: number;
}

export interface RiskAssessment {
  id?: string;
  asset_id: string;
  asset_name?: string;
  risk_score: number;
  risk_level: RiskLevel;
  quantum_vulnerability_score: number;
  data_sensitivity_score: number;
  business_criticality_score: number;
  mosca_factor_score: number;
  exposure_score: number;
  migration_complexity_score: number;
  explanation?: string | null;
  confidence_score: number;
  risk_model_version?: string;
  created_at?: string;
}

// Threat Scenario & Mosca
export interface ThreatScenario {
  id: string;
  name: string;
  scenario_type: ThreatScenarioType;
  quantum_threat_horizon_year: number;
  data_lifetime_years: number;
  migration_time_years: number;
  description?: string | null;
  threat_scenario_version?: string;
}

// Recommendations
export interface Recommendation {
  id?: string;
  asset_id: string;
  target_pqc_candidate: string;
  standard_status: StandardStatus;
  rationale: string;
  compatibility_notes?: string | null;
  performance_notes?: string | null;
  migration_complexity: string;
  confidence: number;
  kb_version?: string;
  created_at?: string;
}

// Graph
export interface GraphNode {
  id: string;
  name?: string;
  type?: string;
  algorithm?: string;
  centrality: number;
  [key: string]: any;
}

export interface GraphEdge {
  source: string;
  target: string;
  type?: string;
  [key: string]: any;
}

export interface ProjectGraph {
  project_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface AssetImpact {
  asset_id: string;
  affected_components_count: number;
  impacted_asset_ids: string[];
}

// Migration
export interface MigrationTask {
  id: string;
  plan_id: string;
  asset_id: string;
  title: string;
  description?: string | null;
  person_days: number;
  sequence_order: number;
  status: string;
  created_at: string;
}

export interface MigrationPlan {
  id: string;
  project_id: string;
  name: string;
  total_person_days: number;
  total_calendar_months: number;
  assumptions?: Record<string, any> | null;
  created_at: string;
  tasks: MigrationTask[];
}

export interface MigrationPlanCreateInput {
  name: string;
  vendor_dependency_count?: number;
  pki_cert_dependency_count?: number;
  crypto_agility_score?: number;
  testing_requirement_level?: TestingRequirement;
  engineering_capacity_developers?: number;
}

export interface SandboxSimulationResult {
  plan_id: string;
  sandbox_path: string;
  transformation: {
    pattern_applied: string;
    files_modified: string[];
    diff_summary: string;
    diff_details?: string;
  };
  status: string;
}

// Validation
export interface ValidationRun {
  id: string;
  plan_id: string;
  status: ValidationStatus;
  build_passed: boolean;
  unit_tests_passed: boolean;
  crypto_tests_passed: boolean;
  integration_tests_passed?: boolean;
  regression_passed?: boolean;
  api_compatible?: boolean;
  logs?: string | null;
  residual_risk_score: number;
  confidence: number;
  created_at: string;
}

// Audit
export interface AuditEvent {
  id: string;
  project_id?: string | null;
  action: string;
  actor: string;
  details?: Record<string, any> | null;
  created_at: string;
}

// CBOM
export interface CBOMCycloneDX {
  bomFormat: string;
  specVersion: string;
  version: number;
  metadata: Record<string, any>;
  components: any[];
}
