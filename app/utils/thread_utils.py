# app/utils/thread_utils.py
import json
from typing import List
from app.models import Thread, Message
from app.utils.path_utils import get_thread_path, list_threads as list_thread_files, get_media_path

def save_thread(thread: Thread):
    """Save a thread to a JSON file."""
    file_path = get_thread_path(thread.id)
    with file_path.open("w") as f:
        json.dump(thread.dict(), f, indent=2)

def load_thread(thread_id: str) -> Thread | None:
    """Load a thread from a JSON file."""
    file_path = get_thread_path(thread_id)
    if file_path.exists():
        with file_path.open("r") as f:
            thread_data = json.load(f)
            return Thread(**thread_data)
    return None

def list_threads() -> List[dict]:
    """List all threads with basic information."""
    threads = []
    for file_path in list_thread_files():
        with file_path.open("r") as f:
            thread_data = json.load(f)
            threads.append({
                "id": thread_data["id"],
                "name": thread_data["name"],
                "journey_id": thread_data["journey_id"]
            })
    return threads

def delete_thread(thread_id: str) -> bool:
    """Delete a thread file and its associated media files."""
    thread = load_thread(thread_id)
    if thread:
        # Delete associated media files
        for message in thread.messages:
            for media_file in message.media_files:
                media_file_path = get_media_path(media_file.filename)
                if media_file_path.exists():
                    media_file_path.unlink()
        
        # Delete the thread file
        file_path = get_thread_path(thread_id)
        file_path.unlink()
        return True
    return False

def add_message_to_thread(thread_id: str, message: Message) -> Thread | None:
    """Add a message to a thread and save it."""
    thread = load_thread(thread_id)
    if thread:
        thread.messages.append(message)
        save_thread(thread)
        return thread
    return None

def update_and_discard_messages_after(thread_id: str, message_id: str, updated_message: Message) -> Thread | None:
    """Update a message in a thread, discard all messages after it, and save it."""
    thread = load_thread(thread_id)
    if thread:
        for i, msg in enumerate(thread.messages):
            if msg.id == message_id:
                thread.messages = thread.messages[:i] + [updated_message]
                save_thread(thread)
                return thread
    return None

