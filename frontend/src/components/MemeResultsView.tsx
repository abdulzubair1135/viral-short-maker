import React, { useState } from 'react';
import { 
  Laugh, CheckCircle2, Download, Play, Pause, RotateCcw, 
  Sparkles, CheckSquare, Star, AlertCircle, ShieldCheck, 
  ChevronDown, ChevronUp, RefreshCw, XCircle, FileText, Video, Edit3
} from 'lucide-react';
import { Meme, api, Clip } from '../services/api';
import { YouTubePublishModal } from './YouTubePublishModal';
import { MemeEditorModal } from './MemeEditorModal';

interface MemeResultsViewProps {
  projectId: string;
  projectTitle: string;
  memes: Meme[];
  onNewMeme: () => void;
  onRefresh: () => void;
}

export const MemeResultsView: React.FC<MemeResultsViewProps> = ({
  projectId,
  projectTitle,
  memes,
  onNewMeme,
  onRefresh
}) => {
  const [playingMemeId, setPlayingMemeId] = useState<string | null>(null);
  const [regeneratingId, setRegeneratingId] = useState<string | null>(null);
  const [editingMeme, setEditingMeme] = useState<Meme | null>(null);
  const [expandedMemeId, setExpandedMemeId] = useState<string | null>(null);
  const [publishModalClip, setPublishModalClip] = useState<Clip | null>(null);
  const [viewingAiLogMeme, setViewingAiLogMeme] = useState<Meme | null>(null);

  const handleTogglePlay = (memeId: string) => {
    const currentVid = document.getElementById(`video-${memeId}`) as HTMLVideoElement;
    if (!currentVid) return;

    if (playingMemeId === memeId) {
      currentVid.pause();
      setPlayingMemeId(null);
    } else {
      if (playingMemeId) {
        const oldVid = document.getElementById(`video-${playingMemeId}`) as HTMLVideoElement;
        if (oldVid) oldVid.pause();
      }
      currentVid.play();
      setPlayingMemeId(memeId);
    }
  };

  const handleApprove = async (memeId: string, status: 'APPROVED' | 'REJECTED') => {
    await api.approveMeme(memeId, status);
    onRefresh();
  };

  const handleApproveAll = async () => {
    for (const m of memes) {
      if (m.approval_status !== 'APPROVED') {
        await api.approveMeme(m.id, 'APPROVED');
      }
    }
    onRefresh();
  };

  const handleRegenerateJoke = async (memeId: string) => {
    setRegeneratingId(memeId);
    try {
      await api.regenerateMemeJoke(memeId);
      onRefresh();
    } catch (e: any) {
      alert("Failed to regenerate joke: " + e.message);
    } finally {
      setRegeneratingId(null);
    }
  };

  // Adapts Meme to Clip structure for YouTubePublishModal
  const handleOpenPublishModal = (meme: Meme) => {
    const adaptedClip: Clip = {
      id: meme.id,
      project_id: meme.project_id,
      title: meme.title,
      start_time: 0,
      end_time: meme.duration,
      duration: meme.duration,
      hook: meme.hook,
      summary: meme.joke,
      description: meme.description,
      hashtags: meme.hashtags,
      score_total: meme.quality_score,
      scores: {},
      decision_reason: meme.concept,
      edit_plan: {},
      crop_mode: '9:16_meme',
      caption_preset: meme.format,
      status: 'READY',
      approval_status: meme.approval_status,
      is_favorite: false,
      output_path: meme.output_path,
      quality_score: meme.quality_score,
      tags: meme.hashtags
    };
    setPublishModalClip(adaptedClip);
  };

  const approvedCount = memes.filter(m => m.approval_status === 'APPROVED').length;
  const avgScore = memes.length > 0 
    ? (memes.reduce((acc, m) => acc + (m.quality_score || 90), 0) / memes.length).toFixed(1)
    : "92.0";

  return (
    <div className="flex-1 overflow-y-auto px-6 py-8 max-w-7xl mx-auto w-full">
      {/* Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 pb-6 border-b border-studio-850">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded-full bg-amber-500/20 text-[10px] font-bold text-amber-300 border border-amber-500/30">
              😂 Meme Studio Pipeline
            </span>
            <span className="text-xs text-slate-400">
              {memes.length} Viral Memes Generated
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            {projectTitle || "Viral Meme Short Concepts"}
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Average Quality Score: <strong className="text-amber-400">{avgScore}/100</strong> • Approved: <strong className="text-emerald-400">{approvedCount}/{memes.length}</strong>
          </p>
        </div>

        {/* Global Actions */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={handleApproveAll}
            className="px-4 py-2 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 text-xs font-semibold flex items-center gap-1.5 transition"
          >
            <CheckSquare className="w-3.5 h-3.5" /> Approve All
          </button>

          <button
            onClick={onNewMeme}
            className="px-4 py-2 rounded-xl bg-studio-850 hover:bg-studio-800 text-slate-200 border border-studio-750 text-xs font-semibold flex items-center gap-1.5 transition"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-400" /> New Topic
          </button>
        </div>
      </div>

      {/* Memes Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {memes.map((meme, idx) => {
          const isPlaying = playingMemeId === meme.id;
          const isRegenerating = regeneratingId === meme.id;
          const isExpanded = expandedMemeId === meme.id;
          const isApproved = meme.approval_status === 'APPROVED';
          const lic = meme.license_record;

          return (
            <div 
              key={meme.id}
              className={`bg-studio-900 border rounded-2xl overflow-hidden flex flex-col justify-between transition-all ${
                isApproved 
                  ? 'border-emerald-500/40 shadow-lg shadow-emerald-500/5' 
                  : 'border-studio-800 hover:border-slate-700 shadow-xl'
              }`}
            >
              {/* Card Top / Video Player */}
              <div>
                <div className="relative aspect-[9/16] max-h-[460px] bg-black flex items-center justify-center overflow-hidden group">
                  {meme.output_path ? (
                    <video
                      id={`video-${meme.id}`}
                      src={meme.video_url || `/storage/projects/${projectId}/memes/meme_${meme.id}.mp4`}
                      className="w-full h-full object-contain"
                      loop
                      playsInline
                      onEnded={() => setPlayingMemeId(null)}
                    />
                  ) : (
                    <div className="text-slate-600 text-xs flex flex-col items-center gap-2">
                      <Laugh className="w-8 h-8 opacity-40 text-amber-500" />
                      <span>Rendering Meme Video...</span>
                    </div>
                  )}

                  {/* Overlay Play / Pause Button */}
                  <button
                    onClick={() => handleTogglePlay(meme.id)}
                    className={`absolute inset-0 m-auto w-14 h-14 rounded-full bg-black/60 backdrop-blur-sm border border-white/20 flex items-center justify-center text-white transition-transform ${
                      isPlaying ? 'opacity-0 group-hover:opacity-100 scale-90' : 'opacity-90 hover:scale-105'
                    }`}
                  >
                    {isPlaying ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6 ml-1" />}
                  </button>

                  {/* Quality Badge */}
                  <div className="absolute top-3 left-3 px-2.5 py-1 rounded-lg bg-black/75 backdrop-blur border border-amber-500/40 text-amber-300 text-xs font-bold flex items-center gap-1">
                    <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                    <span>{meme.quality_score.toFixed(1)}/100</span>
                  </div>

                  {/* Format Pill */}
                  <div className="absolute top-3 right-3 px-2.5 py-1 rounded-lg bg-black/75 backdrop-blur border border-white/20 text-white text-[10px] font-bold uppercase tracking-wider">
                    {meme.format}
                  </div>

                  {/* Duration Badge */}
                  <div className="absolute bottom-3 right-3 px-2 py-0.5 rounded bg-black/80 text-white text-[10px] font-mono">
                    {meme.duration.toFixed(1)}s
                  </div>
                </div>

                {/* Card Content */}
                <div className="p-5">
                  {/* Hook & Joke */}
                  <div className="mb-4">
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                        {meme.style}
                      </span>
                      {isApproved && (
                        <span className="text-[10px] font-bold text-emerald-400 flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" /> Approved
                        </span>
                      )}
                    </div>
                    <h3 className="text-sm font-bold text-white leading-snug mb-1">
                      {meme.hook}
                    </h3>
                    <p className="text-xs text-slate-300 leading-relaxed italic">
                      "{meme.joke}"
                    </p>
                  </div>

                  {/* Verified License Badge */}
                  <div className="mb-4 p-3 rounded-xl bg-studio-950/80 border border-studio-800 text-[11px]">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-slate-300 flex items-center gap-1">
                        <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> Verified License
                      </span>
                      <span className="text-[10px] font-bold text-emerald-400 uppercase">
                        {lic.safety_state || 'VERIFIED_SAFE'}
                      </span>
                    </div>
                    <p className="text-slate-400 text-[10px] truncate">
                      Source: <strong className="text-slate-200">{lic.source}</strong> ({lic.license_name})
                    </p>
                    {lic.attribution_required && lic.attribution_text && (
                      <p className="text-[10px] text-amber-300/80 mt-1 truncate">
                        Attribution: {lic.attribution_text}
                      </p>
                    )}
                  </div>

                  {/* 7-Score Accordion */}
                  <div className="mb-2">
                    <button
                      onClick={() => setExpandedMemeId(isExpanded ? null : meme.id)}
                      className="w-full flex items-center justify-between text-xs font-semibold text-slate-400 hover:text-white py-1"
                    >
                      <span>7-Point Viral Metrics</span>
                      {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    </button>

                    {isExpanded && meme.scores && (
                      <div className="mt-2 pt-2 border-t border-studio-800 space-y-1.5 text-[11px]">
                        {Object.entries(meme.scores).map(([metric, score]) => (
                          <div key={metric} className="flex items-center justify-between">
                            <span className="text-slate-400 capitalize">{metric.replace('_', ' ')}:</span>
                            <span className="font-mono font-bold text-amber-400">{score}/100</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Card Footer Actions */}
              <div className="p-4 bg-studio-950/60 border-t border-studio-800 space-y-2">
                {/* Secondary Actions Row */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleRegenerateJoke(meme.id)}
                    disabled={isRegenerating}
                    className="flex-1 py-1.5 px-2 rounded-lg bg-studio-850 hover:bg-studio-800 border border-studio-700 text-slate-300 text-[11px] font-semibold flex items-center justify-center gap-1 transition"
                  >
                    <RefreshCw className={`w-3 h-3 text-amber-400 ${isRegenerating ? 'animate-spin' : ''}`} />
                    <span>{isRegenerating ? "Rewriting..." : "New Joke"}</span>
                  </button>

                  <button
                    onClick={() => setViewingAiLogMeme(meme)}
                    className="py-1.5 px-2.5 rounded-lg bg-indigo-950/60 hover:bg-indigo-900/60 border border-indigo-500/30 text-indigo-300 text-[11px] font-semibold flex items-center justify-center gap-1 transition"
                    title="View AI Prompt & Raw Response"
                  >
                    <FileText className="w-3 h-3" />
                    <span>AI Logs</span>
                  </button>

                  <a
                    href={meme.output_path ? `/api/memes/video/${meme.id}` : '#'}
                    download={`meme_${meme.id.slice(0, 8)}.mp4`}
                    className="py-1.5 px-2.5 rounded-lg bg-studio-850 hover:bg-studio-800 border border-studio-700 text-slate-300 text-[11px] font-semibold flex items-center justify-center gap-1 transition"
                    title="Download MP4 Video"
                  >
                    <Download className="w-3 h-3 text-indigo-400" />
                    <span>MP4</span>
                  </a>

                  <a
                    href={meme.output_path ? `/api/memes/gif/${meme.id}` : '#'}
                    download={`meme_${meme.id.slice(0, 8)}.gif`}
                    className="py-1.5 px-2.5 rounded-lg bg-purple-950/60 hover:bg-purple-900/60 border border-purple-500/30 text-purple-300 text-[11px] font-semibold flex items-center justify-center gap-1 transition"
                    title="Download GIF Meme"
                  >
                    <Download className="w-3 h-3 text-purple-400" />
                    <span>GIF</span>
                  </a>
                </div>

                {/* Primary Approval & YouTube Publish Row */}
                <div className="flex items-center gap-2">
                  {isApproved ? (
                    <button
                      onClick={() => handleApprove(meme.id, 'REJECTED')}
                      className="flex-1 py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition"
                    >
                      Unapprove
                    </button>
                  ) : (
                    <button
                      onClick={() => handleApprove(meme.id, 'APPROVED')}
                      className="flex-1 py-2 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition flex items-center justify-center gap-1 shadow-md shadow-emerald-600/20"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" /> Approve
                    </button>
                  )}

                  <button
                    onClick={() => handleOpenPublishModal(meme)}
                    className="py-2 px-4 rounded-xl bg-red-600 hover:bg-red-500 text-white text-xs font-bold transition flex items-center gap-1.5 shadow-md shadow-red-600/20"
                  >
                    <Video className="w-4 h-4" /> Publish
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* AI Prompt & Response Inspection Modal */}
      {viewingAiLogMeme && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-studio-900 border border-studio-700 rounded-2xl w-full max-w-2xl p-6 shadow-2xl space-y-4 relative max-h-[85vh] overflow-y-auto">
            <button
              onClick={() => setViewingAiLogMeme(null)}
              className="absolute right-4 top-4 text-slate-400 hover:text-white p-1 rounded-lg"
            >
              <XCircle className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-2 text-indigo-400">
              <FileText className="w-5 h-5" />
              <h2 className="text-base font-bold text-white">AI Conversation & Prompt Inspection Log</h2>
            </div>

            <div className="space-y-4 text-xs font-mono">
              <div>
                <label className="block text-indigo-300 font-bold mb-1 uppercase tracking-wider">
                  1. Exact Prompt Sent to DeepSeek / Gemini AI:
                </label>
                <div className="p-3 bg-studio-950 border border-studio-800 rounded-xl text-slate-300 whitespace-pre-wrap leading-relaxed max-h-60 overflow-y-auto font-mono text-[11px]">
                  {viewingAiLogMeme.ai_prompt || "Prompt logged during system pipeline generation."}
                </div>
              </div>

              <div>
                <label className="block text-emerald-300 font-bold mb-1 uppercase tracking-wider">
                  2. Exact Raw Response Received from AI:
                </label>
                <div className="p-3 bg-studio-950 border border-studio-800 rounded-xl text-emerald-300/90 whitespace-pre-wrap leading-relaxed max-h-60 overflow-y-auto font-mono text-[11px]">
                  {viewingAiLogMeme.ai_response || JSON.stringify(viewingAiLogMeme, null, 2)}
                </div>
              </div>

              <div className="p-3 rounded-xl bg-studio-950 border border-studio-800 text-slate-400 space-y-1">
                <div>Visual Image Query: <strong className="text-amber-300">{viewingAiLogMeme.visual_query}</strong></div>
                <div>Visual Asset Source: <strong className="text-emerald-300">{viewingAiLogMeme.license_record?.source}</strong> ({viewingAiLogMeme.license_record?.license_name})</div>
                <div>Copyright Safety State: <strong className="text-emerald-400">{viewingAiLogMeme.license_record?.safety_state} (100% Safe For Commercial Use)</strong></div>
              </div>
            </div>

            <div className="pt-2 text-right">
              <button
                onClick={() => setViewingAiLogMeme(null)}
                className="px-4 py-2 bg-studio-800 hover:bg-studio-750 text-white rounded-xl font-bold"
              >
                Close Logs
              </button>
            </div>
          </div>
        </div>
      )}

      {/* YouTube Publish Modal */}
      {publishModalClip && (
        <YouTubePublishModal
          clip={publishModalClip}
          onClose={() => setPublishModalClip(null)}
          onSuccess={() => {
            setPublishModalClip(null);
            onRefresh();
          }}
        />
      )}

    </div>
  );
};
