"""Comments endpoints - simplified for initial testing."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_comments():
    """List comments - placeholder."""
    return {"message": "Comments endpoint - coming soon"}
