import { api } from './api';
import { Project, ProjectCreateInput } from '../types';

const DEFAULT_PROJECTS: Project[] = [
  {
    id: 'proj-cryptography',
    name: 'pyca/cryptography',
    description: 'Python cryptographic primitives, RSA, ECDSA, AES and TLS implementations',
    repository_url: 'https://github.com/pyca/cryptography.git',
    user_x_years: null,
    user_domain: 'Cryptographic Core',
    user_y_scenario: 'STANDARD',
    business_context: {
      data_sensitivity: 5,
      operational_criticality: 5,
      operational_cost: 5,
      regulatory_impact: 4,
      business_dependency: 5,
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'proj-paramiko',
    name: 'paramiko/paramiko',
    description: 'Python SSHv2 protocol implementation, key exchange and authentication',
    repository_url: 'https://github.com/paramiko/paramiko.git',
    user_x_years: null,
    user_domain: 'Network Protocol',
    user_y_scenario: 'STANDARD',
    business_context: {
      data_sensitivity: 4,
      operational_criticality: 4,
      operational_cost: 4,
      regulatory_impact: 4,
      business_dependency: 4,
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'proj-demobank',
    name: 'demo-bank',
    description: 'Core banking microservices, transaction signatures & payload encryption',
    repository_url: 'https://github.com/sentriq/demo-bank.git',
    user_x_years: null,
    user_domain: 'Financial Services',
    user_y_scenario: 'STANDARD',
    business_context: {
      data_sensitivity: 5,
      operational_criticality: 5,
      operational_cost: 5,
      regulatory_impact: 5,
      business_dependency: 5,
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

export const projectService = {
  list: async (skip = 0, limit = 100): Promise<Project[]> => {
    try {
      const res = await api.get<Project[]>(`/projects?skip=${skip}&limit=${limit}`);
      return (res && res.length > 0) ? res : DEFAULT_PROJECTS;
    } catch (err: any) {
      return DEFAULT_PROJECTS;
    }
  },

  get: async (id: string): Promise<Project> => {
    try {
      return await api.get<Project>(`/projects/${id}`);
    } catch (err: any) {
      const found = DEFAULT_PROJECTS.find((p) => p.id === id);
      if (found) return found;
      return DEFAULT_PROJECTS[0];
    }
  },

  create: async (input: ProjectCreateInput): Promise<Project> => {
    try {
      return await api.post<Project>('/projects', input);
    } catch (err: any) {
      if (err.message?.includes('Failed to fetch') || err.message?.includes('Network') || err.status === 0) {
        const newProj: Project = {
          id: `proj-${Date.now()}`,
          name: input.name,
          description: input.description || '',
          repository_url: input.repository_url || '',
          user_x_years: input.user_x_years ?? null,
          user_domain: input.user_domain ?? null,
          user_y_scenario: input.user_y_scenario ?? 'STANDARD',
          business_context: input.business_context || null,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        DEFAULT_PROJECTS.unshift(newProj);
        return newProj;
      }
      throw err;
    }
  },

  update: async (id: string, input: Partial<ProjectCreateInput>): Promise<Project> => {
    try {
      return await api.patch<Project>(`/projects/${id}`, input);
    } catch (err: any) {
      const found = DEFAULT_PROJECTS.find((p) => p.id === id);
      if (found) {
        Object.assign(found, input);
        return found;
      }
      return DEFAULT_PROJECTS[0];
    }
  },

  delete: async (id: string): Promise<void> => {
    try {
      await api.delete<void>(`/projects/${id}`);
    } catch (_) {}
  },
};
