import asyncio
import json
from typing import List, Optional
from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
import uuid
import shutil
from app.utils.path_utils import (
    ensure_storage_structure, get_thread_path, get_journey_path,
    get_media_path, list_threads, list_journeys
)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure storage structure exists
ensure_storage_structure()

class MediaFile(BaseModel):
    filename: str
    content_type: str

class Message(BaseModel):
    id: str
    role: str
    content: str
    media_files: List[MediaFile] = []
    visible: bool = True

class Thread(BaseModel):
    id: str
    name: str
    journey_id: str
    messages: List[Message]

class Journey(BaseModel):
    id: str
    name: str
    description: str
    initial_message: Optional[str] = None

class JourneyCreate(BaseModel):
    name: str
    description: str
    initial_message: Optional[str] = None

class ThreadCreate(BaseModel):
    name: str
    journey_id: str

class ThreadRename(BaseModel):
    name: str

async def generate_text():
    sentence = "This is a long hardcoded text that will be streamed to the UI."
    for index in range(0, len(sentence), 5):
        yield sentence[index:index+5]
        await asyncio.sleep(0.05)

@app.post("/api/chat")
async def stream_chat(body: dict):
    print(body)
    return StreamingResponse(generate_text(), media_type="text/plain")

@app.post("/api/threads")
async def create_thread(request: ThreadCreate):
    thread_id = str(uuid.uuid4())
    journey = load_journey(request.journey_id)
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")
    
    initial_messages = []
    if journey.initial_message:
        initial_message_id = str(uuid.uuid4())
        initial_messages.append(Message(
            id=initial_message_id,
            role="assistant",
            content=journey.initial_message,
            visible=False
        ))
    
    thread = Thread(id=thread_id, name=request.name, journey_id=request.journey_id, messages=initial_messages)
    save_thread(thread)
    return thread

@app.get("/api/threads")
async def list_threads_api():
    threads = []
    for file_path in list_threads():
        with file_path.open("r") as f:
            thread = json.load(f)
            threads.append({"id": thread["id"], "name": thread["name"]})
    return threads

@app.get("/api/threads/{thread_id}")
async def get_thread(thread_id: str):
    thread = load_thread(thread_id)
    if thread:
        return thread
    raise HTTPException(status_code=404, detail="Thread not found")

@app.put("/api/threads/{thread_id}")
async def rename_thread(thread_id: str, thread_rename: ThreadRename):
    thread = load_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    thread.name = thread_rename.name
    save_thread(thread)
    return {"message": "Thread renamed successfully"}

@app.delete("/api/threads/{thread_id}")
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

@app.post("/api/threads/{thread_id}/messages")
async def add_message(
    thread_id: str, 
    content: str = Form(...),
    role: str = Form(...),
    message_id: str = Form(default=None),
    files: List[UploadFile] = File(None)
):
    thread = load_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    message_id = message_id or str(uuid.uuid4())
    media_files = []
    
    if files:
        for file in files:
            filename = f"{uuid.uuid4()}_{file.filename}"
            file_path = get_media_path(filename)
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            media_files.append(MediaFile(filename=filename, content_type=file.content_type))
    
    message = Message(id=message_id, role=role, content=content, media_files=media_files, visible=True)
    thread.messages.append(message)
    save_thread(thread)
    return message

@app.put("/api/threads/{thread_id}/messages/{message_id}")
async def edit_message(
    thread_id: str, 
    message_id: str, 
    content: str = Form(...),
    files: List[UploadFile] = File(None)
):
    thread = load_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    message_index = next((index for (index, message) in enumerate(thread.messages) if message.id == message_id), None)
    if message_index is None:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Update the message content
    thread.messages[message_index].content = content
    
    # Handle file updates
    if files:
        # Remove old media files
        for media_file in thread.messages[message_index].media_files:
            old_file_path = get_media_path(media_file.filename)
            if old_file_path.exists():
                old_file_path.unlink()
        
        # Save new media files
        new_media_files = []
        for file in files:
            filename = f"{uuid.uuid4()}_{file.filename}"
            file_path = get_media_path(filename)
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            new_media_files.append(MediaFile(filename=filename, content_type=file.content_type))
        
        thread.messages[message_index].media_files = new_media_files
    
    # Discard messages that came after the edited message
    thread.messages = thread.messages[:message_index + 1]
    
    save_thread(thread)
    return {"message": "Message updated successfully"}

@app.get("/api/media/{filename}")
async def get_media(filename: str):
    file_path = get_media_path(filename)
    if file_path.exists():
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")

@app.post("/api/journeys")
async def create_journey(journey: JourneyCreate):
    journey_id = str(uuid.uuid4())
    new_journey = Journey(id=journey_id, **journey.dict())
    save_journey(new_journey)
    return new_journey

@app.get("/api/journeys")
async def list_journeys_api():
    journeys = []
    for file_path in list_journeys():
        with file_path.open("r") as f:
            journey = json.load(f)
            journeys.append(journey)
    return journeys

@app.get("/api/journeys/{journey_id}")
async def get_journey(journey_id: str):
    journey = load_journey(journey_id)
    if journey:
        return journey
    raise HTTPException(status_code=404, detail="Journey not found")

def save_thread(thread: Thread):
    file_path = get_thread_path(thread.id)
    with file_path.open("w") as f:
        json.dump(thread.dict(), f, indent=2)

def load_thread(thread_id: str) -> Optional[Thread]:
    file_path = get_thread_path(thread_id)
    if file_path.exists():
        with file_path.open("r") as f:
            thread_data = json.load(f)
            return Thread(**thread_data)
    return None

def save_journey(journey: Journey):
    file_path = get_journey_path(journey.id)
    with file_path.open("w") as f:
        json.dump(journey.dict(), f, indent=2)

def load_journey(journey_id: str) -> Optional[Journey]:
    file_path = get_journey_path(journey_id)
    if file_path.exists():
        with file_path.open("r") as f:
            journey_data = json.load(f)
            return Journey(**journey_data)
    return None