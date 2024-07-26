# app/models.py
from pydantic import BaseModel
from typing import List, Optional

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

class ChatRequest(BaseModel):
    messages: List[dict]