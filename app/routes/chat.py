
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.llm.service import stream_openai
from app.llm.token_counter import validate_token_budget

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1)


@router.post("/chat/stream")
def chat_stream(request: ChatRequest):
    # Validate before starting the streaming response.
    try:
        validate_token_budget([
            {"role": "user", "content": request.prompt}
        ])
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc

    def event_generator():
        try:
            for delta in stream_openai(request.prompt):
                payload = json.dumps({"delta": delta})
                yield f"data: {payload}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as exc:
            error_payload = json.dumps({"error": str(exc)})
            yield f"event: error\ndata: {error_payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
