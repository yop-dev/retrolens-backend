"""Comments endpoints with follow relationship checks."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, Depends
from app.db.supabase import supabase_client
from app.schemas.discussion import CommentCreate, CommentPublic, CommentUpdate
from app.core.auth import get_current_user
from pydantic import BaseModel

router = APIRouter()


class CommentCreateRequest(BaseModel):
    """Request model for creating comments."""
    body: str
    discussion_id: Optional[str] = None
    camera_id: Optional[str] = None
    parent_id: Optional[str] = None


async def check_users_follow_each_other(user1_id: str, user2_id: str) -> bool:
    """Check if two users follow each other (mutual follow)."""
    if user1_id == user2_id:
        return True  # Users can comment on their own posts
    
    try:
        # Check if user1 follows user2
        follow1 = supabase_client.table("follows").select("id").eq("follower_id", user1_id).eq("following_id", user2_id).execute()
        
        # Check if user2 follows user1
        follow2 = supabase_client.table("follows").select("id").eq("follower_id", user2_id).eq("following_id", user1_id).execute()
        
        return bool(follow1.data) and bool(follow2.data)
    except Exception:
        return False


async def get_content_owner_id(discussion_id: Optional[str] = None, camera_id: Optional[str] = None) -> Optional[str]:
    """Get the owner ID of the content being commented on."""
    try:
        if discussion_id:
            result = supabase_client.table("discussions").select("user_id").eq("id", discussion_id).single().execute()
            return result.data["user_id"] if result.data else None
        elif camera_id:
            result = supabase_client.table("cameras").select("user_id").eq("id", camera_id).single().execute()
            return result.data["user_id"] if result.data else None
    except Exception:
        return None
    return None


@router.get("/")
async def list_comments(
    discussion_id: Optional[str] = Query(None),
    camera_id: Optional[str] = Query(None),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0)
):
    """List comments for a discussion or camera."""
    try:
        if not discussion_id and not camera_id:
            raise HTTPException(status_code=400, detail="Either discussion_id or camera_id must be provided")
        
        query = supabase_client.table("comments").select("""
            id, user_id, discussion_id, camera_id, parent_id, body, is_edited, created_at, updated_at,
            users!comments_user_id_fkey(username, avatar_url)
        """)
        
        if discussion_id:
            query = query.eq("discussion_id", discussion_id)
        elif camera_id:
            query = query.eq("camera_id", camera_id)
        
        result = query.order("created_at", desc=False).range(offset, offset + limit - 1).execute()
        
        comments = []
        for comment in result.data or []:
            # Get like count for each comment
            like_count_result = supabase_client.table("likes").select("id", count="exact").eq("comment_id", comment["id"]).execute()
            like_count = like_count_result.count or 0
            
            comment_data = {
                **comment,
                "author_username": comment["users"]["username"] if comment.get("users") else None,
                "author_avatar": comment["users"]["avatar_url"] if comment.get("users") else None,
                "like_count": like_count,
                "is_liked": False  # Will be set by frontend based on current user
            }
            comment_data.pop("users", None)
            comments.append(comment_data)
        
        return comments
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/")
async def create_comment(
    comment_data: CommentCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new comment (only if users follow each other)."""
    try:
        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
        # Validate that either discussion_id or camera_id is provided
        if not comment_data.discussion_id and not comment_data.camera_id:
            raise HTTPException(status_code=400, detail="Either discussion_id or camera_id must be provided")
        
        if comment_data.discussion_id and comment_data.camera_id:
            raise HTTPException(status_code=400, detail="Cannot specify both discussion_id and camera_id")
        
        # Get the content owner
        content_owner_id = await get_content_owner_id(comment_data.discussion_id, comment_data.camera_id)
        if not content_owner_id:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Check if users follow each other (or if commenting on own content)
        if not await check_users_follow_each_other(user_id, content_owner_id):
            raise HTTPException(status_code=403, detail="You can only comment on posts from users you mutually follow")
        
        # Create the comment
        comment_insert_data = {
            "user_id": user_id,
            "body": comment_data.body,
            "discussion_id": comment_data.discussion_id,
            "camera_id": comment_data.camera_id,
            "parent_id": comment_data.parent_id
        }
        
        result = supabase_client.table("comments").insert(comment_insert_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to create comment")
        
        # Get the created comment with user info
        comment_id = result.data[0]["id"]
        comment_result = supabase_client.table("comments").select("""
            id, user_id, discussion_id, camera_id, parent_id, body, is_edited, created_at, updated_at,
            users!comments_user_id_fkey(username, avatar_url)
        """).eq("id", comment_id).single().execute()
        
        comment = comment_result.data
        return {
            **comment,
            "author_username": comment["users"]["username"] if comment.get("users") else None,
            "author_avatar": comment["users"]["avatar_url"] if comment.get("users") else None,
            "like_count": 0,
            "is_liked": False
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{comment_id}")
async def update_comment(
    comment_id: str,
    comment_data: CommentUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a comment (only by the author)."""
    try:
        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
        # Check if comment exists and user owns it
        existing_comment = supabase_client.table("comments").select("user_id").eq("id", comment_id).single().execute()
        if not existing_comment.data:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        if existing_comment.data["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="You can only edit your own comments")
        
        # Update the comment
        update_data = {"body": comment_data.body, "is_edited": True}
        result = supabase_client.table("comments").update(update_data).eq("id", comment_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to update comment")
        
        return {"message": "Comment updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a comment (only by the author)."""
    try:
        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
        # Check if comment exists and user owns it
        existing_comment = supabase_client.table("comments").select("user_id").eq("id", comment_id).single().execute()
        if not existing_comment.data:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        if existing_comment.data["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="You can only delete your own comments")
        
        # Delete the comment
        result = supabase_client.table("comments").delete().eq("id", comment_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to delete comment")
        
        return {"message": "Comment deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
