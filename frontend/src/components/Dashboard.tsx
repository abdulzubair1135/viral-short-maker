import React, { useEffect, useState } from 'react';
import { Play, Sparkles, CheckCircle2, AlertTriangle, Film, Layers, ArrowUpRight, Clock, ShieldCheck } from 'lucide-react';
import { api, Project, Job } from '../services/api';

interface DashboardProps {
  onSelectProject: (id: string) => void;
  onCreateProjectClick: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onSelectProject, onCreateProjectClick }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [recentJobs, setRecentJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [projData, jobData] = await Promise.all([
          api.getProjects(),
          api.getJobs()
        ]);
        setProjects(projData);
        setRecentJobs(jobData);
      } catch (e) {
        console.error("Failed to load dashboard:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const totalClips = projects.reduce((acc, p) => acc + (p.clip_count || 0), 0);
  const activeJobs = recentJobs.filter(j => j.status !== 'READY' && j.status !== 'FAILED' && j.status !== 'CANCELLED');

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto overflow-y-auto h-full">
      {/* Hero Welcome Banner */}
      <div className="relative rounded-2xl bg-gradient-to-r from-studio-900 via-studio-850 to-indigo-950/40 p-8 border border-studio-700/60 shadow-2xl overflow-hidden">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-400 text-xs font-semibold tracking-wide uppercase mb-4 border border-indigo-500/20">
            <Sparkles className="w-3.5 h-3.5" /> Desktop AI Studio • No APIs Required
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight sm:text-4xl">
            Repurpose Videos into Viral Shorts
          </h1>
          <p className="mt-3 text-slate-300 text-sm leading-relaxed">
            Automated speech analysis, intelligent browser-based AI moment selection, 9:16 smart subject reframing, and animated karaoke captions with strict 15-point quality assurance.
          </p>
          <div className="mt-6 flex items-center gap-4">
            <button
              onClick={onCreateProjectClick}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-all shadow-lg shadow-indigo-600/25"
            >
              <Film className="w-4 h-4" /> New Project
            </button>
          </div>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-5 rounded-xl bg-studio-900 border border-studio-800 shadow-md">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Total Projects</span>
            <Layers className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="mt-3 text-2xl font-bold text-white">{projects.length}</div>
          <p className="mt-1 text-xs text-slate-400">Organized workspaces</p>
        </div>

        <div className="p-5 rounded-xl bg-studio-900 border border-studio-800 shadow-md">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Generated Shorts</span>
            <Film className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-3 text-2xl font-bold text-white">{totalClips}</div>
          <p className="mt-1 text-xs text-slate-400">Candidate & ready clips</p>
        </div>

        <div className="p-5 rounded-xl bg-studio-900 border border-studio-800 shadow-md">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Active Queue</span>
            <Clock className="w-4 h-4 text-sky-400" />
          </div>
          <div className="mt-3 text-2xl font-bold text-white">{activeJobs.length}</div>
          <p className="mt-1 text-xs text-slate-400">Background renders running</p>
        </div>

        <div className="p-5 rounded-xl bg-studio-900 border border-studio-800 shadow-md">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Rights Safety</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-3 text-2xl font-bold text-emerald-400">Enforced</div>
          <p className="mt-1 text-xs text-slate-400">100% permission checked</p>
        </div>
      </div>

      {/* Recent Projects & Queue */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-white">Recent Projects</h2>
            <button onClick={onCreateProjectClick} className="text-xs text-indigo-400 hover:text-indigo-300 font-medium">
              View All &rarr;
            </button>
          </div>

          <div className="space-y-3">
            {projects.length === 0 ? (
              <div className="p-8 text-center rounded-xl bg-studio-900 border border-studio-800 text-slate-400 text-sm">
                No projects created yet. Click "New Project" to begin.
              </div>
            ) : (
              projects.slice(0, 5).map(p => (
                <div
                  key={p.id}
                  onClick={() => onSelectProject(p.id)}
                  className="group flex items-center justify-between p-4 rounded-xl bg-studio-900/80 hover:bg-studio-850 border border-studio-800 hover:border-studio-700 cursor-pointer transition-all"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 group-hover:scale-105 transition-transform">
                      <Film className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-white group-hover:text-indigo-400 transition-colors">
                        {p.name}
                      </h3>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-slate-400">
                          {p.clip_count || 0} Shorts
                        </span>
                        <span className="text-slate-600">•</span>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                          p.rights_status === 'Not confirmed' 
                            ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                            : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        }`}>
                          {p.rights_status}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs px-2.5 py-1 rounded-md bg-studio-800 text-slate-300 font-mono">
                      {p.status}
                    </span>
                    <ArrowUpRight className="w-4 h-4 text-slate-500 group-hover:text-indigo-400 transition-colors" />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Live Processing Queue */}
        <div className="space-y-4">
          <h2 className="text-lg font-bold text-white">Job Monitor</h2>
          <div className="p-4 rounded-xl bg-studio-900 border border-studio-800 space-y-4">
            {recentJobs.length === 0 ? (
              <p className="text-xs text-slate-500 py-6 text-center">No recent jobs logged</p>
            ) : (
              recentJobs.slice(0, 4).map(job => (
                <div key={job.id} className="p-3 rounded-lg bg-studio-850 border border-studio-800 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-200">{job.job_type}</span>
                    <span className={`px-2 py-0.5 rounded font-mono text-[10px] ${
                      job.status === 'READY' ? 'bg-emerald-500/20 text-emerald-400' :
                      job.status === 'FAILED' ? 'bg-rose-500/20 text-rose-400' : 'bg-sky-500/20 text-sky-400'
                    }`}>
                      {job.status}
                    </span>
                  </div>
                  {/* Progress Bar */}
                  <div className="w-full bg-studio-950 rounded-full h-1.5 overflow-hidden">
                    <div
                      className={`h-full transition-all duration-300 ${job.status === 'FAILED' ? 'bg-rose-500' : 'bg-indigo-500'}`}
                      style={{ width: `${job.progress}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-[11px] text-slate-400 font-mono">
                    <span>{job.checkpoint_stage || 'INITIALIZING'}</span>
                    <span>{job.progress}%</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
