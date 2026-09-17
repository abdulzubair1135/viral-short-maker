import React, { useEffect, useState } from 'react';
import { Sparkles, CheckCircle2, AlertTriangle, ShieldCheck, RefreshCw, Globe, KeyRound } from 'lucide-react';
import { api, AIProviderStatus } from '../services/api';

export const AIProvidersView: React.FC = () => {
  const [statuses, setStatuses] = useState<AIProviderStatus[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchStatuses = async () => {
    setLoading(true);
    try {
      const data = await api.getProvidersStatus();
      setStatuses(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatuses();
  }, []);

  return (
    <div className="p-8 space-y-6 max-w-5xl mx-auto overflow-y-auto h-full">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-400" /> AI Browser Providers
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Zero API keys required. Playwright browser profiles manage persistent web sessions for Gemini, ChatGPT, and DeepSeek.
          </p>
        </div>
        <button
          onClick={fetchStatuses}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-studio-850 hover:bg-studio-800 text-slate-200 text-xs font-medium border border-studio-700/60 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh Status
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {statuses.map(p => (
          <div key={p.provider} className="p-5 rounded-2xl bg-studio-900 border border-studio-800 shadow-xl space-y-4">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                  <Globe className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white capitalize">{p.provider}</h3>
                  <span className="text-[11px] text-slate-400">Browser Profile Adapter</span>
                </div>
              </div>

              {p.ready && !p.requires_human_intervention ? (
                <span className="flex items-center gap-1 text-[11px] px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Ready
                </span>
              ) : (
                <span className="flex items-center gap-1 text-[11px] px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">
                  <AlertTriangle className="w-3.5 h-3.5" /> Human Pause
                </span>
              )}
            </div>

            <div className="p-3 rounded-xl bg-studio-950 border border-studio-850 text-xs font-mono text-slate-300">
              {p.status}
            </div>

            <div className="text-[11px] text-slate-500 space-y-1">
              <p>• Isolated user profile directory: <code className="text-slate-400">storage/browser_profiles/{p.provider}</code></p>
              <p>• Password storage: <strong className="text-emerald-400">Never stored</strong></p>
              <p>• Fallback support: <strong className="text-indigo-400">Enabled</strong></p>
            </div>
          </div>
        ))}
      </div>

      <div className="p-5 rounded-2xl bg-indigo-950/20 border border-indigo-500/20 text-xs text-slate-300 space-y-2">
        <h4 className="font-semibold text-white flex items-center gap-2">
          <KeyRound className="w-4 h-4 text-indigo-400" /> Human Intervention Protocol
        </h4>
        <p className="leading-relaxed">
          When external websites require login or CAPTCHA, the AI Router triggers <code>PAUSED — Human intervention required</code>. You can log into the persistent browser profile once, after which cookies and sessions remain preserved for autonomous repurposing.
        </p>
      </div>
    </div>
  );
};
