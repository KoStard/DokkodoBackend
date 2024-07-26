from fastapi import APIRouter, Depends, HTTPException
from anthropic import Anthropic
from fastapi.responses import StreamingResponse
from app.dependencies import get_anthropic_client
from app.models import ChatRequest

router = APIRouter()


@router.post("/api/chat")
async def stream_chat(
    body: ChatRequest, client: Anthropic = Depends(get_anthropic_client)
):
    anthropic_messages = [
        {"role": message.role, "content": message.content} for message in body.messages
    ]
    try:

        def stream_response():
            with client.messages.stream(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=anthropic_messages,
            ) as stream:
                text_stream = stream.text_stream
                for response in text_stream:
                    yield response

        return StreamingResponse(stream_response(), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
