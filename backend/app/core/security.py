import re
from pathlib import Path
from typing import List

# Allowed rights statuses according to MASTER BUILD PROMPT:
# "I own this content", "I have permission", "Licensed content", "Public domain / permitted use", "Not confirmed"
PERMITTED_RIGHTS_STATUSES = [
    "I own this content",
    "I have permission",
    "Licensed content",
    "Public domain / permitted use"
]

UNCONFIRMED_RIGHTS_STATUS = "Not confirmed"

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal and invalid characters."""
    # Remove directory separators
    name = Path(filename).name
    # Keep only alphanumeric, underscores, hyphens, and dots
    clean = re.sub(r'[^a-zA-Z0-9_.-]', '_', name)
    return clean or "unnamed_file"

def is_safe_path(target_path: Path, base_dir: Path) -> bool:
    """Ensure target path is within base directory (prevent path traversal)."""
    try:
        target_path.resolve().relative_to(base_dir.resolve())
        return True
    except ValueError:
        return False

def check_rights_permission(rights_status: str) -> bool:
    """Verify whether publishing/export is permitted based on content rights status."""
    return rights_status in PERMITTED_RIGHTS_STATUSES
