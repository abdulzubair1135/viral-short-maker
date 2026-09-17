import React from 'react';
import { Sparkles, CheckCircle2, Circle, Loader2, AlertCircle } from 'lucide-react';

interface ProgressScreenProps {
  progress: number;
  stageMessage: string;
  stage: string;
  error?: string;
  onCancel?: () => void;
}

export const ProgressScreen: React.FC<ProgressScreenProps> = ({ progress, stageMessage, stage, error }) => {
  const steps = [
    { key: 'VALIDATING', label: 'Video received & validated' },
    { key: 'TRANSCRIBING', label: 'Transcript generated with word timestamps' },
    { key: 'ANALYZING', label: 'AI analyzed content & identified viral hooks' },
    { key: 'GENERATING_CLIPS', label: 'Boundary optimization & clip selection' },
    { key: 'RENDERING', label: 'Creating 9:16 Shorts with dynamic captions' },
    { key: 'QUALITY_CHECK', label: 'Checking final quality with 15-point inspection' }
  ];

  const currentIdx = steps.findIndex(s => s.key === stage);

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-6 max-w-xl mx-auto text-center space-y-8 animate-in fade-in duration-300">
      <div className="space-y-3">
        <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center mx-auto border border-indigo-500/20 shadow-lg">
          <Sparkles className="w-6 h-6 animate-spin" />
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Creating your Shorts...
        </h2>
        <p className="text-xs text-slate-400 font-mono">
          {stageMessage || "Analyzing video and generating vertical edits..."}
        </p>
      </div>

      {/* Progress Bar */}
      <div className="w-full space-y-2">
        <div className="w-full bg-studio-900 rounded-full h-3 p-0.5 border border-studio-800 overflow-hidden shadow-inner">
          <div
            className="bg-gradient-to-r from-indigo-500 via-indigo-400 to-amber-400 h-full rounded-full transition-all duration-500"
            style={{ width: `${Math.max(5, progress)}%` }}
          />
        </div>
        <div className="flex justify-between text-xs font-mono text-slate-400">
          <span>Processing</span>
          <span className="text-indigo-400 font-bold">{Math.round(progress)}%</span>
        </div>
      </div>

      {/* Human Readable Steps List */}
      <div className="w-full text-left p-5 rounded-2xl bg-studio-900 border border-studio-800 space-y-3 shadow-xl">
        {steps.map((step, idx) => {
          const isDone = currentIdx > idx || progress >= 100;
          const isCurrent = currentIdx === idx;

          return (
            <div key={step.key} className="flex items-center gap-3 text-xs">
              {isDone ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              ) : isCurrent ? (
                <Loader2 className="w-4 h-4 text-indigo-400 animate-spin shrink-0" />
              ) : (
                <Circle className="w-4 h-4 text-slate-700 shrink-0" />
              )}
              <span className={`font-medium ${isDone ? 'text-slate-300' : isCurrent ? 'text-white font-bold' : 'text-slate-600'}`}>
                {step.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Error Alert if any */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/30 text-rose-300 text-xs text-left space-y-1">
          <div className="flex items-center gap-1.5 font-bold text-rose-400">
            <AlertCircle className="w-4 h-4" /> Issue Encountered
          </div>
          <p>{error}</p>
        </div>
      )}
    </div>
  );
};
