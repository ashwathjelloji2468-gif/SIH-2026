import { XResult } from './xEngine';
import { YResult } from './yEngine';
import { ZResultResponse } from './zEngine';

export type MoscaUrgency = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'REQUIRES_REVIEW';

export interface MoscaComponentResultResponse {
  component_id: string;
  algorithm: string;
  location?: string;
  x: XResult;
  y: YResult;
  z: ZResultResponse;
  mosca_score: number | null;
  urgency: MoscaUrgency;
  technical_urgency: MoscaUrgency;
  business_priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  explanation: string;
}

export interface MoscaProjectEvaluationResponse {
  project_id: string;
  project_name: string;
  total_components: number;
  critical_components: number;
  urgency_distribution: Record<MoscaUrgency, number>;
  components: MoscaComponentResultResponse[];
  explanation: string;
  evaluated_x?: XResult;
  evaluated_y?: YResult;
  evaluated_z_horizon?: number;
}
