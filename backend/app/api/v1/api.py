from fastapi import APIRouter

from app.api.v1.endpoints import auth, chat

api_router = APIRouter()

# Include auth routes
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Include chat routes
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])