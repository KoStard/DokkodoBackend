from typing import List, Optional
from pydantic import BaseModel


class Journey(BaseModel):
    id: str
    name: str
    description: str
    initial_message: Optional[str] = None


class JourneyCreate(BaseModel):
    name: str
    description: str
    initial_message: Optional[str] = None


class Thread(BaseModel):
    id: str
    name: str
    journey_id: str
    messages: List["Message"]

class MediaFile(BaseModel):
    filename: str
    content_type: str

class Message(BaseModel):
    id: str
    role: str
    content: str
    media_files: List[MediaFile] = []
    visible: bool = True

class MessageEdit(BaseModel):
    content: str
    
class ThreadCreate(BaseModel):
    name: str
    journey_id: str

class ThreadRename(BaseModel):
    name: str