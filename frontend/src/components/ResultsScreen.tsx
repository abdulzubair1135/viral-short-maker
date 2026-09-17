import React, { useState, useEffect } from 'react';
import { 
  CheckCircle2, Download, Sliders, Play, Pause, Video, 
  RotateCcw, Sparkles, CheckSquare, Film, Star, AlertCircle, 
  Filter, ChevronDown, ChevronUp, Mic, RefreshCw, XCircle, FileText
} from 'lucide-react';
import { Clip, RejectedCandidate, api } from '../services/api';
import { YouTubePublishModal } from './YouTubePublishModal';

interface ResultsScreenProps {
  projectId: string;
  clips: Clip[];
  onOpenEditor: (clip: Clip) => void;
  onNewVideo: () => void;
  onRefresh: () => void;
}

export const ResultsScreen: React.FC<ResultsScreenProps> = ({ 
  projectId, 
  clips, 
  onOpenEditor, 
  onNewVideo,
  onRefresh
}) => {
  const [playingClipId, setPlayingClipId] = useState<string | null>(null);
  const [publishModalClip, setPublishModalClip] = useState<Clip | null>(null);
  const [isApprovingAll, setIsApprovingAll] = useState(false);
  const [activeTab, setActiveTab] = useState<'shorts' | 'rejected'>('shorts');
  const [rejectedCandidates, setRejectedCandidates] = useState<RejectedCandidate[]>([]);
  const [expandedAnalysisId, setExpandedAnalysisId] = useState<string | null>(null);
  const [regeneratingClipId, setRegeneratingClipId] = useState<string | null>(null);

  useEffect(() => {
    if (projectId) {
      api.getRejectedCandidates(projectId)
        .then(res => {
          setRejectedCandidates(res.rejected_candidates || []);
        })
        .catch(err => console.warn("Failed to load rejected candidates:", err));
    }
  }, [projectId]);

  const handleApprove = async (clipId: string) => {
    await api.approveClip(clipId);
    onRefresh();
  };

  const handleApproveAll = async () => {
    setIsApprovingAll(true);
    try {
      const ids = clips.map(c => c.id);
      await api.batchAction('approve', ids);
      onRefresh();
    } finally {
      setIsApprovingAll(false);
    }
  };

  const handleRegenerateCommentary = async (clipId: string) => {
    setRegeneratingClipId(clipId);
    try {
      await api.regenerateCommentary(clipId);
      onRefresh();
    } finally {
      setRegeneratingClipId(null);
    }
  };

  const handleRegenerateMetadata = async (clipId: string) => {
    setRegeneratingClipId(clipId);
    try {
      await api.regenerateMetadata(clipId);
      onRefresh();
    } finally {
      setRegeneratingClipId(null);
    }
  };

  const handleTogglePlay = (clipId: string) => {
    const currentVid = document.getElementById(`video-${clipId}`) as HTMLVideoElement;
    if (!currentVid) return;

    if (!currentVid.paused) {
      currentVid.pause();
      setPlayingClipId(null);
      return;
    }

    // Pause all other videos
    clips.forEach(c => {
      if (c.id !== clipId) {
        const otherVid = document.getElementById(`video-${c.id}`) as HTMLVideoElement;
        if (otherVid && !otherVid.paused) {
          otherVid.pause();
        }
      }
    });

    currentVid.play().then(() => {
      setPlayingClipId(clipId);
    }).catch(err => {
      console.warn("Autoplay/play failed:", err);
    });
  };

  return (
    <div className="flex-1 overflow-y-auto h-full p-6 sm:p-10 max-w-6xl mx-auto space-y-6 animate-in fade-in duration-300">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-studio-800">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold uppercase tracking-wider">
            <CheckCircle2 className="w-4 h-4" /> Transformative Review Shorts Ready
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">
            Curated Review & Analysis Shorts 🎉
          </h1>
          <p className="text-xs text-slate-400 font-mono">
            AI generated <span className="text-indigo-400 font-bold">{clips.length} transformative review Shorts</span> with commentary narration and evaluated <span className="text-amber-400 font-bold">{rejectedCandidates.length} filtered moments</span>.
          </p>
        </div>

        {/* Global Batch Controls */}
        <div className="flex items-center gap-3">
          <button
            onClick={onNewVideo}
            className="px-4 py-2 rounded-xl bg-studio-850 hover:bg-studio-800 text-slate-300 text-xs font-medium border border-studio-700/60 transition"
          >
            + New Video
          </button>
          <button
            onClick={handleApproveAll}
            disabled={isApprovingAll}
            className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-600/20 transition flex items-center gap-1.5"
          >
            <CheckSquare className="w-3.5 h-3.5" /> Approve All
          </button>
          <a
            href={`/api/projects/${projectId}/export_bundle`}
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5" /> Export All (.acs)
          </a>
        </div>
      </div>

      {/* Mandatory Fair Use & Transformative Policy Disclaimer */}
      <div className="rounded-2xl border border-amber-500/25 bg-amber-500/10 p-4 flex items-start gap-3.5 text-xs text-amber-200/90 shadow-lg">
        <AlertCircle className="w-5 h-5 text-amber-400 mt-0.5 shrink-0" />
        <div className="space-y-1 leading-relaxed">
          <span className="font-bold text-amber-300 uppercase tracking-wide text-[11px]">Transformative Review & Commentary Notice:</span>
          <p className="text-amber-200/80">
            These Shorts feature original commentary, critical breakdown, and analysis to establish fair-use transformative context. Transformative structure does not automatically guarantee copyright immunity or YouTube monetization clearance. Always ensure you hold necessary permissions from the original creator.
          </p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center justify-between border-b border-studio-800 pb-3">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab('shorts')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
              activeTab === 'shorts'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/25'
                : 'bg-studio-850 text-slate-400 hover:text-white border border-studio-700/50'
            }`}
          >
            <Film className="w-3.5 h-3.5" /> Created Review Shorts ({clips.length})
          </button>
          <button
            onClick={() => setActiveTab('rejected')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
              activeTab === 'rejected'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/25'
                : 'bg-studio-850 text-slate-400 hover:text-white border border-studio-700/50'
            }`}
          >
            <Filter className="w-3.5 h-3.5" /> Filtered Moments Inspector ({rejectedCandidates.length})
          </button>
        </div>
      </div>

      {/* TAB 1: Created Review Shorts Grid */}
      {activeTab === 'shorts' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {clips.map((clip, idx) => {
            const isPlaying = playingClipId === clip.id;
            const isApproved = clip.approval_status === 'APPROVED';
            const isExpanded = expandedAnalysisId === clip.id;
            const isRegenerating = regeneratingClipId === clip.id;
            const ratingScore = clip.rating || ((clip.score_total || 85) / 10);
            const verdictText = clip.verdict || clip.analysis?.verdict || "High Retention Moment";
            const ratingLabel = clip.analysis?.rating_label || "RECOMMENDED";

            return (
              <div
                key={clip.id}
                className={`rounded-2xl bg-studio-900 border transition-all flex flex-col justify-between overflow-hidden shadow-xl ${
                  isApproved ? 'border-emerald-500/40 bg-emerald-950/10' : 'border-studio-800 hover:border-studio-700'
                }`}
              >
                {/* 9:16 Video Player Container */}
                <div 
                  onClick={() => handleTogglePlay(clip.id)}
                  className="relative aspect-[9/16] bg-black max-h-[380px] overflow-hidden group cursor-pointer"
                >
                  <video
                    id={`video-${clip.id}`}
                    src={`/storage/projects/${clip.project_id || projectId}/clip_${clip.id}.mp4#t=0.001`}
                    className="w-full h-full object-cover"
                    preload="metadata"
                    playsInline
                    onPlay={() => setPlayingClipId(clip.id)}
                    onPause={() => {
                      if (playingClipId === clip.id) setPlayingClipId(null);
                    }}
                    onEnded={() => setPlayingClipId(null)}
                  />

                  {/* Overlaid Rating & Review Badge */}
                  <div className="absolute top-3 left-3 right-3 flex items-center justify-between pointer-events-none z-10">
                    <span className="px-2 py-0.5 rounded-md bg-black/75 backdrop-blur text-white text-[10px] font-bold font-mono border border-white/10">
                      Short #{idx + 1}
                    </span>
                    <span className="px-2.5 py-0.5 rounded-full bg-amber-500 text-black text-xs font-black font-mono shadow-lg flex items-center gap-1">
                      <Star className="w-3 h-3 fill-black" /> {ratingScore.toFixed(1)}/10 • {ratingLabel}
                    </span>
                  </div>

                  {/* Play/Pause Button Icon Overlay */}
                  {!isPlaying ? (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/20 hover:bg-black/35 transition pointer-events-none">
                      <div className="w-14 h-14 rounded-full bg-indigo-600/90 group-hover:bg-indigo-500 text-white flex items-center justify-center shadow-xl group-hover:scale-110 transition border border-white/20">
                        <Play className="w-6 h-6 ml-1 fill-white" />
                      </div>
                    </div>
                  ) : (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/30 opacity-0 group-hover:opacity-100 transition pointer-events-none">
                      <div className="w-14 h-14 rounded-full bg-black/70 text-white flex items-center justify-center shadow-xl border border-white/20">
                        <Pause className="w-6 h-6" />
                      </div>
                    </div>
                  )}

                  {/* Duration & Commentary Badge */}
                  <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between pointer-events-none z-10 text-[10px] font-mono">
                    <span className="px-2 py-0.5 rounded bg-indigo-950/90 text-indigo-300 border border-indigo-500/30 flex items-center gap-1">
                      <Mic className="w-3 h-3 text-indigo-400" /> AI Commentary
                    </span>
                    <span className="px-2 py-0.5 rounded bg-black/80 text-slate-200">
                      {clip.duration.toFixed(1)}s
                    </span>
                  </div>
                </div>

                {/* Clip Metadata & Review Breakdown */}
                <div className="p-4 space-y-3 flex-1 flex flex-col justify-between">
                  <div className="space-y-2">
                    {/* Verdict Banner */}
                    <div className="px-2.5 py-1 rounded-lg bg-studio-800/80 border border-studio-700/60 flex items-center justify-between">
                      <span className="text-[10px] uppercase font-bold text-amber-400 tracking-wide">
                        Verdict
                      </span>
                      <span className="text-xs font-semibold text-slate-200 truncate max-w-[190px]">
                        {verdictText}
                      </span>
                    </div>

                    <h3 className="text-sm font-bold text-white line-clamp-2 leading-snug">
                      {clip.title}
                    </h3>
                    <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                      {clip.description || clip.summary}
                    </p>

                    {/* Transformative Analysis Breakdown Accordion */}
                    <div className="pt-1">
                      <button
                        onClick={() => setExpandedAnalysisId(isExpanded ? null : clip.id)}
                        className="w-full py-1 text-[11px] font-semibold text-indigo-400 hover:text-indigo-300 flex items-center justify-between border-t border-studio-800/60"
                      >
                        <span className="flex items-center gap-1">
                          <FileText className="w-3 h-3" /> Transformative Analysis Breakdown
                        </span>
                        {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                      </button>

                      {isExpanded && clip.analysis && (
                        <div className="mt-2 p-2.5 rounded-xl bg-studio-950 border border-studio-800 space-y-2 text-[11px] animate-in fade-in">
                          {clip.analysis.fact_or_opinion && (
                            <div className="flex items-center gap-1.5">
                              <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase ${
                                clip.analysis.fact_or_opinion === 'fact' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-purple-500/20 text-purple-300'
                              }`}>
                                {clip.analysis.fact_or_opinion}
                              </span>
                              <span className="text-slate-300 text-[10px]">{clip.analysis.claim_or_event}</span>
                            </div>
                          )}
                          {clip.analysis.commentary && (
                            <div>
                              <span className="font-bold text-slate-400">Commentary: </span>
                              <span className="text-slate-300">{clip.analysis.commentary}</span>
                            </div>
                          )}
                          {clip.analysis.counterpoint && (
                            <div>
                              <span className="font-bold text-amber-400/90">Counterpoint: </span>
                              <span className="text-slate-300">{clip.analysis.counterpoint}</span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    <div className="flex flex-wrap gap-1 text-[10px] text-indigo-400 font-mono">
                      {((clip.hashtags && clip.hashtags.length > 0) ? clip.hashtags : (clip.tags && clip.tags.length > 0) ? clip.tags : ['#shorts', '#review']).slice(0, 3).map((tag, i) => (
                        <span key={i}>{typeof tag === 'string' && tag.startsWith('#') ? tag : `#${tag}`}</span>
                      ))}
                    </div>
                  </div>

                  {/* Card Actions & Regeneration Controls */}
                  <div className="pt-3 border-t border-studio-800/80 space-y-2">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleRegenerateCommentary(clip.id)}
                        disabled={isRegenerating}
                        className="flex-1 py-1 rounded-lg bg-studio-850 hover:bg-studio-800 text-slate-300 text-[10px] font-semibold border border-studio-700/60 transition flex items-center justify-center gap-1"
                        title="Regenerate critical commentary and rating"
                      >
                        <RefreshCw className={`w-3 h-3 ${isRegenerating ? 'animate-spin' : ''}`} /> Commentary
                      </button>
                      <button
                        onClick={() => handleRegenerateMetadata(clip.id)}
                        disabled={isRegenerating}
                        className="flex-1 py-1 rounded-lg bg-studio-850 hover:bg-studio-800 text-slate-300 text-[10px] font-semibold border border-studio-700/60 transition flex items-center justify-center gap-1"
                        title="Regenerate viral title and hashtags"
                      >
                        <Sparkles className="w-3 h-3 text-amber-400" /> Metadata
                      </button>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => onOpenEditor(clip)}
                        className="flex-1 py-1.5 rounded-xl bg-studio-800 hover:bg-studio-700 text-slate-200 text-xs font-semibold transition flex items-center justify-center gap-1.5"
                      >
                        <Sliders className="w-3.5 h-3.5" /> Edit
                      </button>

                      <button
                        onClick={() => handleApprove(clip.id)}
                        className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition flex items-center gap-1 ${
                          isApproved
                            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                            : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-md'
                        }`}
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" /> {isApproved ? 'Approved' : 'Approve'}
                      </button>
                    </div>

                    <div className="flex items-center gap-2">
                      <a
                        href={`/api/clips/${clip.id}/download`}
                        className="flex-1 py-1.5 rounded-xl bg-studio-850 hover:bg-studio-800 text-slate-300 text-xs font-medium transition text-center flex items-center justify-center gap-1 border border-studio-700/60"
                      >
                        <Download className="w-3.5 h-3.5" /> Download MP4
                      </a>

                      <button
                        onClick={() => setPublishModalClip(clip)}
                        className="px-3.5 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold shadow-md shadow-rose-600/25 transition flex items-center gap-1.5"
                        title="Publish directly to YouTube Shorts"
                      >
                        <Video className="w-3.5 h-3.5" /> Upload to YT
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* TAB 2: Filtered / Rejected Moments Inspector */}
      {activeTab === 'rejected' && (
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-studio-900 border border-studio-800 text-xs text-slate-300 space-y-1">
            <span className="font-bold text-white">AI Candidate Filtering Diagnostics:</span>
            <p className="text-slate-400">
              The AI evaluated moments across 8 scores (hook, interest, commentary potential, standalone clarity, context depth, and originality). Moments lacking commentary depth, sponsor segments, or greeting filler were safely rejected to maintain premium production quality.
            </p>
          </div>

          {rejectedCandidates.length === 0 ? (
            <div className="p-12 text-center text-slate-500 text-xs border border-dashed border-studio-800 rounded-2xl">
              No moments were rejected for this project.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {rejectedCandidates.map((rj, idx) => (
                <div key={idx} className="p-4 rounded-2xl bg-studio-900 border border-studio-800 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-white flex items-center gap-1.5">
                      <XCircle className="w-4 h-4 text-rose-400" /> {rj.title}
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-studio-800 text-slate-300">
                      {rj.start_time.toFixed(1)}s - {rj.end_time.toFixed(1)}s ({rj.duration.toFixed(1)}s)
                    </span>
                  </div>

                  {rj.claim && (
                    <p className="text-xs text-slate-400">
                      <span className="font-semibold text-slate-300">Segment Content:</span> {rj.claim}
                    </p>
                  )}

                  <div className="p-2.5 rounded-xl bg-rose-950/20 border border-rose-500/20 text-xs text-rose-300 space-y-1">
                    <span className="font-bold text-rose-400 text-[10px] uppercase tracking-wide">
                      Rejection Reason:
                    </span>
                    <p className="text-rose-200/90 leading-relaxed">
                      {rj.rejection_reason || rj.reason || "Low commentary potential and insufficient standalone context."}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* YouTube Publish Review Modal */}
      {publishModalClip && (
        <YouTubePublishModal
          clip={publishModalClip}
          onClose={() => setPublishModalClip(null)}
          onSuccess={onRefresh}
        />
      )}
    </div>
  );
};

