import React, { useState } from 'react';
import { Video, ShieldCheck, CheckCircle2, AlertTriangle, X, Sparkles, Wand2 } from 'lucide-react';
import { Clip, api } from '../services/api';

interface YouTubePublishModalProps {
  clip: Clip;
  onClose: () => void;
  onSuccess: () => void;
}

export const YouTubePublishModal: React.FC<YouTubePublishModalProps> = ({ clip, onClose, onSuccess }) => {
  const [title, setTitle] = useState(clip.title || '');
  const [description, setDescription] = useState(clip.description || clip.summary || '');
  const getInitialHashtags = (): string => {
    const rawList = (clip.hashtags && clip.hashtags.length > 0)
      ? clip.hashtags
      : (clip.tags && clip.tags.length > 0)
        ? clip.tags
        : ['#shorts', '#viral'];
    
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
      tagsArray = ['#shorts', '#viral'];
    }

    return tagsArray.map(t => (typeof t === 'string' && t.startsWith('#')) ? t : `#${t}`).join(' ');
  };

  const [hashtagsText, setHashtagsText] = useState(getInitialHashtags());
  const [audience, setAudience] = useState<string>('not_made_for_kids');
  const [visibility, setVisibility] = useState<string>('private');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccessUrl, setUploadSuccessUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // AI Copywriting state (Gemini & DeepSeek)
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
        setHashtagsText(data.recommended_hashtags.join(' '));
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!audience) {
      setError("You must explicitly confirm audience: Made for Kids or Not Made for Kids.");
      return;
    }

    const tags = hashtagsText.split(' ').map(t => t.trim()).filter(Boolean);

    setIsSubmitting(true);
    setError(null);
    try {
      await api.prepareYouTubePublish({
        clip_id: clip.id,
        title,
        description,
        hashtags: tags,
        audience,
        visibility
      });
      alert(`YouTube upload metadata prepared! Set to '${visibility}' with audience '${audience}'.`);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to prepare publish");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDirectUpload = async () => {
    if (!audience) {
      setError("You must explicitly confirm audience: Made for Kids or Not Made for Kids.");
      return;
    }

    const tags = hashtagsText.split(' ').map(t => t.trim()).filter(Boolean);

    setIsUploading(true);
    setError(null);
    try {
      const res = await api.executeYouTubeUpload({
        clip_id: clip.id,
        title,
        description,
        hashtags: tags,
        audience,
        visibility
      });
      setUploadSuccessUrl(res.video_url || "https://studio.youtube.com");
      alert(`Success! Short published to YouTube Studio. Video link: ${res.video_url}`);
      onSuccess();
    } catch (err: any) {
      setError(err.message || "Failed to upload to YouTube");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-studio-900 border border-studio-700 rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-5 relative">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-slate-400 hover:text-white p-1 rounded-lg"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2 text-rose-500">
          <Video className="w-6 h-6" />
          <h2 className="text-lg font-bold text-white">Publish to YouTube Shorts</h2>
        </div>

        {/* Rights & Transformative Disclaimer Notice */}
        <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/25 text-[11px] text-amber-200/90 leading-relaxed flex items-start gap-2.5">
          <ShieldCheck className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
          <div>
            <span className="font-bold text-amber-300">Policy & Rights Notice:</span> Transformative critique and commentary provide strong fair-use foundations, but YouTube copyright and monetization clearance remain subject to creator rights. We recommend publishing as <span className="font-semibold text-white">Private</span> or <span className="font-semibold text-white">Unlisted</span> first to verify checks in YouTube Studio.
          </div>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}


        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          {/* AI Copywriting Assistant (Gemini & DeepSeek) */}
          <div className="p-3.5 rounded-xl bg-indigo-950/30 border border-indigo-500/25 space-y-2.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-indigo-400 font-bold text-xs">
                <Sparkles className="w-3.5 h-3.5" />
                <span>AI Copywriting & Tag Suggestions</span>
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
                <option value="Storytelling & Dramatic">Storytelling & Dramatic (Emotional Hook)</option>
              </select>
              <button
                type="button"
                onClick={handleGenerateAiMetadata}
                disabled={isGeneratingAi}
                className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-xs font-semibold shadow-md shadow-indigo-600/25 transition flex items-center gap-1.5 shrink-0"
              >
                <Wand2 className="w-3.5 h-3.5" />
                {isGeneratingAi ? "Generating..." : "Ask AI to Suggest"}
              </button>
            </div>

            {/* Suggested Title Pills */}
            {suggestedTitles.length > 0 && (
              <div className="space-y-1 pt-1 border-t border-indigo-500/20">
                <span className="text-[10px] text-slate-400 font-mono">Click to pick alternative title:</span>
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
            <label className="block text-slate-300 font-semibold mb-1">Title *</label>
            <input
              type="text"
              required
              value={title}
              onChange={e => setTitle(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-studio-950 border border-studio-800 text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">Description</label>
            <textarea
              rows={3}
              value={description}
              onChange={e => setDescription(e.target.value)}
              className="w-full px-3.5 py-2 rounded-xl bg-studio-950 border border-studio-800 text-white focus:outline-none focus:border-indigo-500 leading-relaxed"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">Hashtags</label>
            <input
              type="text"
              value={hashtagsText}
              onChange={e => setHashtagsText(e.target.value)}
              className="w-full px-3.5 py-2 rounded-xl bg-studio-950 border border-studio-800 text-indigo-300 focus:outline-none focus:border-indigo-500 font-mono"
            />
          </div>

          {/* Mandatory Explicit Audience Selection */}
          <div className="p-3.5 rounded-xl bg-studio-950 border border-studio-800 space-y-2">
            <label className="block text-slate-200 font-bold">
              Audience (Required by YouTube Policy) *
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

          {/* Visibility Selection */}
          <div>
            <label className="block text-slate-300 font-semibold mb-1">Visibility</label>
            <select
              value={visibility}
              onChange={e => setVisibility(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-studio-950 border border-studio-800 text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="private">Private (Recommended default)</option>
              <option value="unlisted">Unlisted</option>
              <option value="public">Public</option>
            </select>
          </div>

          {uploadSuccessUrl && (
            <div className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 text-xs flex items-center justify-between">
              <span className="font-semibold">Uploaded to YouTube:</span>
              <a
                href={uploadSuccessUrl}
                target="_blank"
                rel="noreferrer"
                className="underline text-emerald-400 font-mono hover:text-emerald-300"
              >
                {uploadSuccessUrl}
              </a>
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
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={isSubmitting || isUploading || !audience}
                className="px-4 py-2 rounded-xl bg-studio-800 hover:bg-studio-750 disabled:opacity-40 text-white font-medium transition"
              >
                Save Metadata
              </button>
              <button
                type="button"
                onClick={handleDirectUpload}
                disabled={isSubmitting || isUploading || !audience}
                className="px-5 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 disabled:opacity-40 text-white font-semibold shadow-lg shadow-rose-600/25 transition flex items-center gap-1.5"
              >
                <Video className="w-4 h-4" />
                {isUploading ? "Uploading to Studio..." : "Upload to YouTube Now"}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
