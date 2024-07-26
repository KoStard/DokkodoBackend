# app/utils/journey_utils.py
import json
from typing import List
from app.models import Journey
from app.utils.path_utils import get_journey_path, list_journeys as list_journey_files

def save_journey(journey: Journey):
    """Save a journey to a JSON file."""
    file_path = get_journey_path(journey.id)
    with file_path.open("w") as f:
        json.dump(journey.dict(), f, indent=2)

def load_journey(journey_id: str) -> Journey | None:
    """Load a journey from a JSON file."""
    file_path = get_journey_path(journey_id)
    if file_path.exists():
        with file_path.open("r") as f:
            journey_data = json.load(f)
            return Journey(**journey_data)
    return None

def list_journeys() -> List[Journey]:
    """List all journeys."""
    journeys = []
    for file_path in list_journey_files():
        with file_path.open("r") as f:
            journey_data = json.load(f)
            journeys.append(Journey(**journey_data))
    return journeys

def delete_journey(journey_id: str) -> bool:
    """Delete a journey file."""
    file_path = get_journey_path(journey_id)
    if file_path.exists():
        file_path.unlink()
        return True
    return False