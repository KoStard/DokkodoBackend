import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def generate_text():
    sentence = "This is a long hardcoded text that will be streamed to the UI."
    for index in range(0, len(sentence), 5):
        yield sentence[index:index+5]
        await asyncio.sleep(0.05)  # 0.5 second delay


@app.post("/api/chat")
async def stream_text(body: dict):
    print(body)
    return StreamingResponse(generate_text(), media_type="text/plain")


@app.get("/api")
async def root():
    return {"message": "Hello World"}
