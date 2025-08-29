"""Discussion endpoints - simplified for initial testing."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Body, Depends
from app.db.supabase import supabase_client
from app.schemas.discussion import DiscussionCreate, DiscussionPublic, DiscussionUpdate
from app.core.auth import get_current_user_optional, get_current_user

router = APIRouter()


@router.get("/")
async def list_discussions(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    sortBy: Optional[str] = Query(default="created_at"),
    sortOrder: Optional[str] = Query(default="desc"),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """List all discussions."""
    try:
        # Validate sort parameters
        valid_sort_fields = ["created_at", "updated_at", "title", "view_count"]
        if sortBy not in valid_sort_fields:
            sortBy = "created_at"
        
        desc = sortOrder.lower() == "desc"
        
        # Get discussions with author info
        result = supabase_client.table("discussions").select("""
            id, user_id, category_id, title, body, tags, is_pinned, is_locked, view_count, created_at, updated_at,
            users!discussions_user_id_fkey(username, avatar_url),
            discussion_categories!discussions_category_id_fkey(name)
        """).order(sortBy, desc=desc).range(offset, offset + limit - 1).execute()
        
        discussions = []
        user_id = current_user.get("sub") if current_user else None
        
        for discussion in result.data or []:
            # Get like count
            like_count_result = supabase_client.table("likes").select("id", count="exact").eq("discussion_id", discussion["id"]).execute()
            like_count = like_count_result.count or 0
            
            # Check if current user liked this discussion
            is_liked = False
            if user_id:
                user_like = supabase_client.table("likes").select("id").eq("user_id", user_id).eq("discussion_id", discussion["id"]).execute()
                is_liked = bool(user_like.data)
            
            # Get comment count
            comment_count_result = supabase_client.table("comments").select("id", count="exact").eq("discussion_id", discussion["id"]).execute()
            comment_count = comment_count_result.count or 0
            
            # Map database 'body' field to 'content' for API response
            discussion_data = {
                **discussion,
                "content": discussion.pop("body", ""),
                "author_username": discussion["users"]["username"] if discussion.get("users") else None,
                "author_avatar": discussion["users"]["avatar_url"] if discussion.get("users") else None,
                "category_name": discussion["discussion_categories"]["name"] if discussion.get("discussion_categories") else None,
                "like_count": like_count,
                "is_liked": is_liked,
                "comment_count": comment_count
            }
            discussion_data.pop("users", None)
            discussion_data.pop("discussion_categories", None)
            discussions.append(discussion_data)
        
        return discussions
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{discussion_id}", response_model=DiscussionPublic)
async def get_discussion(
    discussion_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get a discussion by ID."""
    try:
        # Get discussion with author and category info
        result = supabase_client.table("discussions").select("""
            id, user_id, category_id, title, body, tags, is_pinned, is_locked, view_count, created_at, updated_at,
            users!discussions_user_id_fkey(username, avatar_url),
            discussion_categories!discussions_category_id_fkey(name)
        """).eq("id", discussion_id).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Discussion not found")
        
        discussion = result.data
        user_id = current_user.get("sub") if current_user else None
        
        # Get like count
        like_count_result = supabase_client.table("likes").select("id", count="exact").eq("discussion_id", discussion_id).execute()
        like_count = like_count_result.count or 0
        
        # Check if current user liked this discussion
        is_liked = False
        if user_id:
            user_like = supabase_client.table("likes").select("id").eq("user_id", user_id).eq("discussion_id", discussion_id).execute()
            is_liked = bool(user_like.data)
        
        # Get comment count
        comment_count_result = supabase_client.table("comments").select("id", count="exact").eq("discussion_id", discussion_id).execute()
        comment_count = comment_count_result.count or 0
        
        # Increment view count
        supabase_client.table("discussions").update({"view_count": discussion["view_count"] + 1}).eq("id", discussion_id).execute()
        
        # Map database 'body' field to 'content' for API response
        discussion_data = {
            **discussion,
            "content": discussion.pop("body", ""),
            "author_username": discussion["users"]["username"] if discussion.get("users") else None,
            "author_avatar": discussion["users"]["avatar_url"] if discussion.get("users") else None,
            "category_name": discussion["discussion_categories"]["name"] if discussion.get("discussion_categories") else None,
            "like_count": like_count,
            "is_liked": is_liked,
            "comment_count": comment_count
        }
        discussion_data.pop("users", None)
        discussion_data.pop("discussion_categories", None)
        
        return discussion_data
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


@router.put("/{discussion_id}")
async def update_discussion(
    discussion_id: str,
    user_id: str = Query(..., description="User ID (Clerk ID)"),
    body: DiscussionUpdate = Body(...)
):
    """Update a discussion. Only the author can update their discussion."""
    try:
        # First, check if the discussion exists and belongs to the user
        existing_result = supabase_client.table("discussions").select("user_id").eq("id", discussion_id).single().execute()
        
        if not existing_result.data:
            raise HTTPException(status_code=404, detail="Discussion not found")
        
        if existing_result.data["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="You can only edit your own discussions")
        
        # Prepare update data
        update_data = body.model_dump(exclude_none=True)
        
        # Map 'content' field to 'body' for database
        if 'content' in update_data:
            update_data['body'] = update_data.pop('content')
        
        # Add updated_at timestamp
        from datetime import datetime
        update_data['updated_at'] = datetime.utcnow().isoformat()
        
        # Update the discussion
        result = supabase_client.table("discussions").update(update_data).eq("id", discussion_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to update discussion")
        
        # Map database 'body' field back to 'content' for API response
        response_data = result.data[0]
        if 'body' in response_data:
            response_data['content'] = response_data.pop('body', '')
        
        return response_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{discussion_id}")
async def delete_discussion(
    discussion_id: str,
    user_id: str = Query(..., description="User ID (Clerk ID)")
):
    """Delete a discussion. Only the author can delete their discussion."""
    try:
        # First, check if the discussion exists and belongs to the user
        existing_result = supabase_client.table("discussions").select("user_id").eq("id", discussion_id).single().execute()
        
        if not existing_result.data:
            raise HTTPException(status_code=404, detail="Discussion not found")
        
        if existing_result.data["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="You can only delete your own discussions")
        
        # Delete related data first (comments, likes)
        # Delete comments
        supabase_client.table("comments").delete().eq("discussion_id", discussion_id).execute()
        
        # Delete likes
        supabase_client.table("likes").delete().eq("discussion_id", discussion_id).execute()
        
        # Delete the discussion
        result = supabase_client.table("discussions").delete().eq("id", discussion_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to delete discussion")
        
        return {"message": "Discussion deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
