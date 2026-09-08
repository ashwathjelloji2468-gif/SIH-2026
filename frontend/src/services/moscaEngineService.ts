import { api } from './api';
import { MoscaProjectEvaluationResponse, MoscaComponentResultResponse } from '../types/moscaEngine';

export async function getProjectMoscaContext(
  projectId: string,
  quantumHorizon?: number
): Promise<MoscaProjectEvaluationResponse> {
  const query = quantumHorizon ? `?quantum_horizon=${quantumHorizon}` : '';
  return await api.get<MoscaProjectEvaluationResponse>(`/projects/${projectId}/mosca-context${query}`);
}

export async function evaluateMoscaComponent(
  component: Record<string, any>,
  user_x_years?: number,
  user_y_scenario?: string,
  quantum_horizon?: number
): Promise<MoscaComponentResultResponse> {
  const searchParams = new URLSearchParams();
  if (user_x_years) searchParams.append('user_x_years', String(user_x_years));
  if (user_y_scenario) searchParams.append('user_y_scenario', user_y_scenario);
  if (quantum_horizon) searchParams.append('quantum_horizon', String(quantum_horizon));

  return await api.post<MoscaComponentResultResponse>(
    `/mosca/evaluate-component?${searchParams.toString()}`,
    component
  );
}
