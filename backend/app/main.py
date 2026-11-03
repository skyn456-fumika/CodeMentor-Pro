from fastapi import FastAPI

from backend.app.api.browser_login_page import (
    router as browser_login_page_router,
)
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.chats import router as chats_router
from backend.app.api.v1.reviews import router as reviews_router

app = FastAPI(
    title="CodeMentor Pro API",
    description="AI-powered Code Review Platform",
    version="0.1.0",
)

app.include_router(reviews_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(chats_router, prefix="/api/v1")
app.include_router(
    browser_login_page_router,
    prefix="/api/v1/auth",
    tags=["Browser Authentication"],
)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "CodeMentor Pro",
    }
