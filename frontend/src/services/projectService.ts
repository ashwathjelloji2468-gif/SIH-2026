import { api } from './api';
import { Project, ProjectCreateInput } from '../types';

export const projectService = {
  list: async (skip = 0, limit = 100): Promise<Project[]> => {
    return api.get<Project[]>(`/projects?skip=${skip}&limit=${limit}`);
  },

  get: async (id: string): Promise<Project> => {
    return api.get<Project>(`/projects/${id}`);
  },

  create: async (input: ProjectCreateInput): Promise<Project> => {
    return api.post<Project>('/projects', input);
  },

  update: async (id: string, input: Partial<ProjectCreateInput>): Promise<Project> => {
    return api.patch<Project>(`/projects/${id}`, input);
  },

  delete: async (id: string): Promise<void> => {
    return api.delete<void>(`/projects/${id}`);
  },
};
