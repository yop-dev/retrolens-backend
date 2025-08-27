"""Categories endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException
from app.db.supabase import supabase_client
from app.schemas.discussion import Category

router = APIRouter()


@router.get("/", response_model=List[Category])
async def list_categories():
    """List all discussion categories."""
    try:
        result = supabase_client.table("discussion_categories").select("*").order("display_order").execute()
        return result.data if result.data else []
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
