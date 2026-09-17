import React, { useState } from 'react';
import { X, CheckCircle2, RefreshCw } from 'lucide-react';
import { Meme } from '../services/api';

interface MemeEditorModalProps {
  meme: Meme;
  onClose: () => void;
  onSave: (updated: Partial<Meme>) => void;
}

export const MemeEditorModal: React.FC<MemeEditorModalProps> = ({
  meme,
  onClose,
  onSave
}) => {
  const [hook, setHook] = useState(meme.hook);
  const [joke, setJoke] = useState(meme.joke);
  const [voiceScript, setVoiceScript] = useState(meme.voice_script);
  const [title, setTitle] = useState(meme.title);
  const [description, setDescription] = useState(meme.description);

  const handleSave = () => {
    onSave({
      hook,
      joke,
      voice_script: voiceScript,
      title,
      description
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-studio-900 border border-studio-800 rounded-2xl w-full max-w-xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-studio-800 flex items-center justify-between">
          <h2 className="text-base font-bold text-white">Edit Meme Short Details</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <div className="p-6 overflow-y-auto space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Opening Hook / Top Screen Text
            </label>
            <input
              type="text"
              value={hook}
              onChange={(e) => setHook(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-studio-950 border border-studio-800 text-xs text-white"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Punchline / Bottom Screen Text
            </label>
            <input
              type="text"
              value={joke}
              onChange={(e) => setJoke(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-studio-950 border border-studio-800 text-xs text-white"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Spoken Voiceover Script (Edge-TTS)
            </label>
            <textarea
              rows={2}
              value={voiceScript}
              onChange={(e) => setVoiceScript(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-studio-950 border border-studio-800 text-xs text-white"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              YouTube Short Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-studio-950 border border-studio-800 text-xs text-white"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              YouTube Description & Hashtags
            </label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-studio-950 border border-studio-800 text-xs text-white"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-studio-800 flex items-center justify-end gap-3 bg-studio-950/60">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-studio-850 hover:bg-studio-800 text-slate-300 text-xs font-semibold"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-5 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-studio-950 text-xs font-bold flex items-center gap-1.5"
          >
            <CheckCircle2 className="w-4 h-4" /> Save Edits
          </button>
        </div>
      </div>
    </div>
  );
};
