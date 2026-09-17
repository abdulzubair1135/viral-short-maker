# AI Content Repurposing Studio

A desktop video repurposing application that converts long-form video (local files or validated sources) into high-retention 9:16 Shorts with zero paid AI APIs. It combines browser-automated AI providers (Gemini, ChatGPT, DeepSeek) with an FFmpeg video processing pipeline, OpenCV face-tracking smart reframing, animated karaoke captions, strict 15-point quality assurance, and human review before export.

---

## Key Features

1. **Zero AI APIs Required**
   - Interacts with AI models exclusively via **Playwright-driven persistent browser profiles** (Google Gemini, ChatGPT, DeepSeek).
   - Never stores user passwords. Sessions and cookies persist across runs.
   - Detects CAPTCHAs, verification, and logins automatically: triggers `PAUSED — Human intervention required` so you can sign in once and resume.
   - Includes a deterministic **MockBrowserProvider** for offline testing and development.

2. **Intelligent AI Router**
   - Routes transcripts to primary AI provider, parses structured edit instructions, repairs common JSON syntax errors, and validates schemas.
   - Automatically switches to secondary fallback providers if the primary provider fails or returns malformed data.

3. **Content Rights Safety Guard**
   - Automatically enforces rights confirmation (`I own this content`, `I have permission`, `Licensed content`, `Public domain / permitted use`).
   - Blocks automated export or publishing if rights status is unconfirmed (`Not confirmed`).

4. **Speech Transcription & Boundary Optimization**
   - Speech-to-text pipeline generating word-level and sentence-level timestamps.
   - Caches transcripts on disk (`storage/projects/<id>/work/transcript.json`).
   - Exports formatted SRT subtitle files.
   - Clip boundary optimization snaps cuts to natural sentence/phrase boundaries with configurable pre-roll and post-roll padding (never cuts words mid-syllable).

5. **9:16 Smart Reframing Engine**
   - Detects speaker faces using OpenCV Haar cascades and tracks horizontal speaker motion with an exponential moving average.
   - Supports 3 reframing modes:
     - `speaker_tracking`: Dynamically centers the crop window on the active speaker.
     - `blur_background`: Cinematic blurred background fill with centered crisp 16:9 video.
     - `center`: Fixed center crop.

6. **Animated Caption Engine**
   - Generates Advanced SubStation Alpha (`.ass`) subtitles with per-word karaoke highlighting (`\k` timing tags).
   - Safe zone margins (>= 240px from bottom) prevent overlap with TikTok, YouTube Shorts, and Instagram Reels UI elements.
   - Multiple presets: `Dynamic`, `Minimal`, `Podcast`, `Gaming`, `Cinematic`, `Clean`.

7. **Audio Engine**
   - EBU R128 loudness normalization (`loudnorm=I=-16:TP=-1.5:LRA=11`).
   - Voice presence enhancement gain.
   - Audio sidechain ducking for optional background music tracks.

8. **15-Point Quality Control Verification**
   - Automated quality inspection before any clip is marked `READY`:
     - [x] File existence and size (>5KB)
     - [x] Video stream presence
     - [x] Audio stream presence
     - [x] 1080x1920 target resolution
     - [x] 9:16 aspect ratio verification
     - [x] Frame rate check (>=24 FPS)
     - [x] Black frame detection (<0.8s threshold)
     - [x] Frame decoding integrity
     - [x] Audio sample rate standard (44.1kHz / 48kHz)
     - [x] Caption synchronization
     - [x] Safe zone margin clearance
     - [x] Subject framing check
     - [x] Duration limits (10s to 65s)
     - [x] H.264 & AAC codec standard
     - [x] Content rights confirmed
   - Computes composite **Quality Score (0-100)** with diagnostic check breakdown.

9. **Human Review & Version Control**
   - Human approval workflow: `Approve`, `Edit`, `Reject`, `Regenerate`.
   - Reversible edits with version history stored in SQLite (`clip_versions`).
   - Batch operations: multi-select approve, reject, render, or delete.

10. **Portable Project Bundles (`.acs`)**
    - One-click export of complete project metadata, candidate edit plans, transcripts, and settings into a zip-compressed `.acs` bundle.

---

## Quickstart Guide

### 1. Launch the Studio

To start both the FastAPI backend and open the studio interface in your default browser:

```bash
python run_studio.py
```

The application will run on `http://127.0.0.1:8000`.

### 2. Run the Automated Test Suite

To run all unit tests, FFmpeg video generation tests, quality control checks, and the full end-to-end pipeline test:

```bash
python -m pytest -v
```

### 3. Frontend Development (Optional)

If you wish to run the React + TypeScript frontend in live hot-reloading development mode:

```bash
cd frontend
npm run dev
```

---

## Architecture Overview

```text
├── backend/
│   ├── app/
│   │   ├── api/             # REST endpoints (projects, sources, clips, ai, jobs)
│   │   ├── core/            # Database (SQLite WAL), State Machine, Security, Logging
│   │   ├── models/          # DB models & Pydantic schemas
│   │   ├── ai/              # Browser AI layer, prompts, router, validators, mock & web adapters
│   │   ├── browser/         # Playwright persistent session manager
│   │   ├── video/           # FFmpeg wrapper, ingestion, transcription, reframing, captions, renderer
│   │   ├── quality/         # 15-point QC verification engine
│   │   ├── jobs/            # Background task queue & checkpoint recovery
│   │   ├── config.py        # Central configuration & FFmpeg auto-detection
│   │   └── main.py          # FastAPI application & static asset mounting
├── frontend/
│   ├── src/
│   │   ├── components/      # Dashboard, ProjectList, ProjectStudio, AIProvidersView, JobQueueView
│   │   ├── services/        # Typed API client
│   │   ├── App.tsx          # Root application layout & persistent sidebar navigation
│   │   └── main.tsx         # React DOM entry
│   └── dist/                # Production build bundled directly into FastAPI
├── storage/                 # Projects, output videos, audio WAVs, transcripts, SQLite DB
├── tests/                   # 15 automated unit & end-to-end integration tests
└── run_studio.py            # One-click desktop launcher
```
