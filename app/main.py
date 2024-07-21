import asyncio
import json
import os
from typing import List, Optional
from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
import uuid
import shutil
import os
from fastapi import HTTPException

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the base path for storage
STORAGE_PATH = "storage"

# Ensure the storage directory exists
os.makedirs(STORAGE_PATH, exist_ok=True)

class MediaFile(BaseModel):
    filename: str
    content_type: str

class Message(BaseModel):
    id: str
    role: str
    content: str
    media_files: List[MediaFile] = []

class Thread(BaseModel):
    id: str
    name: str
    messages: List[Message]

class MessageEdit(BaseModel):
    content: str
    
class ThreadCreate(BaseModel):
    name: str

class ThreadRename(BaseModel):
    name: str

async def generate_text():
    sentence = "This is a long hardcoded text that will be streamed to the UI."
    for index in range(0, len(sentence), 5):
        yield sentence[index:index+5]
        await asyncio.sleep(0.05)  # 0.5 second delay

@app.post("/api/chat")
async def stream_text(body: dict):
    print(body)
    return StreamingResponse(generate_text(), media_type="text/plain")

@app.post("/api/threads")
async def create_thread(request: ThreadCreate):
    thread_id = str(uuid.uuid4())
    thread = Thread(id=thread_id, name=request.name, messages=[])
    save_thread(thread)
    return thread

@app.get("/api/threads")
async def list_threads():
    threads = []
    for filename in os.listdir(STORAGE_PATH):
        if filename.endswith(".json"):
            with open(os.path.join(STORAGE_PATH, filename), "r") as f:
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
    thread = load_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    file_path = os.path.join(STORAGE_PATH, f"{thread_id}.json")
    if os.path.exists(file_path):
        os.remove(file_path)
        
        # Delete associated media files
        for message in thread.messages:
            for media_file in message.media_files:
                media_file_path = os.path.join(STORAGE_PATH, media_file.filename)
                if os.path.exists(media_file_path):
                    os.remove(media_file_path)
        
        return {"message": "Thread deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Thread file not found")

@app.post("/api/threads/{thread_id}/messages")
async def add_message(
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
            file_path = os.path.join(STORAGE_PATH, filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            media_files.append(MediaFile(filename=filename, content_type=file.content_type))
    
    message = Message(id=message_id, role=role, content=content, media_files=media_files)
    thread.messages.append(message)
    save_thread(thread)
    return {"message": "Message added successfully", "message_id": message_id}

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
            old_file_path = os.path.join(STORAGE_PATH, media_file.filename)
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
        
        # Save new media files
        new_media_files = []
        for file in files:
            filename = f"{uuid.uuid4()}_{file.filename}"
            file_path = os.path.join(STORAGE_PATH, filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            new_media_files.append(MediaFile(filename=filename, content_type=file.content_type))
        
        thread.messages[message_index].media_files = new_media_files
    
    # Discard messages that came after the edited message
    thread.messages = thread.messages[:message_index + 1]
    
    save_thread(thread)
    return {"message": "Message updated successfully"}

@app.get("/api/media/{filename}")
async def get_media(filename: str):
    file_path = os.path.join(STORAGE_PATH, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")

def save_thread(thread: Thread):
    file_path = os.path.join(STORAGE_PATH, f"{thread.id}.json")
    with open(file_path, "w") as f:
        json.dump(thread.dict(), f, indent=2)

def load_thread(thread_id: str) -> Optional[Thread]:
    file_path = os.path.join(STORAGE_PATH, f"{thread_id}.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            thread_data = json.load(f)
            return Thread(**thread_data)
    return None

@app.get("/api")
async def root():
    return {"message": "Hello World"}