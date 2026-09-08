export type QuantumClass =
  | 'SHOR_VULNERABLE'
  | 'QUANTUM_STRENGTH_REDUCTION'
  | 'PQC_RESISTANT'
  | 'HYBRID'
  | 'UNKNOWN';

export type ZComponentStatus =
  | 'VULNERABLE_AT_HORIZON'
  | 'QUANTUM_UNACCEPTABLE_AT_HORIZON'
  | 'REDUCED_BUT_ACCEPTABLE'
  | 'REQUIRES_REVIEW'
  | 'NO_IMMEDIATE_QUANTUM_DEADLINE';

export interface ZComponentInput {
  id?: string;
  component_id?: string;
  primitive?: string;
  algorithm_name?: string;
  algorithm?: string;
  key_size?: number;
  output_size?: number;
  purpose?: string;
  location?: string;
  repository_path?: string;
}

export interface ZResultResponse {
  component_id: string;
  primitive: string;
  algorithm: string;
  key_size?: number;
  location?: string;
  quantum_horizon: number;
  target_horizon_year: number;
  quantum_class: QuantumClass;
  status: ZComponentStatus;
  z_value?: number;
  classical_security_bits?: number;
  quantum_security_bits?: number;
  explanation: string;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  metadata?: {
    model: string;
    current_year: number;
    threat_horizon_year: number;
    disclaimer: string;
  };
}

export interface ZProjectEvaluationResponse {
  quantum_horizon: number;
  target_horizon_year: number;
  total_components: number;
  vulnerable_components: number;
  class_breakdown: Record<QuantumClass, number>;
  status_breakdown: Record<ZComponentStatus, number>;
  components: ZResultResponse[];
  explanation: string;
}
