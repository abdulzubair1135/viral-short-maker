import React, { useState } from 'react';
import { Sparkles, Upload, ChevronDown, ChevronUp, ShieldCheck, Film, ArrowRight, Video, Calendar, Clock, CheckCircle2 } from 'lucide-react';
import { api, Project } from '../services/api';

interface OneClickHomeProps {
  onStartPipeline: (urlOrPath: string, rightsConfirmed: boolean, options: any) => void;
  onSelectProject: (id: string) => void;
  recentProjects: Project[];
}

export const OneClickHome: React.FC<OneClickHomeProps> = ({ onStartPipeline, onSelectProject, recentProjects }) => {
  const [videoInput, setVideoInput] = useState('');
  const [rightsConfirmed, setRightsConfirmed] = useState(true);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Advanced options
  const [maxShorts, setMaxShorts] = useState(10);
  const [minDuration, setMinDuration] = useState(20);
  const [maxDuration, setMaxDuration] = useState(60);
  const [captionPreset, setCaptionPreset] = useState('dynamic');
  const [cropMode, setCropMode] = useState('speaker_tracking');
  const [aiProvider, setAiProvider] = useState('auto');

  const handleCreateShorts = (e: React.FormEvent) => {
    e.preventDefault();
    if (!videoInput.trim() || !rightsConfirmed || isSubmitting) return;

    setIsSubmitting(true);
    onStartPipeline(videoInput.trim(), rightsConfirmed, {
      max_shorts: maxShorts,
      min_duration: minDuration,
      max_duration: maxDuration,
      caption_preset: captionPreset,
      crop_mode: cropMode,
      ai_provider: aiProvider
    });
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // In desktop/browser context, set path or name
      const fakePath = (file as any).path || file.name;
      setVideoInput(fakePath);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto h-full flex flex-col justify-between p-6 sm:p-10 max-w-4xl mx-auto">
      {/* Top Hero Section */}
      <div className="text-center space-y-3 pt-6 sm:pt-12">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-400 text-xs font-semibold uppercase tracking-wider border border-indigo-500/20">
          <Sparkles className="w-3.5 h-3.5" /> AI Content Studio
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight">
          Turn one video into Shorts.
        </h1>
        <p className="text-sm text-slate-400 max-w-lg mx-auto leading-relaxed">
          Paste your video link below. The AI analyzes your video, selects the best viral moments, reframes to 9:16, and generates animated captions.
        </p>
      </div>

      {/* Main Action Form */}
      <div className="my-8 space-y-6">
        <form onSubmit={handleCreateShorts} className="space-y-4">
          <div className="relative rounded-2xl bg-studio-900/90 border-2 border-studio-700/80 focus-within:border-indigo-500 shadow-2xl p-2 transition-all">
            <input
              type="text"
              placeholder="Paste YouTube URL or local video path (e.g. https://youtube.com/watch?v=...)"
              value={videoInput}
              onChange={e => setVideoInput(e.target.value)}
              className="w-full px-4 py-3 bg-transparent text-sm sm:text-base text-white placeholder-slate-500 focus:outline-none font-mono"
            />
          </div>

          {/* Compact Rights Confirmation */}
          <div className="flex items-center justify-center gap-2 text-xs text-slate-300">
            <input
              type="checkbox"
              id="rightsCheck"
              checked={rightsConfirmed}
              onChange={e => setRightsConfirmed(e.target.checked)}
              className="rounded bg-studio-900 border-studio-700 text-indigo-600 focus:ring-0 cursor-pointer w-4 h-4"
            />
            <label htmlFor="rightsCheck" className="cursor-pointer select-none">
              I own this content or have permission to repurpose it.
            </label>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
            <button
              type="submit"
              disabled={!videoInput.trim() || !rightsConfirmed || isSubmitting}
              className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:hover:bg-indigo-600 text-white font-bold text-sm tracking-wide uppercase transition shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2"
            >
              <Sparkles className="w-4 h-4" /> Create Shorts
            </button>

            <label className="w-full sm:w-auto px-5 py-3.5 rounded-xl bg-studio-850 hover:bg-studio-800 text-slate-300 text-xs font-semibold cursor-pointer border border-studio-700/60 transition flex items-center justify-center gap-2">
              <Upload className="w-4 h-4" /> Select Video File
              <input type="file" accept="video/*" onChange={handleFileSelect} className="hidden" />
            </label>
          </div>
        </form>

        {/* Collapsed Advanced Options */}
        <div className="text-center">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 font-medium transition"
          >
            {showAdvanced ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            Advanced Options
          </button>

          {showAdvanced && (
            <div className="mt-4 p-5 rounded-2xl bg-studio-900 border border-studio-800 text-left grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs animate-in fade-in duration-200">
              <div>
                <label className="block text-slate-400 mb-1">Max Shorts Limit</label>
                <input
                  type="number"
                  min="1"
                  max="15"
                  value={maxShorts}
                  onChange={e => setMaxShorts(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-lg bg-studio-950 border border-studio-800 text-white font-mono"
                />
                <span className="text-[10px] text-slate-500 mt-1 block">AI decides actual quality count</span>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Duration Limits</label>
                <div className="flex gap-2">
                  <input
                    type="number"
                    value={minDuration}
                    onChange={e => setMinDuration(Number(e.target.value))}
                    className="w-1/2 px-2 py-2 rounded-lg bg-studio-950 border border-studio-800 text-white font-mono"
                  />
                  <input
                    type="number"
                    value={maxDuration}
                    onChange={e => setMaxDuration(Number(e.target.value))}
                    className="w-1/2 px-2 py-2 rounded-lg bg-studio-950 border border-studio-800 text-white font-mono"
                  />
                </div>
                <span className="text-[10px] text-slate-500 mt-1 block">Min & Max seconds</span>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Caption Preset</label>
                <select
                  value={captionPreset}
                  onChange={e => setCaptionPreset(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-studio-950 border border-studio-800 text-white"
                >
                  <option value="dynamic">Dynamic Karaoke</option>
                  <option value="minimal">Minimal</option>
                  <option value="podcast">Podcast</option>
                  <option value="gaming">Gaming</option>
                  <option value="clean">Clean</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Crop Mode</label>
                <select
                  value={cropMode}
                  onChange={e => setCropMode(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-studio-950 border border-studio-800 text-white"
                >
                  <option value="speaker_tracking">Smart Speaker Tracking</option>
                  <option value="blur_background">Blurred Background</option>
                  <option value="center">Fixed Center</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">AI Provider Strategy</label>
                <select
                  value={aiProvider}
                  onChange={e => setAiProvider(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-studio-950 border border-studio-800 text-white"
                >
                  <option value="auto">Automatic (Gemini &rarr; ChatGPT &rarr; DeepSeek)</option>
                  <option value="gemini">Google Gemini Web</option>
                  <option value="chatgpt">ChatGPT Web</option>
                  <option value="deepseek">DeepSeek Web</option>
                  <option value="mock">Deterministic Test Mode</option>
                </select>
              </div>
            </div>
          )}
        </div>

        {/* Trust Badges */}
        <div className="pt-2 flex items-center justify-center gap-6 text-[11px] text-slate-400">
          <span>• No APIs Required</span>
          <span>• Browser AI Automation</span>
          <span>• Dynamic Captions</span>
          <span>• Smart 9:16 Reframing</span>
        </div>
      </div>

      {/* Recent Projects Section */}
      <div className="pt-6 border-t border-studio-850">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <Film className="w-3.5 h-3.5 text-indigo-400" /> Recent Repurposed Videos
          </h2>
          <span className="text-[11px] text-slate-500 font-mono">
            {recentProjects.length} Projects Saved
          </span>
        </div>

        {recentProjects.length === 0 ? (
          <p className="text-xs text-slate-500 py-3">No videos repurposed yet. Enter a link above to create your first Shorts.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {recentProjects.slice(0, 6).map(p => {
              const formattedDate = p.created_at ? (() => {
                try {
                  const d = new Date(p.created_at);
                  return d.toLocaleDateString(undefined, {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  });
                } catch {
                  return p.created_at;
                }
              })() : 'Just now';

              const isReady = p.status === 'READY' || p.status === 'COMPLETED';
              const isProcessing = p.status === 'ANALYZING' || p.status === 'PROCESSING' || p.status === 'TRANSCRIBING';

              return (
                <div
                  key={p.id}
                  onClick={() => onSelectProject(p.id)}
                  className="group p-3.5 rounded-xl bg-studio-900/90 border border-studio-800 hover:border-indigo-500/50 hover:bg-studio-850/80 cursor-pointer transition flex flex-col justify-between gap-2.5 shadow-lg"
                >
                  <div className="flex items-start gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center shrink-0 mt-0.5 group-hover:scale-105 transition">
                      <Film className="w-4 h-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <h3 className="text-xs font-semibold text-white group-hover:text-indigo-300 transition truncate leading-snug">
                        {p.name}
                      </h3>
                      <div className="flex items-center gap-2 mt-1 text-[11px] text-slate-400 font-mono">
                        <span className="flex items-center gap-1 text-slate-400">
                          <Clock className="w-3 h-3 text-slate-500" /> {formattedDate}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Metadata Badges Footer */}
                  <div className="flex items-center justify-between pt-2 border-t border-studio-800/60 text-[10px]">
                    <div className="flex items-center gap-1.5">
                      <span className="px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-400 font-semibold font-mono">
                        ⚡ {p.clip_count !== undefined ? `${p.clip_count} Shorts` : 'Shorts'}
                      </span>
                      {p.source?.duration && (
                        <span className="px-1.5 py-0.5 rounded bg-studio-800 text-slate-400 font-mono">
                          ⏱️ {Math.round(p.source.duration)}s
                        </span>
                      )}
                    </div>

                    <span className={`px-2 py-0.5 rounded-full font-mono text-[9px] font-bold uppercase tracking-wider ${
                      isReady 
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                        : isProcessing 
                        ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20 animate-pulse'
                        : 'bg-slate-800 text-slate-400'
                    }`}>
                      {isReady ? '✓ Ready' : p.status}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
