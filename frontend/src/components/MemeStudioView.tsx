import React, { useState } from 'react';
import { 
  Laugh, Sparkles, Upload, Image as ImageIcon, ShieldCheck, 
  HelpCircle, ChevronDown, CheckCircle2, AlertCircle, Wand2, ArrowRight
} from 'lucide-react';
import { api } from '../services/api';

interface MemeStudioViewProps {
  onStartMemePipeline: (params: {
    topic: string;
    style: string;
    format: string;
    count: number;
    uploaded_asset_id?: string | null;
    rights_confirmed: boolean;
    ai_provider: string;
  }) => Promise<void>;
  onSelectProject: (id: string) => void;
}

const QUICK_TOPICS = [
  "Pushing code to production on Friday 5 PM",
  "Me explaining complex lore at 3:00 AM",
  "When the bug fixes itself after adding a print statement",
  "Drinking 4 cups of coffee before 10 AM",
  "Gym leg day regret immediately after walking down stairs",
  "Student studying 5 months of syllabus in 2 hours",
  "Cat plotting world domination behind the curtain"
];

const HUMOR_STYLES = [
  { id: 'sarcastic', name: 'Sarcastic & Witty', desc: 'Deadpan irony, biting satire, tech/work sarcasm' },
  { id: 'relatable', name: 'Relatable Daily Pain', desc: 'Universal struggles, student/adult life, daily fails' },
  { id: 'dark_humor', name: 'Dark & Chaotic', desc: 'Existential dread, coffee dependency, funny despair' },
  { id: 'wholesome', name: 'Wholesome & Cute', desc: 'Heartwarming twists, cute fails, unexpected wins' },
  { id: 'absurd', name: 'Absurd & Surreal', desc: 'Chaotic escalation, surreal memes, unpredictable punchlines' },
  { id: 'educational_roast', name: 'Educational Roast', desc: 'Debunking misconceptions with hilarious roasts' },
];

const MEME_FORMATS = [
  { id: 'pov', name: 'POV Pill Banner', desc: 'Modern POV pill overlay with dynamic reaction' },
  { id: 'classic', name: 'Classic Impact', desc: 'Iconic bold top/bottom text with black outline' },
  { id: 'reaction', name: 'Reaction Short', desc: 'Statement callout with visceral visual reaction' },
  { id: 'story', name: 'Two-Beat Twist', desc: 'Quick setup and sudden expectation twist' },
  { id: 'animated', name: 'Ken Burns Motion', desc: 'Dynamic slow pan and zoom punchline' },
];

