"""Likes endpoints with follow relationship checks."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from app.db.supabase import supabase_client
from app.core.auth import get_current_user
from pydantic import BaseModel

router = APIRouter()


class LikeRequest(BaseModel):
    """Request model for likes."""
    discussion_id: Optional[str] = None
    camera_id: Optional[str] = None
    comment_id: Optional[str] = None


async def check_users_follow_each_other(user1_id: str, user2_id: str) -> bool:
    """Check if two users follow each other (mutual follow)."""
    if user1_id == user2_id:
        return True  # Users can like their own posts
    
    try:
        # Check if user1 follows user2
        follow1 = supabase_client.table("follows").select("id").eq("follower_id", user1_id).eq("following_id", user2_id).execute()
        
        # Check if user2 follows user1
        follow2 = supabase_client.table("follows").select("id").eq("follower_id", user2_id).eq("following_id", user1_id).execute()
        
        return bool(follow1.data) and bool(follow2.data)
    except Exception:
        return False


async def get_content_owner_id(discussion_id: Optional[str] = None, camera_id: Optional[str] = None, comment_id: Optional[str] = None) -> Optional[str]:
    """Get the owner ID of the content being liked."""
    try:
        if discussion_id:
            result = supabase_client.table("discussions").select("user_id").eq("id", discussion_id).single().execute()
            return result.data["user_id"] if result.data else None
        elif camera_id:
            result = supabase_client.table("cameras").select("user_id").eq("id", camera_id).single().execute()
            return result.data["user_id"] if result.data else None
        elif comment_id:
            result = supabase_client.table("comments").select("user_id").eq("id", comment_id).single().execute()
            return result.data["user_id"] if result.data else None
    except Exception:
        return None
    return None


@router.post("/")
async def create_like(
    like_data: LikeRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a like (only if users follow each other)."""
    try:
        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
        # Validate that exactly one target is provided
        targets = [like_data.discussion_id, like_data.camera_id, like_data.comment_id]
        non_null_targets = [t for t in targets if t is not None]
        
        if len(non_null_targets) != 1:
            raise HTTPException(status_code=400, detail="Exactly one of discussion_id, camera_id, or comment_id must be provided")
        
        # Get the content owner
        content_owner_id = await get_content_owner_id(
            like_data.discussion_id, 
            like_data.camera_id, 
            like_data.comment_id
        )
        if not content_owner_id:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Check if users follow each other (or if liking own content)
        if not await check_users_follow_each_other(user_id, content_owner_id):
            raise HTTPException(status_code=403, detail="You can only like posts from users you mutually follow")
        
        # Check if already liked
        existing_like = supabase_client.table("likes").select("id").eq("user_id", user_id)
        
        if like_data.discussion_id:
            existing_like = existing_like.eq("discussion_id", like_data.discussion_id)
        elif like_data.camera_id:
            existing_like = existing_like.eq("camera_id", like_data.camera_id)
        elif like_data.comment_id:
            existing_like = existing_like.eq("comment_id", like_data.comment_id)
        
        existing_result = existing_like.execute()
        if existing_result.data:
            raise HTTPException(status_code=400, detail="Already liked this content")
        
        # Create the like
        like_insert_data = {
            "user_id": user_id,
            "discussion_id": like_data.discussion_id,
            "camera_id": like_data.camera_id,
            "comment_id": like_data.comment_id
        }
        
        result = supabase_client.table("likes").insert(like_insert_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to create like")
        
        return {"message": "Like created successfully", "like_id": result.data[0]["id"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/")
async def delete_like(
    like_data: LikeRequest,
    current_user: dict = Depends(get_current_user)
):
    """Remove a like."""
    try:
        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
        # Validate that exactly one target is provided
        targets = [like_data.discussion_id, like_data.camera_id, like_data.comment_id]
        non_null_targets = [t for t in targets if t is not None]
        
        if len(non_null_targets) != 1:
            raise HTTPException(status_code=400, detail="Exactly one of discussion_id, camera_id, or comment_id must be provided")
        
        # Find and delete the like
        delete_query = supabase_client.table("likes").delete().eq("user_id", user_id)
        
        if like_data.discussion_id:
            delete_query = delete_query.eq("discussion_id", like_data.discussion_id)
        elif like_data.camera_id:
            delete_query = delete_query.eq("camera_id", like_data.camera_id)
        elif like_data.comment_id:
            delete_query = delete_query.eq("comment_id", like_data.comment_id)
        
        result = delete_query.execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Like not found")
        
        return {"message": "Like removed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/check")
async def check_like_status(
    discussion_id: Optional[str] = None,
    camera_id: Optional[str] = None,
    comment_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Check if current user has liked the content."""
    try:
        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
        # Validate that exactly one target is provided
        targets = [discussion_id, camera_id, comment_id]
        non_null_targets = [t for t in targets if t is not None]
        
        if len(non_null_targets) != 1:
            raise HTTPException(status_code=400, detail="Exactly one of discussion_id, camera_id, or comment_id must be provided")
        
        # Check if like exists
        like_query = supabase_client.table("likes").select("id").eq("user_id", user_id)
        
        if discussion_id:
            like_query = like_query.eq("discussion_id", discussion_id)
        elif camera_id:
            like_query = like_query.eq("camera_id", camera_id)
        elif comment_id:
            like_query = like_query.eq("comment_id", comment_id)
        
        result = like_query.execute()
        
        return {"is_liked": bool(result.data)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/count")
async def get_like_count(
    discussion_id: Optional[str] = None,
    camera_id: Optional[str] = None,
    comment_id: Optional[str] = None
):
    """Get like count for content."""
    try:
        # Validate that exactly one target is provided
        targets = [discussion_id, camera_id, comment_id]
        non_null_targets = [t for t in targets if t is not None]
        
        if len(non_null_targets) != 1:
            raise HTTPException(status_code=400, detail="Exactly one of discussion_id, camera_id, or comment_id must be provided")
        
        # Count likes
        count_query = supabase_client.table("likes").select("id", count="exact")
        
        if discussion_id:
            count_query = count_query.eq("discussion_id", discussion_id)
        elif camera_id:
            count_query = count_query.eq("camera_id", camera_id)
        elif comment_id:
            count_query = count_query.eq("comment_id", comment_id)
        
        result = count_query.execute()
        
        return {"like_count": result.count or 0}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))