import React, { useState, useEffect } from 'react';
import { 
  Film, Laugh, Sparkles, FolderKanban, Settings, Video, Home as HomeIcon
} from 'lucide-react';
import { HomeScreen } from './components/HomeScreen';
import { OneClickHome } from './components/OneClickHome';
import { MemeStudioView } from './components/MemeStudioView';
import { MemeResultsView } from './components/MemeResultsView';
import { ProgressScreen } from './components/ProgressScreen';
import { ResultsScreen } from './components/ResultsScreen';
import { ProjectStudio } from './components/ProjectStudio';
import { ProjectList } from './components/ProjectList';
import { PublishingView } from './components/PublishingView';
import { AIProvidersView } from './components/AIProvidersView';
import { api, Project, Clip, Meme } from './services/api';

export function App() {
  // Navigation states: 'home' | 'creator_review' | 'meme_studio' | 'processing' | 'results' | 'editor' | 'projects' | 'publishing' | 'settings'
  const [viewState, setViewState] = useState<'home' | 'creator_review' | 'meme_studio' | 'processing' | 'results' | 'editor' | 'projects' | 'publishing' | 'settings'>('home');
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [jobType, setJobType] = useState<'REVIEW' | 'MEME'>('REVIEW');
  
  // Progress states
  const [jobProgress, setJobProgress] = useState<number>(0);
  const [jobStageMessage, setJobStageMessage] = useState<string>('Initializing...');
  const [jobStage, setJobStage] = useState<string>('QUEUED');
  const [jobError, setJobError] = useState<string | undefined>();
  
  // Results
  const [generatedClips, setGeneratedClips] = useState<Clip[]>([]);
  const [generatedMemes, setGeneratedMemes] = useState<Meme[]>([]);
  const [editingClip, setEditingClip] = useState<Clip | null>(null);

  // Projects list
  const [projects, setProjects] = useState<Project[]>([]);

  const fetchProjects = async () => {
    try {
      const data = await api.getProjects();
      setProjects(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  // Polling loop when in 'processing' state
  useEffect(() => {
    if (viewState !== 'processing' || !activeJobId) return;

    const interval = setInterval(async () => {
      try {
        if (jobType === 'MEME') {
          const res = await api.getMemeStatus(activeJobId);
          setJobProgress(res.progress);
          setJobStageMessage(res.logs ? res.logs.split('\n').filter(Boolean).pop() || "Rendering meme short..." : "Generating memes...");
          setJobStage(res.status);

          if (res.status === 'READY') {
            clearInterval(interval);
            const mData = await api.getProjectMemes(res.project_id);
            setActiveProject(mData.project);
            setActiveProjectId(res.project_id);
            setGeneratedMemes(mData.memes || []);
            setViewState('results');
            fetchProjects();
          } else if (res.status === 'FAILED') {
            clearInterval(interval);
            setJobError(res.error_message || "Meme generation failed");
          }
        } else {
          const res = await api.getRepurposeStatus(activeJobId);
          setJobProgress(res.progress);
          setJobStageMessage(res.human_message);
          setJobStage(res.stage);

          if (res.status === 'READY' || res.status === 'CANDIDATE') {
            clearInterval(interval);
            setGeneratedClips(res.clips || []);
            setActiveProjectId(res.project_id);
            const p = await api.getProject(res.project_id);
            setActiveProject(p);
            setViewState('results');
            fetchProjects();
          } else if (res.status === 'FAILED') {
            clearInterval(interval);
            setJobError(res.error_message || "Pipeline failed");
          }
        }
      } catch (err: any) {
        console.error("Poll error:", err);
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [viewState, activeJobId, jobType]);

  // Creator Review Pipeline Handler
  const handleStartCreatorReview = async (urlOrPath: string, rightsConfirmed: boolean, options: any) => {
    try {
      setJobType('REVIEW');
      setJobProgress(10);
      setJobStageMessage("Acquiring video footage & captions...");
      setJobStage("VALIDATING");
      setJobError(undefined);
      setViewState('processing');

      const res = await api.repurposeVideo(urlOrPath, rightsConfirmed, options);
      setActiveProjectId(res.project_id);
      setActiveJobId(res.job_id);
    } catch (err: any) {
      alert("Error starting Creator Review: " + err.message);
      setViewState('creator_review');
    }
  };

  // Meme Studio Pipeline Handler
  const handleStartMemePipeline = async (params: {
    topic: string;
    style: string;
    format: string;
    count: number;
    uploaded_asset_id?: string | null;
    rights_confirmed: boolean;
    ai_provider: string;
  }) => {
    try {
      setJobType('MEME');
      setJobProgress(15);
      setJobStageMessage("Generating viral comedy hooks with AI...");
      setJobStage("GENERATING_CONCEPTS");
      setJobError(undefined);
      setViewState('processing');

      const res = await api.generateMemes(params);
      setActiveProjectId(res.project_id);
      setActiveJobId(res.job_id);
    } catch (err: any) {
      alert("Error starting Meme Studio: " + err.message);
      setViewState('meme_studio');
    }
  };

  const handleOpenEditor = (clip: Clip) => {
    setEditingClip(clip);
    setViewState('editor');
  };

  const handleSelectProjectFromList = async (id: string) => {
    setActiveProjectId(id);
    try {
      const proj = await api.getProject(id);
      setActiveProject(proj);

      if (proj.project_type === 'MEME_STUDIO') {
        const mData = await api.getProjectMemes(id);
        setGeneratedMemes(mData.memes || []);
        setViewState('results');
      } else {
        const clips = await api.getClips(id);
        if (clips.length > 0) {
          setGeneratedClips(clips);
          setViewState('results');
        } else {
          setViewState('editor');
        }
      }
    } catch (e) {
      console.error("Error opening project:", e);
    }
  };

  const isMemeProject = activeProject?.project_type === 'MEME_STUDIO';

  return (
    <div className="flex flex-col h-screen w-screen bg-studio-950 text-slate-100 font-sans overflow-hidden">
      {/* Global Top Navigation Bar */}
      <header className="h-14 px-6 border-b border-studio-850 bg-studio-900/90 backdrop-blur flex items-center justify-between z-30 shrink-0 select-none">
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => setViewState('home')}>
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-amber-500 flex items-center justify-center text-white shadow-md shadow-indigo-600/30">
            <Sparkles className="w-4 h-4" />
          </div>
          <span className="text-sm font-bold text-white tracking-tight">
            AI Content Studio
          </span>
        </div>

        {/* Dedicated Clear Navigation Tabs */}
        <nav className="flex items-center gap-1 sm:gap-1.5 text-xs font-semibold">
          <button
            onClick={() => setViewState('home')}
            className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
              viewState === 'home'
                ? 'bg-indigo-600/15 text-indigo-300 border border-indigo-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <HomeIcon className="w-3.5 h-3.5" />
            <span>Home</span>
          </button>

          <button
            onClick={() => setViewState('creator_review')}
            className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
              viewState === 'creator_review' || (viewState === 'results' && !isMemeProject)
                ? 'bg-indigo-600/15 text-indigo-300 border border-indigo-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Film className="w-3.5 h-3.5 text-indigo-400" />
            <span>Creator Review</span>
          </button>

          <button
            onClick={() => setViewState('meme_studio')}
            className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
              viewState === 'meme_studio' || (viewState === 'results' && isMemeProject)
                ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Laugh className="w-3.5 h-3.5 text-amber-400" />
            <span>Meme Studio</span>
          </button>

          <button
            onClick={() => { setViewState('projects'); fetchProjects(); }}
            className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
              viewState === 'projects'
                ? 'bg-indigo-600/15 text-indigo-300 border border-indigo-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <FolderKanban className="w-3.5 h-3.5 text-slate-400" />
            <span>Projects ({projects.length})</span>
          </button>

          <button
            onClick={() => setViewState('publishing')}
            className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
              viewState === 'publishing'
                ? 'bg-red-600/15 text-red-300 border border-red-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Video className="w-3.5 h-3.5 text-red-400" />
            <span>Publishing</span>
          </button>


          <button
            onClick={() => setViewState('settings')}
            className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
              viewState === 'settings'
                ? 'bg-indigo-600/15 text-indigo-300 border border-indigo-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Settings className="w-3.5 h-3.5 text-slate-400" />
            <span>Settings</span>
          </button>
        </nav>
      </header>

      {/* Main Viewport */}
      <main className="flex-1 overflow-hidden flex flex-col relative bg-studio-950">
        {viewState === 'home' && (
          <HomeScreen
            onNavigate={(dest) => {
              if (dest === 'creator_review') setViewState('creator_review');
              else if (dest === 'meme_studio') setViewState('meme_studio');
              else if (dest === 'projects') setViewState('projects');
              else if (dest === 'publishing') setViewState('publishing');
              else if (dest === 'settings') setViewState('settings');
            }}
            onSelectProject={handleSelectProjectFromList}
            recentProjects={projects}
          />
        )}

        {viewState === 'creator_review' && (
          <OneClickHome
            onStartPipeline={handleStartCreatorReview}
            onSelectProject={handleSelectProjectFromList}
            recentProjects={projects.filter(p => p.project_type !== 'MEME_STUDIO')}
          />
        )}

        {viewState === 'meme_studio' && (
          <MemeStudioView
            onStartMemePipeline={handleStartMemePipeline}
            onSelectProject={handleSelectProjectFromList}
          />
        )}

        {viewState === 'processing' && (
          <ProgressScreen
            progress={jobProgress}
            stageMessage={jobStageMessage}
            stage={jobStage}
            error={jobError}
          />
        )}

        {viewState === 'results' && activeProjectId && (
          isMemeProject ? (
            <MemeResultsView
              projectId={activeProjectId}
              projectTitle={activeProject?.name || "Meme Short Concepts"}
              memes={generatedMemes}
              onNewMeme={() => setViewState('meme_studio')}
              onRefresh={async () => {
                const mData = await api.getProjectMemes(activeProjectId);
                setGeneratedMemes(mData.memes || []);
              }}
            />
          ) : (
            <ResultsScreen
              projectId={activeProjectId}
              clips={generatedClips}
              onOpenEditor={handleOpenEditor}
              onNewVideo={() => setViewState('creator_review')}
              onRefresh={async () => {
                const updated = await api.getClips(activeProjectId);
                setGeneratedClips(updated);
              }}
            />
          )
        )}

        {viewState === 'editor' && activeProjectId && (
          <ProjectStudio
            projectId={activeProjectId}
            onBack={() => setViewState('results')}
          />
        )}

        {viewState === 'projects' && (
          <ProjectList
            projects={projects}
            onSelectProject={handleSelectProjectFromList}
            onRefresh={fetchProjects}
          />
        )}

        {viewState === 'publishing' && (
          <PublishingView />
        )}

        {viewState === 'settings' && (
          <AIProvidersView />
        )}
      </main>
    </div>
  );
}

export default App;
