import json
from typing import Dict, Any, Optional
from backend.app.core.database import get_db_connection
from backend.app.core.logging import logger

CHECKPOINT_STAGES = [
    "VALIDATING",
    "TRANSCRIBING",
    "ANALYZING",
    "GENERATING_CLIPS",
    "CAPTIONING",
    "RENDERING",
    "QUALITY_CHECK",
    "READY"
]

class CheckpointManager:
    @staticmethod
    def save_checkpoint(job_id: str, stage: str, data: Dict[str, Any], progress: float):
        """Persist checkpoint data and stage progress into DB."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE jobs 
                SET checkpoint_stage = ?, checkpoint_data = ?, progress = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (stage, json.dumps(data), progress, job_id))

    @staticmethod
    def get_checkpoint(job_id: str) -> Optional[Dict[str, Any]]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT checkpoint_stage, checkpoint_data, progress, status FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "stage": row["checkpoint_stage"],
                "data": json.loads(row["checkpoint_data"] or "{}"),
                "progress": row["progress"],
                "status": row["status"]
            }
