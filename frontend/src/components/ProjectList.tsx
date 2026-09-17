import React, { useState } from 'react';
import { Film, Plus, Search, Filter, ShieldAlert, ShieldCheck, Copy, Trash2, ArrowRight } from 'lucide-react';
import { Project, api } from '../services/api';

interface ProjectListProps {
  projects: Project[];
  onSelectProject: (id: string) => void;
  onRefresh: () => void;
}

export const ProjectList: React.FC<ProjectListProps> = ({ projects, onSelectProject, onRefresh }) => {
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [filterType, setFilterType] = useState('ALL');
  const [showModal, setShowModal] = useState(false);

  // New project form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [rightsStatus, setRightsStatus] = useState('I own this content');
  const [tagInput, setTagInput] = useState('');

  const filtered = projects.filter(p => {
    const matchesSearch = p.name.toLowerCase().includes(search.toLowerCase()) || 
                          p.description.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = filterStatus === 'ALL' || p.status === filterStatus;
    const pType = p.project_type || 'CREATOR_REVIEW';
    const matchesType = filterType === 'ALL' || pType === filterType;
    return matchesSearch && matchesStatus && matchesType;
  });


  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    const tags = tagInput.split(',').map(t => t.trim()).filter(Boolean);
    try {
      const res = await api.createProject({
        name,
        description,
        rights_status: rightsStatus,
        tags
      });
      setShowModal(false);
      setName('');
      setDescription('');
      onRefresh();
      onSelectProject(res.id);
    } catch (err) {
      alert("Failed to create project: " + err);
    }
  };

  const handleDuplicate = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    try {
      await api.duplicateProject(id);
      onRefresh();
    } catch (err) {
      alert("Failed to duplicate: " + err);
    }
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (confirm("Are you sure you want to delete this project?")) {
      await api.deleteProject(id);
      onRefresh();
    }
  };

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto overflow-y-auto h-full">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Projects</h1>
          <p className="text-xs text-slate-400 mt-1">Manage video repurposing workspaces and export archives</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition shadow-md shadow-indigo-600/20"
        >
          <Plus className="w-4 h-4" /> New Project
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-500" />
          <input
            type="text"
            placeholder="Search projects by title or description..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-studio-900 border border-studio-800 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <select
          value={filterType}
          onChange={e => setFilterType(e.target.value)}
          className="px-3 py-2 rounded-xl bg-studio-900 border border-studio-800 text-sm text-slate-300 focus:outline-none focus:border-indigo-500"
        >
          <option value="ALL">All Types</option>
          <option value="CREATOR_REVIEW">🎬 Creator Review</option>
          <option value="MEME_STUDIO">😂 Meme Studio</option>
        </select>

        <select
          value={filterStatus}
          onChange={e => setFilterStatus(e.target.value)}
          className="px-3 py-2 rounded-xl bg-studio-900 border border-studio-800 text-sm text-slate-300 focus:outline-none focus:border-indigo-500"
        >
          <option value="ALL">All Statuses</option>
          <option value="DRAFT">Draft</option>
          <option value="ANALYZING">Analyzing</option>
          <option value="CANDIDATE">Candidate</option>
          <option value="READY">Ready</option>
          <option value="APPROVED">Approved</option>
        </select>
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filtered.map(proj => {
          const isMeme = proj.project_type === 'MEME_STUDIO';
          const count = isMeme ? (proj.meme_count || 0) : (proj.clip_count || 0);
          const countLabel = isMeme ? 'memes' : 'shorts';

          return (
            <div
              key={proj.id}
              onClick={() => onSelectProject(proj.id)}
              className="group rounded-xl bg-studio-900 border border-studio-800 hover:border-studio-700 hover:bg-studio-850 p-5 cursor-pointer transition-all flex flex-col justify-between shadow-lg space-y-4"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <div className={`w-9 h-9 rounded-lg border flex items-center justify-center ${
                    isMeme 
                      ? 'bg-amber-500/10 border-amber-500/20 text-amber-400' 
                      : 'bg-indigo-500/10 border-indigo-500/20 text-indigo-400'
                  }`}>
                    {isMeme ? <span className="text-base">😂</span> : <Film className="w-4 h-4" />}
                  </div>

                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    isMeme 
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' 
                      : 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                  }`}>
                    {isMeme ? 'Meme Studio' : 'Creator Review'}
                  </span>

                  <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity ml-auto">
                    <button
                      onClick={(e) => handleDuplicate(e, proj.id)}
                      title="Duplicate"
                      className="p-1.5 rounded hover:bg-studio-700 text-slate-400 hover:text-white"
                    >
                      <Copy className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={(e) => handleDelete(e, proj.id)}
                      title="Delete"
                      className="p-1.5 rounded hover:bg-rose-500/20 text-slate-400 hover:text-rose-400"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                <h3 className="mt-3 text-base font-semibold text-white group-hover:text-indigo-400 transition-colors line-clamp-1">
                  {proj.name}
                </h3>
                <p className="mt-1 text-xs text-slate-400 line-clamp-2 leading-relaxed">
                  {proj.description || "No description provided."}
                </p>
              </div>

              <div className="pt-3 border-t border-studio-800 flex items-center justify-between text-xs">
                <div className="flex items-center gap-1.5 text-slate-400 text-[11px]">
                  <span>{count} {countLabel}</span>
                </div>
                <span className="px-2 py-0.5 rounded bg-studio-800 text-slate-300 font-mono text-[10px]">
                  {proj.status}
                </span>
              </div>
            </div>
          );
        })}
      </div>


      {/* New Project Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-studio-900 border border-studio-700 rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-5">
            <h2 className="text-xl font-bold text-white">Create New Project</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Project Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Masterclass Episode 4"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-studio-950 border border-studio-800 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Description</label>
                <textarea
                  rows={2}
                  placeholder="Notes or source info..."
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl bg-studio-950 border border-studio-800 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Content Rights Status * (Required for Safe Publishing)
                </label>
                <select
                  value={rightsStatus}
                  onChange={e => setRightsStatus(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-studio-950 border border-studio-800 text-sm text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="I own this content">I own this content</option>
                  <option value="I have permission">I have permission</option>
                  <option value="Licensed content">Licensed content</option>
                  <option value="Public domain / permitted use">Public domain / permitted use</option>
                  <option value="Not confirmed">Not confirmed (Automatic publishing blocked)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Tags (comma separated)</label>
                <input
                  type="text"
                  placeholder="podcast, education, tech"
                  value={tagInput}
                  onChange={e => setTagInput(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl bg-studio-950 border border-studio-800 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-xl text-sm text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition"
                >
                  Create Project
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
