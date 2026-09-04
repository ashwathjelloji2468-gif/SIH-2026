import React, { useState } from 'react';
import { useProject } from '../context/ProjectContext';
import { projectService } from '../services/projectService';
import { FolderGit2, Plus, Check, Trash2, ExternalLink, Calendar, Loader2, AlertCircle } from 'lucide-react';
import { Project as ProjectType } from '../types';

export const Project: React.FC = () => {
  const { projects, currentProject, setCurrentProject, refreshProjects } = useProject();
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [repoUrl, setRepoUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const created = await projectService.create({
        name,
        description,
        repository_url: repoUrl || undefined,
      });
      await refreshProjects();
      setCurrentProject(created);
      setCreateModalOpen(false);
      setName('');
      setDescription('');
      setRepoUrl('');
    } catch (err: any) {
      setError(err.message || 'Failed to create project.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this project and its scan data?')) return;
    try {
      await projectService.delete(id);
      await refreshProjects();
    } catch (err) {
      console.error('Failed to delete project:', err);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Top action header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold font-mono text-slate-100">Project & Repository Management</h1>
          <p className="text-xs text-slate-400 mt-1">
            Registered enterprise repositories inspected for quantum-vulnerable cryptography.
          </p>
        </div>

        <button
          onClick={() => setCreateModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs shadow-md shadow-cyan-950/50 cursor-pointer transition-all self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>Ingest New Repository</span>
        </button>
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {projects.map((p) => {
          const isSelected = currentProject?.id === p.id;
          return (
            <div
              key={p.id}
              onClick={() => setCurrentProject(p)}
              className={`rounded-2xl border p-5 transition-all cursor-pointer relative ${
                isSelected
                  ? 'border-cyan-500/80 bg-gradient-to-br from-cyan-950/30 via-[#0B0F19] to-[#0B0F19] shadow-lg shadow-cyan-950/20'
                  : 'border-slate-800 bg-[#0B0F19] hover:border-slate-700 hover:bg-slate-900/40'
              }`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2.5">
                  <div
                    className={`p-2 rounded-xl border ${
                      isSelected
                        ? 'bg-cyan-950/60 border-cyan-800/80 text-cyan-400'
                        : 'bg-slate-900 border-slate-800 text-slate-400'
                    }`}
                  >
                    <FolderGit2 className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold font-mono text-slate-100 truncate max-w-[180px]">
                      {p.name}
                    </h3>
                    <span className="text-[10px] text-slate-500 font-mono">
                      ID: {p.id.slice(0, 8)}
                    </span>
                  </div>
                </div>

                {isSelected ? (
                  <span className="inline-flex items-center gap-1 text-[11px] font-mono font-semibold text-cyan-400 bg-cyan-950/80 px-2 py-0.5 rounded-full border border-cyan-800/60">
                    <Check className="w-3 h-3" />
                    <span>Active</span>
                  </span>
                ) : (
                  <button
                    onClick={(e) => handleDelete(p.id, e)}
                    className="text-slate-600 hover:text-rose-400 p-1 transition-colors"
                    title="Delete project"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>

              <p className="text-xs text-slate-400 min-h-[32px] line-clamp-2 leading-relaxed mb-4">
                {p.description || 'No project description configured.'}
              </p>

              <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] font-mono text-slate-500">
                <span className="flex items-center gap-1">
                  <Calendar className="w-3 h-3 text-slate-600" />
                  <span>{new Date(p.created_at).toLocaleDateString()}</span>
                </span>
                {p.repository_url && (
                  <span className="text-cyan-400 truncate max-w-[120px]">{p.repository_url}</span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Ingest Repository Modal */}
      {createModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-[#0B0F19] p-6 shadow-2xl">
            <h3 className="text-base font-bold font-mono text-slate-100 mb-1">Ingest New Project</h3>
            <p className="text-xs text-slate-400 mb-4">Register a git repository or local codebase target</p>

            {error && (
              <div className="mb-4 p-3 rounded-lg bg-rose-950/50 border border-rose-800/60 text-xs text-rose-300 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Project Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-xs font-mono focus:outline-none focus:border-cyan-500"
                  placeholder="e.g. core-auth-service"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Description</label>
                <textarea
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-cyan-500"
                  placeholder="Service description and scope"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Repository URL (Optional)</label>
                <input
                  type="text"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-xs font-mono focus:outline-none focus:border-cyan-500"
                  placeholder="https://github.com/org/repo.git"
                />
              </div>

              <div className="pt-3 flex justify-end gap-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setCreateModalOpen(false)}
                  className="px-4 py-2 rounded-lg border border-slate-800 text-slate-300 text-xs hover:bg-slate-900 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-xs cursor-pointer shadow-md shadow-cyan-950/50"
                >
                  {loading ? 'Creating...' : 'Register Project'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
