import uuid
from fastapi import APIRouter, HTTPException
from app.models import JourneyCreate, Journey
from app.utils.journey_utils import save_journey, load_journey, list_journeys

router = APIRouter()

@router.post("/api/journeys")
async def create_journey(journey: JourneyCreate):
    journey_id = str(uuid.uuid4())
    new_journey = Journey(id=journey_id, **journey.dict())
    save_journey(new_journey)
    return new_journey

@router.get("/api/journeys")
async def list_journeys_api():
    return list_journeys()

@router.get("/api/journeys/{journey_id}")
async def get_journey(journey_id: str):
    journey = load_journey(journey_id)
    if journey:
        return journey
    raise HTTPException(status_code=404, detail="Journey not found")