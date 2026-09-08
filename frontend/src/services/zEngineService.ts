import { api } from './api';
import { ZProjectEvaluationResponse, ZResultResponse, ZComponentInput } from '../types/zEngine';

export async function getProjectZContext(
  projectId: string,
  quantumHorizon: number = 10
): Promise<ZProjectEvaluationResponse> {
  return await api.get<ZProjectEvaluationResponse>(`/projects/${projectId}/z-context?quantum_horizon=${quantumHorizon}`);
}

export async function evaluateZComponent(
  component: ZComponentInput,
  quantumHorizon: number = 10
): Promise<ZResultResponse> {
  return await api.post<ZResultResponse>(`/z-engine/evaluate-component?quantum_horizon=${quantumHorizon}`, component);
}
