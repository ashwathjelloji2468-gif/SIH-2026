export type YScenarioKey = 'FAST' | 'STANDARD' | 'COMPLEX' | 'LEGACY_HEAVY';

export type YSource = 'SYSTEM_DEFAULT' | 'USER_SELECTED';

export interface YResult {
  value: 5 | 10 | 15 | 20;
  unit: 'years';
  scenario: YScenarioKey;
  scenarioTitle: string;
  source: YSource;
  explanation: string;
  details?: string;
}

export interface MigrationScenario {
  key: YScenarioKey;
  title: string;
  value: number;
  description: string;
  details: string;
}

export interface ProjectYContextResponse {
  project_id: string;
  project_name: string;
  user_y_scenario?: YScenarioKey | null;
  y_result: YResult;
}

export interface YContextUpdateInput {
  user_y_scenario?: YScenarioKey | null;
  clear_user_y?: boolean;
}
