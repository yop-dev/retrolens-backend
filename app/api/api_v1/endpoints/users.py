"""User endpoints."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from app.db.supabase import supabase_client
from app.schemas.user import UserCreate, UserUpdate, UserPublic
from app.core.auth import get_current_user, get_current_user_optional
from pydantic import BaseModel

router = APIRouter()

@router.post("/test-sync")
async def test_sync():
    """Test endpoint without any dependencies."""
    return {"message": "Test sync endpoint working"}

class UserSyncRequest(BaseModel):
    """Schema for syncing user from Clerk."""
    clerk_id: str
    email: str  # Changed from EmailStr to str to avoid validation issues
    username: str
    full_name: Optional[str] = ""
    avatar_url: Optional[str] = ""
    metadata: Optional[Dict[str, Any]] = {}


@router.post("/sync", dependencies=[])
async def sync_user(request: UserSyncRequest):
    """Sync user data from Clerk to our database."""
    try:
        # Check if user already exists by id (which stores the clerk_id)
        existing = supabase_client.table("users").select("*").eq("id", request.clerk_id).execute()
        
        if existing.data:
            # Update existing user - but don't update username if it would cause a conflict
            user_id = existing.data[0]["id"]
            
            # Check if the requested username is taken by another user
            username_to_use = request.username
            if existing.data[0].get("username") != request.username:
                username_check = supabase_client.table("users").select("id").eq("username", request.username).execute()
                if username_check.data and username_check.data[0]["id"] != user_id:
                    # Username is taken by another user, keep existing username
                    username_to_use = existing.data[0].get("username")
            
            update_data = {
                "email": request.email,
                "username": username_to_use,
                "display_name": request.full_name or existing.data[0].get("display_name", ""),
                "avatar_url": request.avatar_url or existing.data[0].get("avatar_url", ""),
                "updated_at": "now()"
            }
            result = supabase_client.table("users").update(update_data).eq("id", user_id).execute()
            
            return {
                "message": "User updated successfully",
                "user_id": user_id,
                "clerk_id": request.clerk_id
            }
        else:
            # Create new user
            # Check if username is already taken
            username_to_use = request.username
            username_check = supabase_client.table("users").select("id").eq("username", request.username).execute()
            if username_check.data:
                # Username is taken, generate a unique one
                import random
                username_to_use = f"{request.username}_{random.randint(1000, 9999)}"
                # Keep trying until we find an available username
                while True:
                    check = supabase_client.table("users").select("id").eq("username", username_to_use).execute()
                    if not check.data:
                        break
                    username_to_use = f"{request.username}_{random.randint(1000, 9999)}"
            
            user_data = {
                "id": request.clerk_id,  # Use id field to store clerk_id
                "email": request.email,
                "username": username_to_use,
                "display_name": request.full_name or request.username,  # Use display_name instead of full_name
                "avatar_url": request.avatar_url,
                "bio": "",
                "location": "",
                "expertise_level": "beginner"
            }
            result = supabase_client.table("users").insert(user_data).execute()
            
            if not result.data:
                raise HTTPException(status_code=400, detail="Failed to create user")
            
            return {
                "message": "User created successfully",
                "user_id": result.data[0]["id"],
                "clerk_id": request.clerk_id
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/", response_model=UserPublic)
async def create_user(user_in: UserCreate):
    """Create a new user."""
    try:
        # Check if username already exists
        existing = supabase_client.table("users").select("*").eq("username", user_in.username).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Create user in database
        user_data = user_in.model_dump()
        # Generate a unique ID if not provided (for non-Clerk users)
        import uuid
        user_data["id"] = str(uuid.uuid4())
        
        result = supabase_client.table("users").insert(user_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to create user")
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(user_id: str):
    """Get a user by ID."""
    try:
        result = supabase_client.table("users").select("*").eq("id", str(user_id)).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        user = result.data
        
        # Get additional stats
        cameras = supabase_client.table("cameras").select("id").eq("user_id", str(user_id)).execute()
        discussions = supabase_client.table("discussions").select("id").eq("user_id", str(user_id)).execute()
        followers = supabase_client.table("follows").select("id").eq("following_id", str(user_id)).execute()
        following = supabase_client.table("follows").select("id").eq("follower_id", str(user_id)).execute()
        
        user["camera_count"] = len(cameras.data) if cameras.data else 0
        user["discussion_count"] = len(discussions.data) if discussions.data else 0
        user["follower_count"] = len(followers.data) if followers.data else 0
        user["following_count"] = len(following.data) if following.data else 0
        
        return user
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/username/{username}", response_model=UserPublic)
async def get_user_by_username(username: str):
    """Get a user by username."""
    try:
        result = supabase_client.table("users").select("*").eq("username", username).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        user = result.data
        
        # Get additional stats
        cameras = supabase_client.table("cameras").select("id").eq("user_id", user["id"]).execute()
        discussions = supabase_client.table("discussions").select("id").eq("user_id", user["id"]).execute()
        followers = supabase_client.table("follows").select("id").eq("following_id", user["id"]).execute()
        following = supabase_client.table("follows").select("id").eq("follower_id", user["id"]).execute()
        
        user["camera_count"] = len(cameras.data) if cameras.data else 0
        user["discussion_count"] = len(discussions.data) if discussions.data else 0
        user["follower_count"] = len(followers.data) if followers.data else 0
        user["following_count"] = len(following.data) if following.data else 0
        
        return user
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{user_id}", response_model=UserPublic)
async def update_user(user_id: str, user_update: UserUpdate):
    """Update a user."""
    try:
        # Update user
        update_data = user_update.model_dump(exclude_unset=True)
        result = supabase_client.table("users").update(update_data).eq("id", str(user_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[UserPublic])
async def list_users(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0)
):
    """List all users."""
    try:
        result = supabase_client.table("users").select("*").range(offset, offset + limit - 1).execute()
        return result.data if result.data else []
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}/followers")
async def get_user_followers(user_id: str):
    """Get list of users who follow this user."""
    try:
        # Get follower relationships
        follows = supabase_client.table("follows").select("follower_id").eq("following_id", str(user_id)).execute()
        
        if not follows.data:
            return []
        
        # Get user details for each follower
        follower_ids = [f["follower_id"] for f in follows.data]
        followers = []
        
        for follower_id in follower_ids:
            user_result = supabase_client.table("users").select("id,username,display_name,avatar_url,bio").eq("id", follower_id).single().execute()
            if user_result.data:
                followers.append(user_result.data)
        
        return followers
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}/following")
async def get_user_following(user_id: str):
    """Get list of users this user follows."""
    try:
        # Get following relationships
        follows = supabase_client.table("follows").select("following_id").eq("follower_id", str(user_id)).execute()
        
        if not follows.data:
            return []
        
        # Get user details for each followed user
        following_ids = [f["following_id"] for f in follows.data]
        following = []
        
        for following_id in following_ids:
            user_result = supabase_client.table("users").select("id,username,display_name,avatar_url,bio").eq("id", following_id).single().execute()
            if user_result.data:
                following.append(user_result.data)
        
        return following
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{user_id}/follow")
async def follow_user(user_id: str, request_data: dict):
    """Follow a user."""
    try:
        follower_id = request_data.get("follower_id")
        if not follower_id:
            raise HTTPException(status_code=400, detail="follower_id is required")
            
        if user_id == follower_id:
            raise HTTPException(status_code=400, detail="Cannot follow yourself")
        
        # Check if already following
        existing = supabase_client.table("follows").select("*").eq("follower_id", str(follower_id)).eq("following_id", str(user_id)).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Already following this user")
        
        # Create follow relationship
        result = supabase_client.table("follows").insert({
            "follower_id": str(follower_id),
            "following_id": str(user_id)
        }).execute()
        
        return {"message": "Successfully followed user"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{user_id}/unfollow")
async def unfollow_user(user_id: str, request_data: dict):
    """Unfollow a user."""
    try:
        follower_id = request_data.get("follower_id")
        if not follower_id:
            raise HTTPException(status_code=400, detail="follower_id is required")
            
        result = supabase_client.table("follows").delete().eq("follower_id", str(follower_id)).eq("following_id", str(user_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Follow relationship not found")
        
        return {"message": "Successfully unfollowed user"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

