export interface Project {
  id: string;
  name: string;
  description: string;
  status: string;
  rights_status: string;
  tags: string[];
  settings: Record<string, any>;
  created_at: string;
  project_type?: 'CREATOR_REVIEW' | 'MEME_STUDIO';
  source?: any;
  clip_count?: number;
  meme_count?: number;
}

export interface Meme {
  id: string;
  project_id: string;
  concept: string;
  hook: string;
  joke: string;
  style: string;
  format: string;
  visual_query: string;
  asset_id: string;
  screen_text: Array<{ text: string; position: 'top' | 'middle' | 'bottom'; style: 'impact' | 'pill' | 'subtitle' | 'bubble' }>;
  voice_script: string;
  audio_path: string;
  output_path: string;
  video_url: string;
  duration: number;
  quality_score: number;
  scores: {
    relatability?: number;
    punchline_timing?: number;
    visual_synergy?: number;
    shareability?: number;
    trend_alignment?: number;
    hook_power?: number;
    simplicity?: number;
  };
  title: string;
  description: string;
  hashtags: string[];
  approval_status: 'PENDING' | 'APPROVED' | 'REJECTED';
  license_record: {
    source: string;
    creator: string;
    license_name: string;
    license_url: string;
    commercial_use: boolean;
    modification_allowed: boolean;
    attribution_required: boolean;
    attribution_text: string;
    safety_state: string;
  };
  created_at: string;
}


export interface Clip {
  id: string;
  project_id: string;
  title: string;
  start_time: number;
  end_time: number;
  duration: number;
  hook: string;
  summary: string;
  description?: string;
  hashtags?: string[];
  keywords?: string[];
  score_total: number;
  scores: {
    hook?: number;
    story?: number;
    emotion?: number;
    curiosity?: number;
    clarity?: number;
    visual?: number;
    length?: number;
  };
  decision_reason: string;
  edit_plan: any;
  crop_mode: string;
  caption_preset: string;
  status: string;
  approval_status: string;
  is_favorite: boolean;
  output_path?: string;
  quality_score: number;
  tags: string[];

  analysis?: {
    claim_or_event?: string;
    fact_or_opinion?: string;
    commentary?: string;
    context?: string;
    counterpoint?: string;
    verdict?: string;
    rating?: number;
    rating_label?: string;
  };
  verdict?: string;
  rating?: number;
  source_attribution?: string;
  is_ai_narrated?: boolean;
  narration_script?: Array<{ segment: string; text: string }>;
  quality_check?: {
    score: number;
    passed: boolean;
    checks: Array<{ name: string; passed: boolean; details: string }>;
    notes?: string;
  };
  versions?: any[];
}

export interface RejectedCandidate {
  id?: string;
  project_id?: string;
  title: string;
  start_time: number;
  end_time: number;
  duration: number;
  claim?: string;
  score_total?: number;
  rejection_reason?: string;
  reason?: string;
  scores?: any;
}


export interface Job {
  id: string;
  project_id?: string;
  clip_id?: string;
  job_type: string;
  status: string;
  progress: number;
  checkpoint_stage?: string;
  error_message?: string;
  logs?: string;
  created_at: string;
}

export interface AIProviderStatus {
  provider: string;
  ready: boolean;
  status: string;
  requires_human_intervention: boolean;
}

const API_BASE = '/api';

