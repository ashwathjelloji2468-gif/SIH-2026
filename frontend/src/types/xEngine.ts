export type XSource = 'USER' | 'DOMAIN_BASELINE' | 'SYSTEM_DEFAULT';

export type XConfidence = 'HIGH' | 'MEDIUM' | 'LOW';

export type XContextLevel = 'REPOSITORY' | 'FOLDER';

export interface XResult {
  value: number;
  unit: 'years';
  source: XSource;
  domain?: string;
  domainTitle?: string;
  confidence?: XConfidence;
  explanation: string;
  overrideAvailable: boolean;
  userX?: number | null;
  estimatedDomainX?: number | null;
  contextLevel?: XContextLevel;
  matchedIndicators?: string[];
}

export interface DomainBaseline {
  key: string;
  title: string;
  baseline_x_years: number;
  description: string;
  compliance_references: string[];
  keywords: string[];
}

export interface FolderXContext {
  user_x_years: number;
  notes?: string;
}

export interface ProjectXContextResponse {
  project_id: string;
  project_name: string;
  user_x_years?: number | null;
  user_domain?: string | null;
  folder_contexts?: Record<string, FolderXContext>;
  x_result: XResult;
}

export interface XContextUpdateInput {
  user_x_years?: number | null;
  user_domain?: string | null;
  folder_path?: string | null;
  folder_x_years?: number | null;
  folder_notes?: string | null;
  clear_user_x?: boolean;
}
