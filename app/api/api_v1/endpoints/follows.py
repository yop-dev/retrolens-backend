"""Follow relationships endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException, Query
from app.db.supabase import supabase_client
from pydantic import BaseModel

router = APIRouter()


class FollowRelation(BaseModel):
    """Follow relationship model."""
    id: str
    follower_id: str
    following_id: str
    created_at: str


@router.get("/", response_model=List[FollowRelation])
async def list_follows(
    follower_id: str = Query(default=None),
    following_id: str = Query(default=None)
):
    """List follow relationships."""
    try:
        query = supabase_client.table("follows").select("*")
        
        if follower_id:
            query = query.eq("follower_id", follower_id)
        
        if following_id:
            query = query.eq("following_id", following_id)
        
        result = query.execute()
        return result.data if result.data else []
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/")
async def create_follow(follower_id: str, following_id: str):
    """Create a follow relationship."""
    try:
        if follower_id == following_id:
            raise HTTPException(status_code=400, detail="Cannot follow yourself")
        
        # Check if already following
        existing = supabase_client.table("follows").select("*").eq("follower_id", follower_id).eq("following_id", following_id).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Already following this user")
        
        # Create follow relationship
        result = supabase_client.table("follows").insert({
            "follower_id": follower_id,
            "following_id": following_id
        }).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to create follow relationship")
        
        return {"message": "Follow successful", "data": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/")
async def delete_follow(follower_id: str, following_id: str):
    """Delete a follow relationship (unfollow)."""
    try:
        result = supabase_client.table("follows").delete().eq("follower_id", follower_id).eq("following_id", following_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Follow relationship not found")
        
        return {"message": "Unfollow successful"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
