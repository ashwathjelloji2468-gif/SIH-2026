import { api } from './api';
import { MigrationScenario, ProjectYContextResponse, YResult, YContextUpdateInput, YScenarioKey } from '../types/yEngine';
import { MIGRATION_SCENARIOS_LIST, DEFAULT_Y_YEARS_VALUE, DEFAULT_Y_SCENARIO_KEY } from '../config/migrationScenarios';

export async function getMigrationScenarios(): Promise<MigrationScenario[]> {
  try {
    return await api.get<MigrationScenario[]>('/y-engine/scenarios');
  } catch (error) {
    console.warn('Using client fallback for migration scenarios', error);
    return MIGRATION_SCENARIOS_LIST;
  }
}

export async function evaluateYContext(userScenario?: string): Promise<YResult> {
  const query = userScenario ? `?user_scenario=${encodeURIComponent(userScenario)}` : '';
  try {
    return await api.post<YResult>(`/y-engine/evaluate${query}`);
  } catch (error) {
    console.warn('Using client evaluation fallback for Y Engine', error);
    const key = (userScenario || DEFAULT_Y_SCENARIO_KEY).toUpperCase() as YScenarioKey;
    const item = MIGRATION_SCENARIOS_LIST.find(s => s.key === key) || MIGRATION_SCENARIOS_LIST[1];
    return {
      value: item.value as 5 | 10 | 15 | 20,
      unit: 'years',
      scenario: item.key,
      scenarioTitle: item.title,
      source: userScenario ? 'USER_SELECTED' : 'SYSTEM_DEFAULT',
      explanation: userScenario
        ? `User-selected migration scenario '${item.title}' active.`
        : 'Standardized 10-year migration planning assumption applied for MVP.',
      details: item.details
    };
  }
}

export async function getProjectYContext(projectId: string): Promise<ProjectYContextResponse> {
  return await api.get<ProjectYContextResponse>(`/projects/${projectId}/y-context`);
}

export async function updateProjectYContext(
  projectId: string,
  input: YContextUpdateInput
): Promise<ProjectYContextResponse> {
  return await api.post<ProjectYContextResponse>(`/projects/${projectId}/y-context`, input);
}
