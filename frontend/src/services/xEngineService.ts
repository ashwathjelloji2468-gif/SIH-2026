import { api } from './api';
import { DomainBaseline, ProjectXContextResponse, XResult, XContextUpdateInput } from '../types/xEngine';
import { DOMAIN_BASELINES_LIST, DEFAULT_X_FALLBACK_YEARS } from '../config/domainBaselines';

export async function getDomainBaselines(): Promise<DomainBaseline[]> {
  try {
    return await api.get<DomainBaseline[]>('/x-engine/baselines');
  } catch (error) {
    console.warn('Using client fallback for domain baselines', error);
    return DOMAIN_BASELINES_LIST;
  }
}

export async function evaluateXContext(params: {
  user_x_years?: number;
  user_domain?: string;
  project_name?: string;
  description?: string;
  target_path?: string;
  folder_path?: string;
}): Promise<XResult> {
  const searchParams = new URLSearchParams();
  if (params.user_x_years) searchParams.append('user_x_years', String(params.user_x_years));
  if (params.user_domain) searchParams.append('user_domain', params.user_domain);
  if (params.project_name) searchParams.append('project_name', params.project_name);
  if (params.description) searchParams.append('description', params.description);
  if (params.target_path) searchParams.append('target_path', params.target_path);
  if (params.folder_path) searchParams.append('folder_path', params.folder_path);

  try {
    return await api.post<XResult>(`/x-engine/evaluate?${searchParams.toString()}`);
  } catch (error) {

    console.warn('Using client evaluation fallback for X Engine', error);
    const userVal = params.user_x_years;
    if (userVal) {
      return {
        value: userVal,
        unit: 'years',
        source: 'USER',
        explanation: `Organization-selected confidentiality horizon: ${userVal} years.`,
        overrideAvailable: true,
        userX: userVal,
        estimatedDomainX: DEFAULT_X_FALLBACK_YEARS,
        contextLevel: params.folder_path ? 'FOLDER' : 'REPOSITORY'
      };
    }
    return {
      value: DEFAULT_X_FALLBACK_YEARS,
      unit: 'years',
      source: 'SYSTEM_DEFAULT',
      explanation: 'Conservative 20-year confidentiality planning horizon applied.',
      overrideAvailable: true,
      userX: null,
      estimatedDomainX: DEFAULT_X_FALLBACK_YEARS,
      contextLevel: 'REPOSITORY'
    };
  }
}

export async function getProjectXContext(projectId: string, folderPath?: string): Promise<ProjectXContextResponse> {
  const query = folderPath ? `?folder_path=${encodeURIComponent(folderPath)}` : '';
  return await api.get<ProjectXContextResponse>(`/projects/${projectId}/x-context${query}`);
}

export async function updateProjectXContext(
  projectId: string,
  input: XContextUpdateInput
): Promise<ProjectXContextResponse> {
  return await api.post<ProjectXContextResponse>(`/projects/${projectId}/x-context`, input);
}

