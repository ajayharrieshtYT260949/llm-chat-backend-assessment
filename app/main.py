
from fastapi import FastAPI

from app.routes.chat import router as chat_router
from app.routes.usage import router as usage_router
from app.routes.sessions import router as sessions_router

from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.exceptions import register_exception_handlers


app = FastAPI(
    title="LLM Chat Backend",
    description=(
        "Multi-provider LLM integration with streaming, "
        "usage tracking, and session-based conversations."
    ),
    version="1.0.0",
)

register_exception_handlers(app)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register existing Task 1–3 routers.
app.include_router(chat_router)
app.include_router(usage_router)

# Register Task 4 session router.
app.include_router(sessions_router)


@app.get("/")
def root():
    return {
        "message": "LLM Chat Backend is running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
