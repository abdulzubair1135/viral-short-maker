import sqlite3
import json

def create_tables(conn: sqlite3.Connection):
    cursor = conn.cursor()

    # Projects
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT DEFAULT '',
        status TEXT NOT NULL DEFAULT 'DRAFT',
        rights_status TEXT NOT NULL DEFAULT 'Not confirmed',
        tags TEXT DEFAULT '[]',
        settings TEXT DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        archived INTEGER DEFAULT 0
    );
    """)

    # Source videos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sources (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        file_path TEXT NOT NULL,
        filename TEXT NOT NULL,
        source_url TEXT DEFAULT '',
        file_size INTEGER DEFAULT 0,
        duration REAL DEFAULT 0.0,
        width INTEGER DEFAULT 0,
        height INTEGER DEFAULT 0,
        fps REAL DEFAULT 0.0,
        video_codec TEXT DEFAULT '',
        audio_codec TEXT DEFAULT '',
        audio_channels INTEGER DEFAULT 0,
        audio_sample_rate INTEGER DEFAULT 0,
        rights_status TEXT NOT NULL DEFAULT 'Not confirmed',
        validated INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    );
    """)

    # Transcripts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transcripts (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL UNIQUE,
        language TEXT DEFAULT 'en',
        full_text TEXT DEFAULT '',
        srt_content TEXT DEFAULT '',
        segments_json TEXT DEFAULT '[]',
        words_json TEXT DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    );
    """)

    # Candidate / Selected Clips
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clips (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        title TEXT NOT NULL,
        start_time REAL NOT NULL,
        end_time REAL NOT NULL,
        duration REAL NOT NULL,
        hook TEXT DEFAULT '',
        summary TEXT DEFAULT '',
        description TEXT DEFAULT '',
        hashtags TEXT DEFAULT '[]',
        keywords TEXT DEFAULT '[]',
        score_total REAL DEFAULT 0.0,
        scores_json TEXT DEFAULT '{}',
        decision_reason TEXT DEFAULT '',
        edit_plan TEXT DEFAULT '{}',
        crop_mode TEXT DEFAULT 'speaker_tracking',
        caption_preset TEXT DEFAULT 'dynamic',
        status TEXT NOT NULL DEFAULT 'CANDIDATE',
        approval_status TEXT NOT NULL DEFAULT 'PENDING',
        is_favorite INTEGER DEFAULT 0,
        output_path TEXT DEFAULT '',
        quality_score REAL DEFAULT 0.0,
        tags TEXT DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    );
    """)

    # Clip Versions (Version control for edits)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clip_versions (
        id TEXT PRIMARY KEY,
        clip_id TEXT NOT NULL,
        version_num INTEGER NOT NULL,
        description TEXT DEFAULT '',
        edit_plan TEXT NOT NULL,
        output_path TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (clip_id) REFERENCES clips(id) ON DELETE CASCADE
    );
    """)

    # Quality Control records
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quality_checks (
        id TEXT PRIMARY KEY,
        clip_id TEXT NOT NULL,
        score REAL NOT NULL,
        passed INTEGER NOT NULL,
        checks_json TEXT NOT NULL,
        notes TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (clip_id) REFERENCES clips(id) ON DELETE CASCADE
    );
    """)

    # Background Jobs / Task Queue
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        project_id TEXT,
        clip_id TEXT,
        job_type TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'QUEUED',
        progress REAL DEFAULT 0.0,
        checkpoint_stage TEXT DEFAULT '',
        checkpoint_data TEXT DEFAULT '{}',
        error_message TEXT DEFAULT '',
        logs TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # AI Job Logs & History
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_jobs (
        id TEXT PRIMARY KEY,
        project_id TEXT,
        provider TEXT NOT NULL,
        task TEXT NOT NULL,
        prompt_text TEXT NOT NULL,
        response_text TEXT DEFAULT '',
        duration REAL DEFAULT 0.0,
        success INTEGER DEFAULT 0,
        retry_count INTEGER DEFAULT 0,
        validation_error TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Templates
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS templates (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT DEFAULT '',
        is_default INTEGER DEFAULT 0,
        aspect_ratio TEXT DEFAULT '9:16',
        resolution TEXT DEFAULT '1080x1920',
        caption_preset TEXT DEFAULT 'dynamic',
        font_name TEXT DEFAULT 'Arial',
        font_size INTEGER DEFAULT 24,
        crop_mode TEXT DEFAULT 'speaker_tracking',
        audio_settings TEXT DEFAULT '{}',
        effects_settings TEXT DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Prompt Library
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prompt_templates (
        id TEXT PRIMARY KEY,
        category TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT DEFAULT '',
        prompt_text TEXT NOT NULL,
        is_default INTEGER DEFAULT 0,
        version INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Assets Manager
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assets (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_size INTEGER DEFAULT 0,
        tags TEXT DEFAULT '[]',
        rights_confirmed INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Settings
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Rejected Candidate Moments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rejected_candidates (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        title TEXT NOT NULL,
        start_time REAL NOT NULL,
        end_time REAL NOT NULL,
        duration REAL NOT NULL,
        claim TEXT DEFAULT '',
        scores_json TEXT DEFAULT '{}',
        score_total REAL DEFAULT 0.0,
        rejection_reason TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    );
    """)

    # YouTube Auth & Channel Connections
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS youtube_auth (
        id TEXT PRIMARY KEY,
        channel_id TEXT DEFAULT '',
        channel_title TEXT DEFAULT '',
        channel_custom_url TEXT DEFAULT '',
        thumbnail_url TEXT DEFAULT '',
        credentials_json TEXT DEFAULT '{}',
        is_authenticated INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Memes (Meme Studio)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memes (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        concept TEXT NOT NULL,
        hook TEXT DEFAULT '',
        joke TEXT DEFAULT '',
        style TEXT DEFAULT 'sarcastic',
        format TEXT DEFAULT 'classic',
        visual_query TEXT DEFAULT '',
        asset_id TEXT DEFAULT '',
        screen_text_json TEXT DEFAULT '[]',
        voice_script TEXT DEFAULT '',
        audio_path TEXT DEFAULT '',
        output_path TEXT DEFAULT '',
        duration REAL DEFAULT 8.0,
        quality_score REAL DEFAULT 0.0,
        scores_json TEXT DEFAULT '{}',
        title TEXT DEFAULT '',
        description TEXT DEFAULT '',
        hashtags TEXT DEFAULT '[]',
        approval_status TEXT NOT NULL DEFAULT 'PENDING',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    );
    """)

    # Run column migrations for existing tables
    migrate_schema(conn)

    conn.commit()

def migrate_schema(conn: sqlite3.Connection):
    """Safely adds new columns to existing tables without data loss."""
    cursor = conn.cursor()

    # clips table migrations
    cursor.execute("PRAGMA table_info(clips)")
    existing_clip_cols = {row[1] for row in cursor.fetchall()}

    new_clip_cols = [
        ("analysis_json", "TEXT DEFAULT '{}'"),
        ("script_json", "TEXT DEFAULT '{}'"),
        ("verdict", "TEXT DEFAULT ''"),
        ("rating", "REAL DEFAULT 0.0"),
        ("source_attribution", "TEXT DEFAULT ''"),
        ("is_ai_narrated", "INTEGER DEFAULT 1"),
    ]

    for col_name, col_def in new_clip_cols:
        if col_name not in existing_clip_cols:
            try:
                cursor.execute(f"ALTER TABLE clips ADD COLUMN {col_name} {col_def};")
            except Exception:
                pass

    # projects table migrations
    cursor.execute("PRAGMA table_info(projects)")
    existing_project_cols = {row[1] for row in cursor.fetchall()}
    if "project_type" not in existing_project_cols:
        try:
            cursor.execute("ALTER TABLE projects ADD COLUMN project_type TEXT DEFAULT 'CREATOR_REVIEW';")
        except Exception:
            pass

    # assets table migrations
    cursor.execute("PRAGMA table_info(assets)")
    existing_asset_cols = {row[1] for row in cursor.fetchall()}
    new_asset_cols = [
        ("source", "TEXT DEFAULT 'unknown'"),
        ("source_url", "TEXT DEFAULT ''"),
        ("creator", "TEXT DEFAULT ''"),
        ("license_name", "TEXT DEFAULT 'UNKNOWN'"),
        ("license_url", "TEXT DEFAULT ''"),
        ("commercial_use", "INTEGER DEFAULT 0"),
        ("modification_allowed", "INTEGER DEFAULT 0"),
        ("attribution_required", "INTEGER DEFAULT 0"),
        ("attribution_text", "TEXT DEFAULT ''"),
        ("safety_state", "TEXT DEFAULT 'REJECTED'"),
        ("verified_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ]
    for col_name, col_def in new_asset_cols:
        if col_name not in existing_asset_cols:
            try:
                cursor.execute(f"ALTER TABLE assets ADD COLUMN {col_name} {col_def};")
            except Exception:
                pass

