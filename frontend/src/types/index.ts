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

export type TestingRequirement = 'LOW' | 'MEDIUM' | 'HIGH' | 'REGULATED';

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

// Project Business Context
export interface BusinessContextInput {
  data_sensitivity: number;
  operational_criticality: number;
  operational_cost: number;
  regulatory_impact: number;
  business_dependency: number;
}

// Project
export interface Project {
  id: string;
  name: string;
  description?: string | null;
  repository_url?: string | null;
  user_x_years?: number | null;
  user_domain?: string | null;
  user_y_scenario?: string | null;
  business_context?: BusinessContextInput | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreateInput {
  name: string;
  description?: string;
  repository_url?: string;
  user_x_years?: number;
  user_domain?: string;
  user_y_scenario?: string;
  business_context?: BusinessContextInput;
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
  data_lifetime_years?: number | null;
  lifetime_label?: string | null;
  business_criticality_label?: string | null;
  business_criticality_score?: number | null;
  classification_summary?: string | null;
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
  assessed_assets?: number;
  unassessed_assets?: number;
  high_or_critical_risk_assets: number;
  average_risk_score: number;
  risk_counts?: {
    low: number;
    moderate: number;
    high: number;
    critical: number;
  };
  quantum_vulnerable_count?: number;
  quantum_resistant_count?: number;
  unknown_count?: number;
  mosca?: {
    mosca_score: number;
    mosca_status: string;
    urgency_gap_years: number;
    quantum_threat_horizon: number;
    years_until_quantum: number;
    data_lifetime_years: number;
    migration_time_years: number;
    protection_window_years: number;
    rationale?: string;
    urgency_level?: string;
  };
  priority_list?: RiskAssessment[];
  highest_risk_assets?: RiskAssessment[];
}


export interface RiskAssessment {
  id?: string;
  asset_id: string;
  asset_name?: string;
  algorithm_name?: string;
  location?: string;
  quantum_status?: string;
  crypto_purpose?: string;
  risk_score: number;
  risk_level: RiskLevel | string;
  priority?: string;
  quantum_vulnerability_score?: number;
  data_sensitivity_score?: number;
  business_criticality_score?: number;
  mosca_factor_score?: number;
  exposure_score?: number;
  migration_complexity_score?: number;
  explanation?: string | null;
  confidence_score: number;
  risk_model_version?: string;
  created_at?: string;
  x?: {
    value: number;
    unit?: string;
    source?: string;
    explanation?: string;
  };
  y?: {
    value: number;
    unit?: string;
    scenario?: string;
    explanation?: string;
  };
  z?: {
    z_score?: number;
    z_planning_horizon_years?: number;
    z_target_year?: number;
    z_value?: number;
    quantum_class?: string;
    status?: string;
    base_score?: number;
    env_multiplier?: number;
    dep_factor?: number;
    explanation?: string;
  };
  z_score?: number;
  z_planning_horizon_years?: number;
  mosca_score?: number;
  technical_urgency?: string;
  factors?: {
    quantum_exposure?: number;
    data_sensitivity?: number;
    business_criticality?: number;
    migration_complexity?: number;
    lifetime_exposure?: number;
    mosca_score?: number;
  };
  mosca?: {
    mosca_status?: string;
    quantum_threat_horizon?: number;
    rationale?: string;
    mosca_score?: number;
    x_years?: number;
    y_years?: number;
    z_horizon_years?: number;
    z_score?: number;
    x?: number;
    y?: number;
    z?: number;
  };
  threat_scenarios?: Array<{
    id?: string;
    scenario_type?: string;
    name?: string;
    severity?: string;
    urgency?: string;
    description?: string;
    rationale?: string;
  }>;
  rationale?: string[];
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
  asset_name?: string;
  algorithm_name?: string;
  location?: string;
  line_number?: number | null;
  crypto_purpose?: string;
  quantum_status?: string;
  target_pqc_candidate: string;
  recommended_algorithm?: string;
  alternative_algorithm?: string;
  transformation_pattern?: string;
  category?: string;
  priority?: string;
  standard_status: StandardStatus;
  rationale: string;
  compatibility_notes?: string | null;
  performance_notes?: string | null;
  latency_impact?: string;
  cost_impact?: string;
  latency_level?: 'LOW' | 'MODERATE' | 'HIGH' | 'UNKNOWN';
  cost_level?: 'LOW' | 'MEDIUM' | 'HIGH' | 'UNKNOWN';
  tradeoffs?: Record<string, any>;
  threat_scenarios?: Array<any>;
  migration_notes?: string;
  migration_complexity: string;
  confidence: number;
  kb_version?: string;
  created_at?: string;
  risk_score?: number;
  risk_level?: string;
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
  simulation_id?: string;
  sandbox_path: string;
  transformation: {
    pattern_applied: string;
    files_modified: string[];
    diff_summary: string;
    diff_details?: string;
    original_snippet?: string;
    transformed_snippet?: string;
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

// Stage 8: Blast Radius & Network Dependence
export interface CryptoNode {
  id: string;
  scan_id: string;
  asset_id?: string | null;
  artefact_type: string;
  name: string;
  version?: string | null;
  location?: string | null;
  quantum_risk: string;
  mosca_x: number;
  business_criticality: number;
  extra_metadata?: Record<string, any> | null;
}

export interface CryptoEdge {
  id: string;
  scan_id: string;
  source_node_id: string;
  target_node_id: string;
  relation_type: string;
  strength: number;
  extra_metadata?: Record<string, any> | null;
}

export interface ScanGraph {
  scan_id: string;
  nodes: CryptoNode[];
  edges: CryptoEdge[];
  total_nodes: number;
  total_edges: number;
  single_points_of_failure: Array<{
    node_id: string;
    name: string;
    artefact_type: string;
    degree: number;
    quantum_risk: string;
  }>;
}

export interface BlastRadiusAffectedNode {
  node_id: string;
  name: string;
  artefact_type: string;
  location?: string | null;
  quantum_risk: string;
  distance: number;
  relation_path: string[];
  impact_score: number;
}

export interface BlastRadiusResult {
  id?: string;
  scan_id: string;
  root_node_id: string;
  root_node_name: string;
  root_node_type: string;
  radius_score: number;
  affected_nodes_count: number;
  systems_count: number;
  data_classes: string[];
  estimated_migration_effort: number;
  affected_nodes: BlastRadiusAffectedNode[];
  affected_systems: string[];
}

export interface TopBlastRadiusSummary {
  project_id: string;
  top_blast_radii: BlastRadiusResult[];
  shared_credentials_high_impact: Array<{
    credential_name: string;
    source_location: string;
    target_location: string;
    shared_metadata?: Record<string, any>;
    risk_level: string;
    impact_description: string;
  }>;
  single_points_of_failure: Array<{
    node_id: string;
    node_name: string;
    node_type: string;
    radius_score: number;
    affected_systems_count: number;
    risk_level: string;
  }>;
}

