from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = ""
    rights_status: str = "Not confirmed"
    tags: List[str] = []
    settings: Dict[str, Any] = {}

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    rights_status: Optional[str] = None
    tags: Optional[List[str]] = None
    settings: Optional[Dict[str, Any]] = None
    archived: Optional[bool] = None

class WordTimestamp(BaseModel):
    word: str
    start: float
    end: float
    confidence: Optional[float] = 1.0

class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str
    words: Optional[List[WordTimestamp]] = []

class TranscriptResponse(BaseModel):
    id: str
    project_id: str
    language: str
    full_text: str
    srt_content: str
    segments: List[TranscriptSegment]

class ZoomEvent(BaseModel):
    time: float
    scale: float = 1.15
    duration: float = 2.0

class CaptionStyleConfig(BaseModel):
    preset: str = "dynamic"
    font_name: str = "Arial"
    font_size: int = 24
    font_color: str = "#FFFFFF"
    highlight_color: str = "#FFFF00"
    position_y: float = 0.75  # % from top (inside safe zone)
    uppercase: bool = True

class AudioSettingsConfig(BaseModel):
    normalize_loudness: bool = True
    voice_gain_db: float = 2.0
    background_music_path: Optional[str] = None
    music_volume: float = 0.15
    ducking_enabled: bool = True

class EditPlan(BaseModel):
    start: float
    end: float
    hook: str
    crop_mode: str = "speaker_tracking"  # "speaker_tracking", "center", "blur_background"
    caption_style: CaptionStyleConfig = CaptionStyleConfig()
    audio_settings: AudioSettingsConfig = AudioSettingsConfig()
    zoom_events: List[ZoomEvent] = []
    show_progress_bar: bool = True

class ClipScoreBreakdown(BaseModel):
    hook: float = Field(0.0, ge=0, le=100)
    story: float = Field(0.0, ge=0, le=100)
    emotion: float = Field(0.0, ge=0, le=100)
    curiosity: float = Field(0.0, ge=0, le=100)
    clarity: float = Field(0.0, ge=0, le=100)
    visual: float = Field(0.0, ge=0, le=100)
    length: float = Field(0.0, ge=0, le=100)
    total: float = Field(0.0, ge=0, le=100)

class ClipCandidate(BaseModel):
    title: str
    start: float
    end: float
    hook: str
    summary: str
    scores: ClipScoreBreakdown
    decision_reason: str
    crop_mode: str = "speaker_tracking"
    caption_preset: str = "dynamic"

class ClipResponse(BaseModel):
    id: str
    project_id: str
    title: str
    start_time: float
    end_time: float
    duration: float
    hook: str
    summary: str
    score_total: float
    scores: Dict[str, Any]
    decision_reason: str
    edit_plan: Dict[str, Any]
    crop_mode: str
    caption_preset: str
    status: str
    approval_status: str
    is_favorite: bool
    output_path: Optional[str]
    quality_score: float
    tags: List[str]
    created_at: str

class QualityCheckItem(BaseModel):
    name: str
    passed: bool
    details: str

class QualityReport(BaseModel):
    clip_id: str
    score: float
    passed: bool
    checks: List[QualityCheckItem]
    notes: Optional[str] = ""

class AIJobLog(BaseModel):
    id: str
    project_id: Optional[str]
    provider: str
    task: str
    prompt_text: str
    response_text: str
    duration: float
    success: bool
    retry_count: int
    validation_error: Optional[str] = ""

class JobStatusResponse(BaseModel):
    id: str
    project_id: Optional[str]
    clip_id: Optional[str]
    job_type: str
    status: str
    progress: float
    checkpoint_stage: str
    error_message: Optional[str]
    logs: Optional[str]
