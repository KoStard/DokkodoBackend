import os
from pathlib import Path

# Base storage path
STORAGE_PATH = Path("storage")

# Subfolder paths
THREADS_PATH = STORAGE_PATH / "threads"
JOURNEYS_PATH = STORAGE_PATH / "journeys"
MEDIA_PATH = STORAGE_PATH / "media"

def ensure_storage_structure():
    """Ensure all necessary folders exist."""
    THREADS_PATH.mkdir(parents=True, exist_ok=True)
    JOURNEYS_PATH.mkdir(parents=True, exist_ok=True)
    MEDIA_PATH.mkdir(parents=True, exist_ok=True)

def get_thread_path(thread_id: str) -> Path:
    """Get the file path for a thread."""
    return THREADS_PATH / f"{thread_id}.json"

def get_journey_path(journey_id: str) -> Path:
    """Get the file path for a journey."""
    return JOURNEYS_PATH / f"{journey_id}.json"

def get_media_path(filename: str) -> Path:
    """Get the file path for a media file."""
    return MEDIA_PATH / filename

def list_threads() -> list[Path]:
    """List all thread files."""
    return list(THREADS_PATH.glob("*.json"))

def list_journeys() -> list[Path]:
    """List all journey files."""
    return list(JOURNEYS_PATH.glob("*.json"))