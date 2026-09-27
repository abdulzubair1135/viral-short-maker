import React, { useState } from 'react';
import { Video, ShieldCheck, CheckCircle2, AlertTriangle, X, Sparkles, Wand2, Share2, Globe, PlaySquare, Layers } from 'lucide-react';
import { Clip, api } from '../services/api';

interface MultiPlatformPublishModalProps {
  clip: Clip;
  itemType?: 'clip' | 'meme';
  onClose: () => void;
  onSuccess: () => void;
}

export const MultiPlatformPublishModal: React.FC<MultiPlatformPublishModalProps> = ({ 
  clip, 
  itemType = 'clip', 
  onClose, 
  onSuccess 
}) => {
  const [platform, setPlatform] = useState<'both' | 'youtube' | 'facebook'>('both');
  const [title, setTitle] = useState(clip.title || '');
  const [description, setDescription] = useState(clip.description || clip.summary || '');
  
  const getInitialHashtags = (): string => {
    const rawList = (clip.hashtags && clip.hashtags.length > 0)
      ? clip.hashtags
      : (clip.tags && clip.tags.length > 0)
        ? clip.tags
        : ['#shorts', '#reels', '#viral', '#trending'];
    
    let tagsArray: string[] = [];
    if (typeof rawList === 'string') {
      try {
        tagsArray = JSON.parse(rawList);
      } catch {
        tagsArray = (rawList as string).split(' ').filter(Boolean);
      }
    } else if (Array.isArray(rawList)) {
      tagsArray = rawList;
    }
    
    if (!tagsArray || tagsArray.length === 0) {
      tagsArray = ['#shorts', '#reels', '#viral', '#trending'];
    }

    return tagsArray.map(t => (typeof t === 'string' && t.startsWith('#')) ? t : `#${t}`).join(' ');
  };

  const [hashtagsText, setHashtagsText] = useState(getInitialHashtags());
  const [audience, setAudience] = useState<string>('not_made_for_kids');
  const [visibility, setVisibility] = useState<string>('public');
  
  const [isPublishing, setIsPublishing] = useState(false);
  const [publishStatus, setPublishStatus] = useState<string | null>(null);
  const [publishResults, setPublishResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // AI Copywriting state
  const [aiProvider, setAiProvider] = useState<'gemini' | 'deepseek'>('gemini');
  const [contentStyle, setContentStyle] = useState<string>('Viral Hook & Mystery');
  const [isGeneratingAi, setIsGeneratingAi] = useState(false);
  const [suggestedTitles, setSuggestedTitles] = useState<string[]>([]);

  const handleGenerateAiMetadata = async () => {
    setIsGeneratingAi(true);
    setError(null);
    try {
      const res = await api.suggestMetadata({
        clip_id: clip.id,
        title: title || clip.title,
        transcript: clip.hook || clip.summary,
        style: contentStyle,
        provider: aiProvider
      });
      const data = res.data || {};
      if (data.recommended_title) setTitle(data.recommended_title);
      if (data.recommended_description) setDescription(data.recommended_description);
      if (data.recommended_hashtags && data.recommended_hashtags.length > 0) {
        // Ensure both shorts and reels tags are included
        const mergedTags = Array.from(new Set([...data.recommended_hashtags, '#shorts', '#reels']));
        setHashtagsText(mergedTags.join(' '));
      }
      if (data.title_options && data.title_options.length > 0) {
        setSuggestedTitles(data.title_options.map((o: any) => o.title));
      }
    } catch (err: any) {
      setError("AI generation failed: " + (err.message || "Unknown error"));
    } finally {
      setIsGeneratingAi(false);
    }
  };

  const handleExecutePublish = async (e: React.FormEvent) => {
    e.preventDefault();
    if (platform !== 'facebook' && !audience) {
      setError("You must explicitly confirm audience selection for YouTube.");
      return;
    }

    const tags = hashtagsText.split(' ').map(t => t.trim()).filter(Boolean);

    setIsPublishing(true);
    setError(null);
    setPublishStatus(`Publishing to ${platform.toUpperCase()}...`);

    try {
      const res = await api.executeMultiPlatformUpload({
        item_id: clip.id,
        item_type: itemType,
        platform,
        title,
        description,
        hashtags: tags,
        audience,
        visibility
      });

      setPublishResults(res);
      setPublishStatus("Publishing Complete!");
      alert(`🎉 Publishing finished! Status: ${res.status}`);
      onSuccess();
    } catch (err: any) {
      setError(err.message || "Publishing failed");
    } finally {
      setIsPublishing(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-studio-900 border border-studio-700 rounded-2xl w-full max-w-xl p-6 shadow-2xl space-y-5 relative my-8">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-slate-400 hover:text-white p-1 rounded-lg"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2.5 text-indigo-400">
          <Share2 className="w-6 h-6" />
          <div>
            <h2 className="text-lg font-bold text-white leading-none">Multi-Platform Publisher Studio</h2>
            <p className="text-[11px] text-slate-400 mt-1">Publish 1-Click to YouTube Shorts, Facebook Reels, or BOTH</p>
          </div>
        </div>

        {/* Platform Selection Tabs */}
        <div className="p-1.5 rounded-xl bg-studio-950 border border-studio-800 grid grid-cols-3 gap-1.5">
          <button
            type="button"
            onClick={() => setPlatform('both')}
            className={`py-2 px-3 rounded-lg text-xs font-bold transition flex items-center justify-center gap-2 ${
              platform === 'both'
                ? 'bg-gradient-to-r from-red-600 to-blue-600 text-white shadow-lg'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Layers className="w-4 h-4" />
            <span>🚀 BOTH (YT + FB)</span>
          </button>

          <button
            type="button"
            onClick={() => setPlatform('youtube')}
            className={`py-2 px-3 rounded-lg text-xs font-bold transition flex items-center justify-center gap-2 ${
              platform === 'youtube'
                ? 'bg-red-600 text-white shadow-lg'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <PlaySquare className="w-4 h-4 text-red-200" />
            <span>🔴 YouTube Only</span>
          </button>

          <button
            type="button"
            onClick={() => setPlatform('facebook')}
            className={`py-2 px-3 rounded-lg text-xs font-bold transition flex items-center justify-center gap-2 ${
              platform === 'facebook'
                ? 'bg-blue-600 text-white shadow-lg'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Globe className="w-4 h-4 text-blue-200" />
            <span>🔵 Facebook Only</span>
          </button>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleExecutePublish} className="space-y-4 text-xs">
          {/* AI Copywriting Assistant */}
          <div className="p-3.5 rounded-xl bg-indigo-950/30 border border-indigo-500/25 space-y-2.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-indigo-400 font-bold text-xs">
                <Sparkles className="w-3.5 h-3.5" />
                <span>AI Copywriting & Viral Hashtags</span>
              </div>
              <div className="flex items-center gap-1 bg-studio-950 p-0.5 rounded-lg border border-studio-800">
                <button
                  type="button"
                  onClick={() => setAiProvider('gemini')}
                  className={`px-2 py-0.5 rounded text-[11px] font-medium transition ${
                    aiProvider === 'gemini' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Gemini
                </button>
                <button
                  type="button"
                  onClick={() => setAiProvider('deepseek')}
                  className={`px-2 py-0.5 rounded text-[11px] font-medium transition ${
                    aiProvider === 'deepseek' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  DeepSeek
                </button>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <select
                value={contentStyle}
                onChange={e => setContentStyle(e.target.value)}
                className="flex-1 px-2.5 py-1.5 rounded-lg bg-studio-950 border border-studio-800 text-slate-200 text-xs focus:outline-none focus:border-indigo-500"
              >
                <option value="Viral Hook & Mystery">Viral Hook & Mystery (Max Curiosity)</option>
                <option value="Action & High Stakes">Action & High Stakes (High Adrenaline)</option>
                <option value="Educational & Mindblowing">Educational & Mindblowing (High Value)</option>
                <option value="Funny Meme & Humor">Funny Meme & Humor (Max Shares)</option>
              </select>
              <button
                type="button"
                onClick={handleGenerateAiMetadata}
                disabled={isGeneratingAi}
                className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-xs font-semibold shadow-md shadow-indigo-600/25 transition flex items-center gap-1.5 shrink-0"
              >
                <Wand2 className="w-3.5 h-3.5" />
                {isGeneratingAi ? "Generating..." : "Generate AI Copy"}
              </button>
            </div>

            {suggestedTitles.length > 0 && (
              <div className="space-y-1 pt-1 border-t border-indigo-500/20">
                <span className="text-[10px] text-slate-400 font-mono">Alternative AI Titles:</span>
                <div className="flex flex-wrap gap-1.5">
                  {suggestedTitles.map((t, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => setTitle(t)}
                      className="px-2 py-1 rounded bg-studio-950 hover:bg-studio-800 border border-studio-700 text-[11px] text-slate-300 hover:text-white text-left transition"
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">Title / Caption *</label>
            <input
              type="text"
              required
              value={title}
              onChange={e => setTitle(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-studio-950 border border-studio-800 text-white focus:outline-none focus:border-indigo-500 font-medium"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">Description / Post Details</label>
            <textarea
              rows={3}
              value={description}
              onChange={e => setDescription(e.target.value)}
              className="w-full px-3.5 py-2 rounded-xl bg-studio-950 border border-studio-800 text-white focus:outline-none focus:border-indigo-500 leading-relaxed"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">Hashtags (Auto #shorts #reels)</label>
            <input
              type="text"
              value={hashtagsText}
              onChange={e => setHashtagsText(e.target.value)}
              className="w-full px-3.5 py-2 rounded-xl bg-studio-950 border border-studio-800 text-indigo-300 focus:outline-none focus:border-indigo-500 font-mono"
            />
          </div>

          {platform !== 'facebook' && (
            <div className="p-3.5 rounded-xl bg-studio-950 border border-studio-800 space-y-2">
              <label className="block text-slate-200 font-bold">
                YouTube Audience Policy *
              </label>
              <div className="space-y-1.5 text-slate-300">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="audience"
                    value="not_made_for_kids"
                    checked={audience === "not_made_for_kids"}
                    onChange={() => setAudience("not_made_for_kids")}
                    className="text-indigo-600 focus:ring-0 cursor-pointer"
                  />
                  <span>No, it's not made for kids</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="audience"
                    value="made_for_kids"
                    checked={audience === "made_for_kids"}
                    onChange={() => setAudience("made_for_kids")}
                    className="text-indigo-600 focus:ring-0 cursor-pointer"
                  />
                  <span>Yes, it's made for kids</span>
                </label>
              </div>
            </div>
          )}

          <div>
            <label className="block text-slate-300 font-semibold mb-1">Visibility / Post Settings</label>
            <select
              value={visibility}
              onChange={e => setVisibility(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-studio-950 border border-studio-800 text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="public">Public (Instant Viral Exposure)</option>
              <option value="private">Private (YouTube Check & Review First)</option>
              <option value="unlisted">Unlisted</option>
            </select>
          </div>

          {publishResults && (
            <div className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 text-xs space-y-1">
              <div className="font-bold flex items-center gap-1 text-emerald-400">
                <CheckCircle2 className="w-4 h-4" />
                <span>Publishing Results:</span>
              </div>
              {publishResults.results?.youtube && (
                <div className="text-[11px] font-mono">🔴 YouTube: Published ({publishResults.results.youtube.video_url})</div>
              )}
              {publishResults.results?.facebook && (
                <div className="text-[11px] font-mono">🔵 Facebook: Reel Published ({publishResults.results.facebook.video_url})</div>
              )}
            </div>
          )}

          <div className="flex items-center justify-between pt-3 border-t border-studio-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-slate-400 hover:text-white"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={isPublishing}
              className={`px-6 py-2.5 rounded-xl text-white font-bold shadow-lg transition flex items-center gap-2 ${
                platform === 'both'
                  ? 'bg-gradient-to-r from-red-600 to-blue-600 hover:from-red-500 hover:to-blue-500 shadow-purple-600/30'
                  : platform === 'facebook'
                    ? 'bg-blue-600 hover:bg-blue-500 shadow-blue-600/30'
                    : 'bg-red-600 hover:bg-red-500 shadow-red-600/30'
              }`}
            >
              <Share2 className="w-4 h-4" />
              <span>
                {isPublishing
                  ? "Publishing Video..."
                  : platform === 'both'
                    ? "Publish to Both (YT + FB)"
                    : platform === 'facebook'
                      ? "Publish to Facebook Reel"
                      : "Publish to YouTube Shorts"}
              </span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
