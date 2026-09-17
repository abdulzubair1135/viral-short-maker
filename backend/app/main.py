from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.config import STORAGE_DIR, PROJECTS_DIR, BASE_DIR
from backend.app.core.database import init_db, get_db_connection
from backend.app.core.logging import logger
from backend.app.api.routes_projects import router as projects_router
from backend.app.api.routes_sources import router as sources_router
from backend.app.api.routes_transcripts import router as transcripts_router
from backend.app.api.routes_clips import router as clips_router
from backend.app.api.routes_ai import router as ai_router_endpoints
from backend.app.api.routes_jobs import router as jobs_router
from backend.app.api.routes_templates import router as templates_router
from backend.app.api.routes_repurpose import router as repurpose_router
from backend.app.api.routes_memes import router as memes_router

app = FastAPI(
    title="AI Content Repurposing Studio API",
    version="1.0.0",
    description="Professional desktop video repurposing engine using Playwright browser AI and FFmpeg"
)

@app.on_event("startup")
async def startup_event():
    import asyncio
    init_db()
    from backend.app.jobs.queue import job_queue
    job_queue.loop = asyncio.get_running_loop()
    logger.info("AI Content Repurposing Studio backend initialized.")

# Enable CORS for local React/Vite development and desktop webview
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static video storage
app.mount("/storage", StaticFiles(directory=str(STORAGE_DIR)), name="storage")

# Include API Routers
app.include_router(repurpose_router, prefix="/api")
app.include_router(memes_router, prefix="/api")
app.include_router(projects_router, prefix="/api")
app.include_router(sources_router, prefix="/api")
app.include_router(transcripts_router, prefix="/api")
app.include_router(clips_router, prefix="/api")
app.include_router(ai_router_endpoints, prefix="/api")
app.include_router(jobs_router, prefix="/api")
app.include_router(templates_router, prefix="/api")


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": "AI Content Repurposing Studio",
        "version": "1.0.0"
    }

# Mount frontend production build if present (must be after explicit API routes)
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
