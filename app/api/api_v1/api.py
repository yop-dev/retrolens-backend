"""Main API router that combines all endpoints."""

from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    auth,
    users,
    cameras,
    discussions,
    comments,
    upload,
    categories,
    test_sync,
    follows,
    likes
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(test_sync.router, prefix="/test", tags=["test"])
api_router.include_router(cameras.router, prefix="/cameras", tags=["cameras"])
api_router.include_router(discussions.router, prefix="/discussions", tags=["discussions"])
api_router.include_router(comments.router, prefix="/comments", tags=["comments"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
api_router.include_router(follows.router, prefix="/follows", tags=["follows"])
api_router.include_router(likes.router, prefix="/likes", tags=["likes"])
