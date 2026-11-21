
from fastapi import APIRouter, Depends, HTTPException, status
from openai import AsyncOpenAI

from app.auth import verify_api_key
from app.config import Settings
from app.dependencies import (
    get_app_settings,
    get_llm_client,
    get_session_store,
)
from app.llm.token_counter import validate_token_budget
from app.sessions.schemas import (
    ChatRequest,
    ChatResponse,
    MessageHistoryResponse,
    MessageResponse,
    SessionCreateResponse,
)
from app.sessions.store import SessionStore


router = APIRouter(
    prefix="/sessions",
    tags=["sessions"],
    dependencies=[Depends(verify_api_key)],
)


@router.post(
    "",
    response_model=SessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_session(
    store: SessionStore = Depends(get_session_store),
):
    """Create a new conversation session."""

    return store.create_session()


@router.post(
    "/{session_id}/chat",
    response_model=ChatResponse,
)
async def chat_in_session(
    session_id: str,
    request: ChatRequest,
    store: SessionStore = Depends(get_session_store),
    client: AsyncOpenAI = Depends(get_llm_client),
    settings: Settings = Depends(get_app_settings),
):
    """Send a message within an existing conversation session."""

    session = store.get_session(session_id)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    if len(request.message) > 2000:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Message cannot exceed 2000 characters.",
        )

    # Reconstruct the existing conversation.
    messages = [
        {
            "role": message["role"],
            "content": message["content"],
        }
        for message in session["messages"]
    ]

    # Add the new user message to the request context.
    messages.append(
        {
            "role": "user",
            "content": request.message,
        }
    )

    try:
        # Validate the complete conversation token budget.
        validate_token_budget(messages)

        # Send the conversation to the LLM.
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            max_tokens=settings.max_output_tokens,
        )

        assistant_content = (
            response.choices[0].message.content or ""
        )

        # Save messages only after a successful LLM response.
        store.add_message(
            session_id,
            "user",
            request.message,
        )

        assistant_message = store.add_message(
            session_id,
            "assistant",
            assistant_content,
        )

        return ChatResponse(
            session_id=session_id,
            message=MessageResponse(**assistant_message),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=str(exc),
        ) from exc

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The language model service is temporarily unavailable.",
        ) from exc


@router.get(
    "/{session_id}/messages",
    response_model=MessageHistoryResponse,
)
def get_session_messages(
    session_id: str,
    store: SessionStore = Depends(get_session_store),
):
    """Retrieve all messages belonging to a session."""

    messages = store.get_messages(session_id)

    if messages is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    return MessageHistoryResponse(
        session_id=session_id,
        messages=messages,
        total_messages=len(messages),
    )
