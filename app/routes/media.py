from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.utils.path_utils import get_media_path

router = APIRouter()

@router.get("/api/media/{filename}")
async def get_media(filename: str):
    file_path = get_media_path(filename)
    if file_path.exists():
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")