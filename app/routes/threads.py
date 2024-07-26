import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List
from app.models import Message, ThreadCreate, ThreadRename, Thread, MediaFile
from app.utils.journey_utils import load_journey
from app.utils.path_utils import get_media_path, get_thread_path
from app.utils.thread_utils import save_thread, load_thread, list_threads, add_message_to_thread, update_and_discard_messages_after

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

@router.post("/api/threads/{thread_id}/messages")
async def create_message(
    thread_id: str,
    content: str = Form(...),
    role: str = Form(...),
    files: List[UploadFile] = File(None)
):
    thread = load_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    message_id = str(uuid.uuid4())
    media_files = []

    if files:
        for file in files:
            filename = f"{uuid.uuid4()}_{file.filename}"
            file_path = get_media_path(filename)
            with file_path.open("wb") as buffer:
                buffer.write(await file.read())
            media_files.append(MediaFile(filename=filename, content_type=file.content_type))

    new_message = Message(
        id=message_id,
        role=role,
        content=content,
        media_files=media_files,
        visible=True
    )

    updated_thread = add_message_to_thread(thread_id, new_message)
    if not updated_thread:
        raise HTTPException(status_code=500, detail="Failed to add message to thread")

    return new_message

@router.put("/api/threads/{thread_id}/messages/{message_id}")
async def update_message(
    thread_id: str,
    message_id: str,
    content: str = Form(...),
    files: List[UploadFile] = File(None)
):
    thread = load_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    existing_message = next((m for m in thread.messages if m.id == message_id), None)
    if not existing_message:
        raise HTTPException(status_code=404, detail="Message not found")

    media_files = []

    if files:
        for file in files:
            filename = f"{uuid.uuid4()}_{file.filename}"
            file_path = get_media_path(filename)
            with file_path.open("wb") as buffer:
                buffer.write(await file.read())
            media_files.append(MediaFile(filename=filename, content_type=file.content_type))

    updated_message = Message(
        id=message_id,
        role=existing_message.role,
        content=content,
        media_files=media_files,
        visible=existing_message.visible
    )

    updated_thread = update_and_discard_messages_after(thread_id, message_id, updated_message)
    if not updated_thread:
        raise HTTPException(status_code=500, detail="Failed to update message in thread")

    return updated_message

@router.delete("/api/threads/{thread_id}/messages/{message_id}")
async def delete_message(thread_id: str, message_id: str):
    thread = load_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    message_to_delete = next((m for m in thread.messages if m.id == message_id), None)
    if not message_to_delete:
        raise HTTPException(status_code=404, detail="Message not found")

    # Remove the message from the thread
    thread.messages = [m for m in thread.messages if m.id != message_id]

    # Delete associated media files
    for media_file in message_to_delete.media_files:
        media_file_path = get_media_path(media_file.filename)
        if media_file_path.exists():
            media_file_path.unlink()

    save_thread(thread)
    return {"message": "Message deleted successfully"}