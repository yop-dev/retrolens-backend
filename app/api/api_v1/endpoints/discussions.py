"""Discussion endpoints - simplified for initial testing."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Body
from app.db.supabase import supabase_client
from app.schemas.discussion import DiscussionCreate, DiscussionPublic

router = APIRouter()


@router.get("/")
async def list_discussions(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0)
):
    """List all discussions."""
    try:
        result = supabase_client.table("discussions").select("*").order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        
        # Map database 'body' field to 'content' for API response
        discussions = result.data if result.data else []
        for discussion in discussions:
            if 'body' in discussion:
                discussion['content'] = discussion.pop('body', '')
        
        return discussions
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{discussion_id}", response_model=DiscussionPublic)
async def get_discussion(discussion_id: str):
    """Get a discussion by ID."""
    try:
        result = supabase_client.table("discussions").select("*").eq("id", discussion_id).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Discussion not found")
        
        # Map database 'body' field to 'content' for API response
        if result.data and 'body' in result.data:
            result.data['content'] = result.data.pop('body', '')
        
        return result.data
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/")
async def create_discussion(
    user_id: str = Query(..., description="User ID (Clerk ID)"),
    body: DiscussionCreate = Body(...)
):
    """Create a new discussion."""
    try:
        discussion_data = body.model_dump(exclude_none=True)
        
        # Map 'content' field to 'body' for database
        if 'content' in discussion_data:
            discussion_data['body'] = discussion_data.pop('content')
        
        # Add user_id
        discussion_data["user_id"] = user_id
        
        # Remove category_id if it's None or 0
        if discussion_data.get('category_id') in [None, 0]:
            discussion_data.pop('category_id', None)
        
        result = supabase_client.table("discussions").insert(discussion_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to create discussion")
        
        # Map database 'body' field back to 'content' for API response
        response_data = result.data[0]
        if 'body' in response_data:
            response_data['content'] = response_data.pop('body', '')
        
        return response_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
