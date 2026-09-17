import React, { useEffect, useState } from 'react';
import { Clock, RefreshCw, AlertCircle, CheckCircle2, RotateCcw, FileText, ChevronRight } from 'lucide-react';
import { api, Job } from '../services/api';

export const JobQueueView: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);

  const fetchJobs = async () => {
    try {
      const data = await api.getJobs();
      setJobs(data);
      if (data.length > 0 && !selectedJob) {
        setSelectedJob(data[0]);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleResume = async (jobId: string) => {
    try {
      await api.resumeJob(jobId);
      fetchJobs();
      alert("Resumed job from last valid checkpoint!");
    } catch (err) {
      alert("Failed to resume job: " + err);
    }
  };

  return (
    <div className="p-8 space-y-6 max-w-6xl mx-auto overflow-y-auto h-full">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Clock className="w-5 h-5 text-indigo-400" /> Job Queue & Error Center
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Asynchronous task pipeline with stage checkpointing and crash recovery.
          </p>
        </div>
        <button
          onClick={fetchJobs}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-studio-850 hover:bg-studio-800 text-slate-200 text-xs font-medium border border-studio-700/60"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Jobs List */}
        <div className="lg:col-span-1 space-y-3">
          {jobs.length === 0 ? (
            <div className="p-8 text-center rounded-xl bg-studio-900 border border-studio-800 text-slate-500 text-xs">
              No jobs in queue
            </div>
          ) : (
            jobs.map(j => (
              <div
                key={j.id}
                onClick={() => setSelectedJob(j)}
                className={`p-4 rounded-xl border transition-all cursor-pointer flex flex-col space-y-2 ${
                  selectedJob?.id === j.id
                    ? 'bg-studio-850 border-indigo-500 shadow-md'
                    : 'bg-studio-900 border-studio-800 hover:border-studio-700'
                }`}
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-white">{j.job_type}</span>
                  <span className={`px-2 py-0.5 rounded font-mono text-[10px] ${
                    j.status === 'READY' ? 'bg-emerald-500/20 text-emerald-400' :
                    j.status === 'FAILED' ? 'bg-rose-500/20 text-rose-400' : 'bg-sky-500/20 text-sky-400'
                  }`}>
                    {j.status}
                  </span>
                </div>

                <div className="w-full bg-studio-950 rounded-full h-1.5 overflow-hidden">
                  <div
                    className={`h-full ${j.status === 'FAILED' ? 'bg-rose-500' : 'bg-indigo-500'}`}
                    style={{ width: `${j.progress}%` }}
                  />
                </div>

                <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                  <span>{j.checkpoint_stage || 'QUEUED'}</span>
                  <span>{j.progress}%</span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Selected Job Details & Error Center */}
        <div className="lg:col-span-2">
          {selectedJob ? (
            <div className="p-6 rounded-2xl bg-studio-900 border border-studio-800 space-y-5 shadow-xl">
              <div className="flex items-center justify-between pb-4 border-b border-studio-800">
                <div>
                  <h2 className="text-base font-bold text-white">{selectedJob.job_type}</h2>
                  <p className="text-xs text-slate-500 font-mono mt-0.5">Job ID: {selectedJob.id}</p>
                </div>

                {selectedJob.status === 'FAILED' && (
                  <button
                    onClick={() => handleResume(selectedJob.id)}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md transition"
                  >
                    <RotateCcw className="w-3.5 h-3.5" /> Resume from Checkpoint
                  </button>
                )}
              </div>

              {/* Error Center Alert */}
              {selectedJob.status === 'FAILED' && selectedJob.error_message && (
                <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/30 text-xs text-rose-200 space-y-2">
                  <div className="flex items-center gap-2 font-bold text-rose-400">
                    <AlertCircle className="w-4 h-4" /> Failure Diagnostic
                  </div>
                  <p className="font-mono">{selectedJob.error_message}</p>
                  <p className="text-[11px] text-rose-300/80">
                    The pipeline checkpoint has been preserved. You can resume processing directly from this stage or retry using a secondary AI provider.
                  </p>
                </div>
              )}

              {/* Logs */}
              <div className="space-y-2">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-300">
                  <FileText className="w-3.5 h-3.5" /> Execution Logs
                </div>
                <div className="p-4 rounded-xl bg-studio-950 border border-studio-850 font-mono text-[11px] text-slate-300 h-64 overflow-y-auto whitespace-pre-wrap leading-relaxed">
                  {selectedJob.logs || "No logs recorded for this job."}
                </div>
              </div>
            </div>
          ) : (
            <div className="p-12 text-center text-slate-500 text-xs">
              Select a job to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