export const MemeStudioView: React.FC<MemeStudioViewProps> = ({
  onStartMemePipeline
}) => {
  const [topic, setTopic] = useState('');
  const [selectedStyle, setSelectedStyle] = useState('sarcastic');
  const [selectedFormat, setSelectedFormat] = useState('pov');
  const [count, setCount] = useState(3);
  const [rightsConfirmed, setRightsConfirmed] = useState(true);
  const [aiProvider, setAiProvider] = useState('auto');
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Upload image state
  const [uploadedAssetId, setUploadedAssetId] = useState<string | null>(null);
  const [uploadFileName, setUploadFileName] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadRightsConfirmed, setUploadRightsConfirmed] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!uploadRightsConfirmed) {
      alert("You must confirm you have the rights to use this image before uploading.");
      return;
    }

    setIsUploading(true);
    setErrorMsg(null);
    try {
      const res = await api.uploadMemeImage(file, uploadRightsConfirmed);
      setUploadedAssetId(res.asset_id);
      setUploadFileName(file.name);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to upload image.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) {
      setErrorMsg("Please enter a meme topic or idea.");
      return;
    }
    if (!rightsConfirmed) {
      setErrorMsg("Please confirm that content complies with copyright & safe licensing rules.");
      return;
    }

    setErrorMsg(null);
    await onStartMemePipeline({
      topic: topic.trim(),
      style: selectedStyle,
      format: selectedFormat,
      count,
      uploaded_asset_id: uploadedAssetId,
      rights_confirmed: rightsConfirmed,
      ai_provider: aiProvider
    });
  };

  return (
    <div className="flex-1 overflow-y-auto px-6 py-8 max-w-4xl mx-auto w-full">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-12 h-12 rounded-2xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-amber-400 shadow-lg shadow-amber-500/20">
          <Laugh className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight flex items-center gap-2">
            Meme Studio
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 font-semibold border border-amber-500/30">
              Viral Creator
            </span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-400">
            Create high-retention 9:16 vertical meme Shorts & animated GIFs with clean silent audio (no voiceover), AI jokes, and verified licensed visual assets.
          </p>
        </div>
      </div>

      {errorMsg && (
        <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Topic Input Card */}
        <div className="bg-studio-900 border border-studio-800 rounded-2xl p-6 shadow-xl">
          <label className="block text-sm font-bold text-white mb-2">
            What is your meme idea or topic? <span className="text-amber-400">*</span>
          </label>
          <textarea
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            rows={3}
            placeholder="e.g., Software engineers deploying straight to production at 4:59 PM on a Friday..."
            className="w-full px-4 py-3 rounded-xl bg-studio-950 border border-studio-800 focus:border-amber-500 focus:ring-1 focus:ring-amber-500 text-white placeholder-slate-500 text-sm outline-none transition"
          />

          {/* Quick Idea Chips */}
          <div className="mt-3">
            <span className="text-[11px] font-semibold text-slate-400 block mb-2">
              💡 Or pick a trending inspiration:
            </span>
            <div className="flex flex-wrap gap-1.5">
              {QUICK_TOPICS.map((t, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setTopic(t)}
                  className="px-2.5 py-1 rounded-lg bg-studio-850 hover:bg-amber-500/10 hover:text-amber-300 border border-studio-800 hover:border-amber-500/30 text-[11px] text-slate-300 transition text-left"
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Style & Format Selection */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Humor Style */}
          <div className="bg-studio-900 border border-studio-800 rounded-2xl p-6 shadow-xl">
            <label className="block text-sm font-bold text-white mb-3">
              Humor Style
            </label>
            <div className="space-y-2">
              {HUMOR_STYLES.map((style) => (
                <div
                  key={style.id}
                  onClick={() => setSelectedStyle(style.id)}
                  className={`p-3 rounded-xl border transition cursor-pointer flex items-start justify-between ${
                    selectedStyle === style.id
                      ? 'bg-amber-500/10 border-amber-500/50 text-white'
                      : 'bg-studio-950/60 border-studio-800/80 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <div>
                    <span className="text-xs font-bold block">{style.name}</span>
                    <span className="text-[11px] text-slate-400 block">{style.desc}</span>
                  </div>
                  {selectedStyle === style.id && (
                    <CheckCircle2 className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Meme Format & Count */}
          <div className="bg-studio-900 border border-studio-800 rounded-2xl p-6 shadow-xl flex flex-col justify-between">
            <div>
              <label className="block text-sm font-bold text-white mb-3">
                Meme Format
              </label>
              <div className="space-y-2 mb-6">
                {MEME_FORMATS.map((fmt) => (
                  <div
                    key={fmt.id}
                    onClick={() => setSelectedFormat(fmt.id)}
                    className={`p-3 rounded-xl border transition cursor-pointer flex items-start justify-between ${
                      selectedFormat === fmt.id
                        ? 'bg-amber-500/10 border-amber-500/50 text-white'
                        : 'bg-studio-950/60 border-studio-800/80 text-slate-300 hover:border-slate-700'
                    }`}
                  >
                    <div>
                      <span className="text-xs font-bold block">{fmt.name}</span>
                      <span className="text-[11px] text-slate-400 block">{fmt.desc}</span>
                    </div>
                    {selectedFormat === fmt.id && (
                      <CheckCircle2 className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Shorts Count */}
            <div className="pt-4 border-t border-studio-800">
              <label className="block text-xs font-bold text-white mb-2">
                Number of Memes to Generate
              </label>
              <div className="flex gap-2">
                {[2, 3, 4, 5].map((num) => (
                  <button
                    key={num}
                    type="button"
                    onClick={() => setCount(num)}
                    className={`flex-1 py-2 rounded-lg text-xs font-bold transition border ${
                      count === num
                        ? 'bg-amber-500 text-studio-950 border-amber-400 shadow-md shadow-amber-500/20'
                        : 'bg-studio-950 border-studio-800 text-slate-300 hover:border-slate-700'
                    }`}
                  >
                    {num} Memes
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Optional Custom Image Upload */}
        <div className="bg-studio-900 border border-studio-800 rounded-2xl p-6 shadow-xl">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-bold text-white flex items-center gap-2">
              <ImageIcon className="w-4 h-4 text-amber-400" />
              Upload Custom Meme Image / Template <span className="text-xs text-slate-500 font-normal">(Optional)</span>
            </span>
            {uploadFileName && (
              <span className="text-xs text-emerald-400 font-medium">✓ Uploaded: {uploadFileName}</span>
            )}
          </div>
          <p className="text-xs text-slate-400 mb-4">
            If omitted, Meme Studio will automatically search & verify royalty-free public domain and Creative Commons visual assets from Wikimedia Commons.
          </p>

          <div className="flex flex-col sm:flex-row items-center gap-4">
            <label className="cursor-pointer px-4 py-2.5 rounded-xl bg-studio-850 hover:bg-studio-800 border border-studio-700 text-xs font-semibold text-white flex items-center gap-2 transition">
              <Upload className="w-4 h-4 text-amber-400" />
              <span>{isUploading ? "Uploading..." : "Choose Image (PNG / JPG)"}</span>
              <input
                type="file"
                accept="image/*"
                onChange={handleFileUpload}
                disabled={isUploading}
                className="hidden"
              />
            </label>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="uploadRights"
                checked={uploadRightsConfirmed}
                onChange={(e) => setUploadRightsConfirmed(e.target.checked)}
                className="rounded border-studio-700 text-amber-500 focus:ring-amber-500"
              />
              <label htmlFor="uploadRights" className="text-[11px] text-slate-400 select-none">
                I own this image or have permission to use it
              </label>
            </div>
          </div>
        </div>

        {/* Advanced Accordion */}
        <div className="bg-studio-900/60 border border-studio-800/80 rounded-2xl overflow-hidden">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="w-full px-6 py-4 flex items-center justify-between text-xs font-bold text-slate-300 hover:text-white"
          >
            <span>Advanced Configuration (AI Engine)</span>
            <ChevronDown className={`w-4 h-4 transition-transform ${showAdvanced ? 'rotate-180' : ''}`} />
          </button>

          {showAdvanced && (
            <div className="px-6 pb-6 pt-2 border-t border-studio-800/60 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  AI Comedy Engine Provider
                </label>
                <select
                  value={aiProvider}
                  onChange={(e) => setAiProvider(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-studio-950 border border-studio-800 text-xs text-white"
                >
                  <option value="auto">Auto (Best Available Browser Provider)</option>
                  <option value="gemini">Google Gemini (Chrome Browser Session)</option>
                  <option value="chatgpt">ChatGPT (Chrome Browser Session)</option>
                  <option value="deepseek">DeepSeek (Chrome Browser Session)</option>
                </select>
                <p className="text-[11px] text-slate-500 mt-1">
                  Uses your local logged-in browser session. Zero API keys or subscriptions required.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Legal & Safety Confirmation */}
        <div className="p-4 rounded-xl bg-studio-900/80 border border-studio-800 flex items-start gap-3">
          <input
            type="checkbox"
            id="rightsConfirmation"
            checked={rightsConfirmed}
            onChange={(e) => setRightsConfirmed(e.target.checked)}
            className="mt-1 rounded border-studio-700 text-amber-500 focus:ring-amber-500"
          />
          <div>
            <label htmlFor="rightsConfirmation" className="text-xs font-semibold text-slate-200 cursor-pointer">
              Strict License & Fair Use Certification
            </label>
            <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">
              I understand Meme Studio enforces strict licensing. Visual assets are checked against verified CC0, Public Domain, and CC-BY databases. Any unknown or restrictive license is rejected automatically.
            </p>
          </div>
        </div>

        {/* Generate Action Button */}
        <button
          type="submit"
          className="w-full py-4 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-studio-950 font-bold text-base shadow-xl shadow-amber-500/20 hover:shadow-amber-500/30 transition-all flex items-center justify-center gap-3 cursor-pointer"
        >
          <Sparkles className="w-5 h-5 text-studio-950" />
          <span>GENERATE MEME SHORTS</span>
          <ArrowRight className="w-5 h-5 text-studio-950" />
        </button>
      </form>
    </div>
  );
};
