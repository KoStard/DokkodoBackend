from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import chat, threads, journeys, media
from app.dependencies import get_anthropic_client
from app.utils.path_utils import ensure_storage_structure

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

# Include routers
app.include_router(chat.router)
app.include_router(threads.router)
app.include_router(journeys.router)
app.include_router(media.router)

# Dependency injection
app.dependency_overrides[get_anthropic_client] = get_anthropic_client

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)