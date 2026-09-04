import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { Project, Scan } from '../types';
import { projectService } from '../services/projectService';
import { scanService } from '../services/scanService';

interface ProjectContextType {
  projects: Project[];
  currentProject: Project | null;
  setCurrentProject: (project: Project | null) => void;
  loading: boolean;
  error: string | null;
  refreshProjects: () => Promise<void>;
  latestScan: Scan | null;
  refreshLatestScan: () => Promise<void>;
  isScanModalOpen: boolean;
  setIsScanModalOpen: (open: boolean) => void;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

const SAVED_PROJECT_KEY = 'sentriq_active_project_id';

export const ProjectProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [currentProject, setCurrentProjectState] = useState<Project | null>(null);
  const [latestScan, setLatestScan] = useState<Scan | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isScanModalOpen, setIsScanModalOpen] = useState<boolean>(false);

  const fetchProjects = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await projectService.list();
      setProjects(data);

      if (data.length > 0) {
        // Try to restore saved project or pick first with scans/assets
        const savedId = localStorage.getItem(SAVED_PROJECT_KEY);
        const matched = savedId ? data.find((p) => p.id === savedId) : null;
        
        // Default to cryptography or paramiko or demo if available, otherwise first
        const preferred = matched || 
          data.find((p) => p.name.includes('cryptography')) || 
          data.find((p) => p.name.includes('paramiko')) || 
          data.find((p) => p.name.startsWith('demo-')) || 
          data[0];

        setCurrentProjectState(preferred);
      } else {
        setCurrentProjectState(null);
      }
    } catch (err: any) {
      console.error('Failed to load projects:', err);
      setError(err.message || 'Unable to connect to SENTRIQ backend.');
    } finally {
      setLoading(false);
    }
  }, []);

  const setCurrentProject = (proj: Project | null) => {
    setCurrentProjectState(proj);
    if (proj) {
      localStorage.setItem(SAVED_PROJECT_KEY, proj.id);
    } else {
      localStorage.removeItem(SAVED_PROJECT_KEY);
    }
  };

  const fetchLatestScan = useCallback(async () => {
    if (!currentProject) {
      setLatestScan(null);
      return;
    }
    try {
      const scans = await scanService.getProjectScans(currentProject.id);
      if (scans && scans.length > 0) {
        // Sort descending by created_at
        const sorted = [...scans].sort(
          (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
        setLatestScan(sorted[0]);
      } else {
        setLatestScan(null);
      }
    } catch (err) {
      console.warn('Could not fetch latest scan:', err);
      setLatestScan(null);
    }
  }, [currentProject]);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  useEffect(() => {
    fetchLatestScan();
  }, [fetchLatestScan]);

  return (
    <ProjectContext.Provider
      value={{
        projects,
        currentProject,
        setCurrentProject,
        loading,
        error,
        refreshProjects: fetchProjects,
        latestScan,
        refreshLatestScan: fetchLatestScan,
        isScanModalOpen,
        setIsScanModalOpen,
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
};

export const useProject = (): ProjectContextType => {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
};
