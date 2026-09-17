import React, { useState, useEffect } from 'react';
import { 
  Video, CheckCircle2, Film, Laugh, ArrowUpRight, 
  ExternalLink, Sparkles, Star, AlertCircle, RefreshCw, Eye
} from 'lucide-react';
import { api, Project, Clip, Meme } from '../services/api';
import { YouTubePublishModal } from './YouTubePublishModal';

export const PublishingView: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [approvedItems, setApprovedItems] = useState<Array<{
    id: string;
    type: 'CREATOR_REVIEW' | 'MEME_STUDIO';
    projectName: string;
    title: string;
    description: string;
    hashtags: string[];
    duration: number;
    score: number;
    output_path: string;
    video_url: string;
    original: Clip | Meme;
  }>>([]);

  const [publishModalClip, setPublishModalClip] = useState<Clip | null>(null);

  const fetchApproved = async () => {
    setLoading(true);
    try {
      const projects = await api.getProjects();
      const items: typeof approvedItems = [];

      for (const p of projects) {
        if (p.project_type === 'MEME_STUDIO') {
          try {
            const data = await api.getProjectMemes(p.id);
            for (const m of data.memes) {
              if (m.approval_status === 'APPROVED') {
                items.push({
                  id: m.id,
                  type: 'MEME_STUDIO',
                  projectName: p.name,
                  title: m.title,
                  description: m.description,
                  hashtags: m.hashtags,
                  duration: m.duration,
                  score: m.quality_score,
                  output_path: m.output_path,
                  video_url: m.video_url || `/api/memes/video/${m.id}`,
                  original: m
                });
              }
            }
          } catch (e) {
            console.warn(e);
          }
        } else {
          try {
            const clips = await api.getClips(p.id);
            for (const c of clips) {
              if (c.approval_status === 'APPROVED') {
                items.push({
                  id: c.id,
                  type: 'CREATOR_REVIEW',
                  projectName: p.name,
                  title: c.title,
                  description: c.description || c.summary,
                  hashtags: c.hashtags || [],
                  duration: c.duration,
                  score: c.quality_score || c.score_total,
                  output_path: c.output_path || '',
                  video_url: `/storage/projects/${p.id}/work/clip_${c.id}.mp4`,
                  original: c
                });
              }
            }
          } catch (e) {
            console.warn(e);
          }
        }
      }

      setApprovedItems(items);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApproved();
  }, []);

  const handlePublish = (item: typeof approvedItems[0]) => {
    const adapted: Clip = {
      id: item.id,
      project_id: (item.original as any).project_id,
      title: item.title,
      start_time: 0,
      end_time: item.duration,
      duration: item.duration,
      hook: item.title,
      summary: item.description,
      description: item.description,
      hashtags: item.hashtags,
      score_total: item.score,
      scores: {},
      decision_reason: item.projectName,
      edit_plan: {},
      crop_mode: '9:16',
      caption_preset: 'dynamic',
      status: 'READY',
      approval_status: 'APPROVED',
      is_favorite: false,
      output_path: item.output_path,
      quality_score: item.score,
      tags: item.hashtags
    };
    setPublishModalClip(adapted);
  };

  return (
    <div className="flex-1 overflow-y-auto px-6 py-8 max-w-6xl mx-auto w-full">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8 pb-6 border-b border-studio-850">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            <span className="text-xs font-bold text-red-400 uppercase tracking-wider">
              YouTube Publishing Control Center
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Approved Shorts Ready to Publish
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Review and publish approved videos across both Creator Review and Meme Studio pipelines.
          </p>
        </div>

        <button
          onClick={fetchApproved}
          className="px-4 py-2 rounded-xl bg-studio-900 hover:bg-studio-850 border border-studio-800 text-xs font-semibold text-slate-300 flex items-center gap-1.5 transition self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      {loading ? (
        <div className="py-20 text-center text-slate-500 text-xs flex flex-col items-center gap-3">
          <RefreshCw className="w-6 h-6 animate-spin text-red-500" />
          <span>Scanning approved videos...</span>
        </div>
      ) : approvedItems.length === 0 ? (
        <div className="py-20 text-center bg-studio-900/40 border border-studio-850 rounded-2xl p-8">
          <CheckCircle2 className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-bold text-white mb-1">No Approved Videos Yet</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
            When you approve clips in <strong>Creator Review</strong> or memes in <strong>Meme Studio</strong>, they will appear here ready for one-click publishing to YouTube.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {approvedItems.map((item) => (
            <div 
              key={item.id}
              className="bg-studio-900 border border-studio-800 hover:border-slate-700 rounded-2xl overflow-hidden flex flex-col justify-between shadow-xl"
            >
              <div>
                {/* 9:16 Video Preview */}
                <div className="relative aspect-[9/16] max-h-[380px] bg-black flex items-center justify-center overflow-hidden">
                  <video
                    src={item.video_url}
                    controls
                    className="w-full h-full object-contain"
                  />
                  <div className="absolute top-3 left-3 px-2 py-0.5 rounded bg-black/70 backdrop-blur text-[10px] font-bold text-white flex items-center gap-1">
                    <Star className="w-3 h-3 text-amber-400 fill-amber-400" />
                    <span>{item.score.toFixed(1)}/100</span>
                  </div>

                  <div className="absolute top-3 right-3 px-2 py-0.5 rounded bg-black/70 backdrop-blur text-[10px] font-bold text-white uppercase">
                    {item.type === 'MEME_STUDIO' ? '😂 Meme' : '🎬 Review'}
                  </div>
                </div>

                <div className="p-4">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1 truncate">
                    {item.projectName}
                  </span>
                  <h3 className="text-xs font-bold text-white mb-2 leading-snug line-clamp-2">
                    {item.title}
                  </h3>
                  <p className="text-[11px] text-slate-400 line-clamp-2 italic mb-2">
                    {item.description}
                  </p>
                </div>
              </div>

              <div className="p-4 pt-0">
                <button
                  onClick={() => handlePublish(item)}
                  className="w-full py-2.5 rounded-xl bg-red-600 hover:bg-red-500 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-red-600/20 transition"
                >
                  <Video className="w-4 h-4" />
                  <span>Publish to YouTube</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {publishModalClip && (
        <YouTubePublishModal
          clip={publishModalClip}
          onClose={() => setPublishModalClip(null)}
          onSuccess={() => {
            setPublishModalClip(null);
            fetchApproved();
          }}
        />
      )}

    </div>
  );
};
