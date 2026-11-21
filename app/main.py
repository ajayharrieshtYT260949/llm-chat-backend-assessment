
from fastapi import FastAPI

from app.routes.chat import router as chat_router
from app.routes.usage import router as usage_router

app = FastAPI(
    title="LLM Chat Backend",
    description="Multi-provider LLM integration with streaming and usage tracking",
    version="1.0.0",
)

app.include_router(chat_router)
app.include_router(usage_router)


@app.get("/")
def root():
    return {
        "message": "LLM Chat Backend is running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
