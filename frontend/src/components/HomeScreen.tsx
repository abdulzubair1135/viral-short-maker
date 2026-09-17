import React from 'react';
import { Film, Laugh, Sparkles, ArrowRight, ShieldCheck, Zap, CheckCircle2, FolderKanban } from 'lucide-react';
import { Project } from '../services/api';

interface HomeScreenProps {
  onNavigate: (view: 'creator_review' | 'meme_studio' | 'projects' | 'publishing' | 'settings') => void;
  onSelectProject: (id: string) => void;
  recentProjects: Project[];
}

export const HomeScreen: React.FC<HomeScreenProps> = ({
  onNavigate,
  onSelectProject,
  recentProjects
}) => {
  return (
    <div className="flex-1 overflow-y-auto px-6 py-10 max-w-6xl mx-auto w-full">
      {/* Header Banner */}
      <div className="text-center max-w-2xl mx-auto mb-12">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold uppercase tracking-wider mb-4">
          <Sparkles className="w-3.5 h-3.5" /> Next-Gen AI Content Studio
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight mb-4">
          What would you like to create today?
        </h1>
        <p className="text-slate-400 text-sm sm:text-base leading-relaxed">
          Select a dedicated creation suite below. Two distinct, specialized workflows engineered for high retention and viral reach.
        </p>
      </div>

      {/* Two Product Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-14">
        {/* Product 1: Creator Review */}
        <div 
          onClick={() => onNavigate('creator_review')}
          className="group relative bg-studio-900 border border-studio-800 hover:border-indigo-500/50 rounded-2xl p-8 transition-all duration-300 hover:shadow-2xl hover:shadow-indigo-500/10 cursor-pointer flex flex-col justify-between"
        >
          <div className="absolute top-0 right-0 w-48 h-48 bg-indigo-500/5 rounded-full blur-3xl group-hover:bg-indigo-500/10 transition-colors pointer-events-none" />
          
          <div>
            <div className="w-14 h-14 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 mb-6 group-hover:scale-105 transition-transform shadow-lg shadow-indigo-600/20">
              <Film className="w-7 h-7" />
            </div>

            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-400">Video Pipeline</span>
              <span className="px-2 py-0.5 rounded-full bg-indigo-500/20 text-[10px] font-bold text-indigo-300">Fair Use</span>
            </div>

            <h2 className="text-2xl font-bold text-white mb-3 group-hover:text-indigo-300 transition-colors">
              🎬 Creator Review
            </h2>
            <p className="text-slate-400 text-sm leading-relaxed mb-6">
              Turn long-form YouTube videos into transformative critique & analysis Shorts. Includes 8-score retention analysis, fair-use commentary narration, verdict cards, and 15-point QC.
            </p>

            <ul className="space-y-2 mb-8 text-xs text-slate-300">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>YouTube URL / Local MP4 to 9:16 Shorts</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Transformative commentary & verdict rating card</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Speaker tracking reframing & dynamic captions</span>
              </li>
            </ul>
          </div>

          <button className="w-full py-3 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm flex items-center justify-center gap-2 transition shadow-lg shadow-indigo-600/25 group-hover:gap-3">
            <span>Launch Creator Review</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {/* Product 2: Meme Studio */}
        <div 
          onClick={() => onNavigate('meme_studio')}
          className="group relative bg-studio-900 border border-studio-800 hover:border-amber-500/50 rounded-2xl p-8 transition-all duration-300 hover:shadow-2xl hover:shadow-amber-500/10 cursor-pointer flex flex-col justify-between"
        >
          <div className="absolute top-0 right-0 w-48 h-48 bg-amber-500/5 rounded-full blur-3xl group-hover:bg-amber-500/10 transition-colors pointer-events-none" />

          <div>
            <div className="w-14 h-14 rounded-2xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-amber-400 mb-6 group-hover:scale-105 transition-transform shadow-lg shadow-amber-500/20">
              <Laugh className="w-7 h-7" />
            </div>

            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-amber-400">Viral Studio</span>
              <span className="px-2 py-0.5 rounded-full bg-amber-500/20 text-[10px] font-bold text-amber-300">Brand New</span>
            </div>

            <h2 className="text-2xl font-bold text-white mb-3 group-hover:text-amber-300 transition-colors">
              😂 Meme Studio
            </h2>
            <p className="text-slate-400 text-sm leading-relaxed mb-6">
              Generate viral, high-retention meme Shorts from any idea, topic, or image. Features AI comedic setup & punchline, verified licensed visual assets, Ken Burns motion, and voiceover.
            </p>

            <ul className="space-y-2 mb-8 text-xs text-slate-300">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-amber-400 shrink-0" />
                <span>Text topic or uploaded template image</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-amber-400 shrink-0" />
                <span>Strict license verification (Wikimedia & Public Domain)</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-amber-400 shrink-0" />
                <span>Impact typography, POV pill banners & Edge-TTS voice</span>
              </li>
            </ul>
          </div>

          <button className="w-full py-3 px-4 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-semibold text-sm flex items-center justify-center gap-2 transition shadow-lg shadow-amber-600/25 group-hover:gap-3">
            <span>Launch Meme Studio</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Recent Projects Section */}
      {recentProjects.length > 0 && (
        <div className="border-t border-studio-850 pt-10">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <FolderKanban className="w-5 h-5 text-slate-400" /> Recent Projects
            </h3>
            <button
              onClick={() => onNavigate('projects')}
              className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition"
            >
              View All ({recentProjects.length}) →
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {recentProjects.slice(0, 6).map((proj) => {
              const isMeme = proj.project_type === 'MEME_STUDIO';
              const count = isMeme ? (proj.meme_count || 0) : (proj.clip_count || 0);
              const label = isMeme ? 'memes' : 'shorts';

              return (
                <div
                  key={proj.id}
                  onClick={() => onSelectProject(proj.id)}
                  className="bg-studio-900 border border-studio-800 hover:border-slate-700 p-4 rounded-xl transition cursor-pointer hover:bg-studio-850 flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        isMeme 
                          ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' 
                          : 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                      }`}>
                        {isMeme ? '😂 Meme Studio' : '🎬 Creator Review'}
                      </span>
                      <span className="text-[11px] text-slate-500">
                        {new Date(proj.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <h4 className="text-sm font-semibold text-white truncate mb-1">
                      {proj.name}
                    </h4>
                  </div>

                  <div className="flex items-center justify-between pt-3 border-t border-studio-800/60 text-xs text-slate-400 mt-2">
                    <span>{count} {label} generated</span>
                    <span className="text-indigo-400 hover:underline">Open →</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
