import { api } from './api';
import { MoscaProjectEvaluationResponse, MoscaComponentResultResponse } from '../types/moscaEngine';

export async function getProjectMoscaContext(
  projectId: string,
  params?: {
    user_x_years?: number;
    user_domain?: string;
    user_y_scenario?: string;
    quantum_horizon?: number;
  }
): Promise<MoscaProjectEvaluationResponse> {
  const searchParams = new URLSearchParams();
  if (params?.user_x_years) searchParams.append('user_x_years', String(params.user_x_years));
  if (params?.user_domain) searchParams.append('user_domain', params.user_domain);
  if (params?.user_y_scenario) searchParams.append('user_y_scenario', params.user_y_scenario);
  if (params?.quantum_horizon) searchParams.append('quantum_horizon', String(params.quantum_horizon));

  const queryStr = searchParams.toString() ? `?${searchParams.toString()}` : '';
  return await api.get<MoscaProjectEvaluationResponse>(`/projects/${projectId}/mosca-context${queryStr}`);
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