export const api = {
  // Projects
  getProjects: async (): Promise<Project[]> => {
    const res = await fetch(`${API_BASE}/projects/`);
    return res.json();
  },
  getProject: async (id: string): Promise<Project> => {
    const res = await fetch(`${API_BASE}/projects/${id}`);
    return res.json();
  },
  createProject: async (data: { name: string; description?: string; rights_status: string; tags?: string[] }) => {
    const res = await fetch(`${API_BASE}/projects/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return res.json();
  },
  duplicateProject: async (id: string) => {
    const res = await fetch(`${API_BASE}/projects/${id}/duplicate`, { method: 'POST' });
    return res.json();
  },
  deleteProject: async (id: string) => {
    const res = await fetch(`${API_BASE}/projects/${id}`, { method: 'DELETE' });
    return res.json();
  },

  // Sources
  attachLocalSource: async (projectId: string, filePath: string, rightsStatus: string) => {
    const formData = new FormData();
    formData.append('project_id', projectId);
    formData.append('file_path', filePath);
    formData.append('rights_status', rightsStatus);
    const res = await fetch(`${API_BASE}/sources/attach_local`, { method: 'POST', body: formData });
    return res.json();
  },

  // Transcripts
  getTranscript: async (projectId: string) => {
    const res = await fetch(`${API_BASE}/transcripts/${projectId}`);
    return res.json();
  },

  // Clips
  getClips: async (projectId: string, favoritesOnly: boolean = false): Promise<Clip[]> => {
    const res = await fetch(`${API_BASE}/clips/?project_id=${projectId}&favorites_only=${favoritesOnly}`);
    return res.json();
  },
  getClip: async (clipId: string): Promise<Clip> => {
    const res = await fetch(`${API_BASE}/clips/${clipId}`);
    return res.json();
  },
  approveClip: async (clipId: string) => {
    const res = await fetch(`${API_BASE}/clips/${clipId}/approve`, { method: 'POST' });
    return res.json();
  },
  rejectClip: async (clipId: string) => {
    const res = await fetch(`${API_BASE}/clips/${clipId}/reject`, { method: 'POST' });
    return res.json();
  },
  toggleFavorite: async (clipId: string) => {
    const res = await fetch(`${API_BASE}/clips/${clipId}/favorite`, { method: 'POST' });
    return res.json();
  },
  updateEditPlan: async (clipId: string, payload: any) => {
    const res = await fetch(`${API_BASE}/clips/${clipId}/edit_plan`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return res.json();
  },
  batchAction: async (action: 'approve' | 'reject' | 'delete', clipIds: string[]) => {
    const res = await fetch(`${API_BASE}/clips/batch_action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, clip_ids: clipIds })
    });
    return res.json();
  },

  // AI
  getProvidersStatus: async (): Promise<AIProviderStatus[]> => {
    const res = await fetch(`${API_BASE}/ai/providers`);
    return res.json();
  },
  getAIJobs: async (projectId?: string) => {
    const url = projectId ? `${API_BASE}/ai/jobs?project_id=${projectId}` : `${API_BASE}/ai/jobs`;
    const res = await fetch(url);
    return res.json();
  },

  // Jobs
  startPipeline: async (projectId: string, aiProvider: string = 'mock') => {
    const res = await fetch(`${API_BASE}/jobs/start_pipeline`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_id: projectId, ai_provider: aiProvider })
    });
    return res.json();
  },
  getJobs: async (projectId?: string): Promise<Job[]> => {
    const url = projectId ? `${API_BASE}/jobs/?project_id=${projectId}` : `${API_BASE}/jobs/`;
    const res = await fetch(url);
    return res.json();
  },
  resumeJob: async (jobId: string, aiProvider: string = 'mock') => {
    const res = await fetch(`${API_BASE}/jobs/${jobId}/resume`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ai_provider: aiProvider })
    });
    return res.json();
  },

  // One-Click Repurpose
  repurposeVideo: async (urlOrPath: string, rightsConfirmed: boolean, options: any = {}) => {
    const res = await fetch(`${API_BASE}/repurpose/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url_or_path: urlOrPath,
        rights_confirmed: rightsConfirmed,
        options
      })
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || "Failed to start repurposing");
    }
    return res.json();
  },

  getRepurposeStatus: async (jobId: string) => {
    const res = await fetch(`${API_BASE}/repurpose/status/${jobId}`);
    return res.json();
  },

  getRejectedCandidates: async (projectId: string): Promise<{ project_id: string; rejected_candidates: RejectedCandidate[] }> => {
    const res = await fetch(`${API_BASE}/repurpose/rejected/${projectId}`);
    return res.json();
  },

  regenerateCommentary: async (clipId: string) => {
    const res = await fetch(`${API_BASE}/clips/${clipId}/regenerate_commentary`, { method: 'POST' });
    return res.json();
  },

  regenerateMetadata: async (clipId: string) => {
    const res = await fetch(`${API_BASE}/clips/${clipId}/regenerate_metadata`, { method: 'POST' });
    return res.json();
  },

  prepareYouTubePublish: async (data: { clip_id: string; title: string; description: string; hashtags: string[]; audience: string; visibility: string }) => {
    const res = await fetch(`${API_BASE}/repurpose/publish_preparation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Publish preparation error");
    }
    return res.json();
  },

  executeYouTubeUpload: async (data: { clip_id: string; title: string; description: string; hashtags: string[]; audience: string; visibility: string }) => {
    const res = await fetch(`${API_BASE}/repurpose/publish_upload`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "YouTube upload error");
    }
    return res.json();
  },

  executeMultiPlatformUpload: async (data: {
    item_id: string;
    item_type?: string;
    platform: 'youtube' | 'facebook' | 'both';
    title: string;
    description: string;
    hashtags: string[];
    audience?: string;
    visibility?: string;
  }) => {
    const res = await fetch(`${API_BASE}/repurpose/publish_multi_platform`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Multi-platform publishing error");
    }
    return res.json();
  },

  suggestMetadata: async (data: { clip_id?: string; title?: string; transcript?: string; style?: string; provider?: string }) => {
    const res = await fetch(`${API_BASE}/ai/suggest_metadata`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return res.json();
  },

  // Templates
  getTemplates: async () => {
    const res = await fetch(`${API_BASE}/templates/`);
    return res.json();
  },

  // Meme Studio
  generateMemes: async (data: {
    topic: string;
    style?: string;
    format?: string;
    count?: number;
    uploaded_asset_id?: string | null;
    rights_confirmed: boolean;
    ai_provider?: string;
  }) => {
    const res = await fetch(`${API_BASE}/memes/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to start meme generation");
    }
    return res.json();
  },

  getProjectMemes: async (projectId: string): Promise<{ project: Project; memes: Meme[] }> => {
    const res = await fetch(`${API_BASE}/memes/project/${projectId}`);
    if (!res.ok) throw new Error("Failed to load project memes");
    return res.json();
  },

  getMemeStatus: async (jobId: string) => {
    const res = await fetch(`${API_BASE}/memes/status/${jobId}`);
    return res.json();
  },

  regenerateMemeJoke: async (memeId: string, aiProvider: string = 'auto') => {
    const res = await fetch(`${API_BASE}/memes/${memeId}/regenerate_joke`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ai_provider: aiProvider })
    });
    if (!res.ok) throw new Error("Failed to regenerate joke");
    return res.json();
  },

  approveMeme: async (memeId: string, status: 'APPROVED' | 'REJECTED' | 'PENDING' = 'APPROVED') => {
    const res = await fetch(`${API_BASE}/memes/${memeId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status })
    });
    return res.json();
  },

  uploadMemeImage: async (file: File, rightsConfirmed: boolean) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('rights_confirmed', String(rightsConfirmed));
    const res = await fetch(`${API_BASE}/memes/upload_image`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to upload image");
    }
    return res.json();
  }
};

