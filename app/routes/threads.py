import uuid
from fastapi import APIRouter, HTTPException
from app.models import Message, ThreadCreate, ThreadRename, Thread
from app.utils.journey_utils import load_journey
from app.utils.path_utils import get_media_path, get_thread_path
from app.utils.thread_utils import save_thread, load_thread, list_threads

router = APIRouter()

@router.post("/api/threads")
async def create_thread(request: ThreadCreate):
    thread_id = str(uuid.uuid4())
    journey = load_journey(request.journey_id)
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")

    initial_messages = []
    if journey.initial_message:
        initial_message_id = str(uuid.uuid4())
        initial_messages.append(
            Message(
                id=initial_message_id,
                role="user",
                content=journey.initial_message,
                visible=False,
            )
        )

    thread = Thread(
        id=thread_id,
        name=request.name,
        journey_id=request.journey_id,
        messages=initial_messages,
    )
    save_thread(thread)
    return thread

@router.get("/api/threads")
async def list_threads_api():
    return list_threads()

@router.get("/api/threads/{thread_id}")
async def get_thread(thread_id: str):
    thread = load_thread(thread_id)
    if thread:
        return thread
    raise HTTPException(status_code=404, detail="Thread not found")

@router.put("/api/threads/{thread_id}")
async def rename_thread(thread_id: str, thread_rename: ThreadRename):
    thread = load_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    thread.name = thread_rename.name
    save_thread(thread)
    return {"message": "Thread renamed successfully"}

@router.delete("/api/threads/{thread_id}")
async def delete_thread(thread_id: str):
    thread_path = get_thread_path(thread_id)
    if thread_path.exists():
        thread = load_thread(thread_id)
        thread_path.unlink()

        # Delete associated media files
        for message in thread.messages:
            for media_file in message.media_files:
                media_file_path = get_media_path(media_file.filename)
                if media_file_path.exists():
                    media_file_path.unlink()

        return {"message": "Thread deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Thread file not found")