"""Test sync endpoint without any dependencies."""

from typing import Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel
from app.db.supabase import supabase_client

router = APIRouter()

class UserSyncRequest(BaseModel):
    """Schema for syncing user from Clerk."""
    clerk_id: str
    email: str
    username: str
    full_name: str = ""
    avatar_url: str = ""
    metadata: Dict[str, Any] = {}

@router.post("/sync")
async def sync_user_test(request: UserSyncRequest):
    """Sync user data from Clerk to our database - test version."""
    try:
        # Check if user already exists by id (which stores the clerk_id)
        existing = supabase_client.table("users").select("*").eq("id", request.clerk_id).execute()
        
        if existing.data:
            # Update existing user
            user_id = existing.data[0]["id"]
            update_data = {
                "email": request.email,
                "username": request.username,
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
            user_data = {
                "id": request.clerk_id,  # Use id field to store clerk_id
                "email": request.email,
                "username": request.username,
                "display_name": request.full_name,  # Use display_name instead of full_name
                "avatar_url": request.avatar_url,
                "bio": "",
                "location": "",
                "expertise_level": "beginner"
            }
            result = supabase_client.table("users").insert(user_data).execute()
            
            if not result.data:
                return {"error": "Failed to create user"}
            
            return {
                "message": "User created successfully",
                "user_id": result.data[0]["id"],
                "clerk_id": request.clerk_id
            }
    except Exception as e:
        return {"error": str(e)}

@router.get("/test")
async def test_endpoint():
    """Simple test endpoint."""
    return {"message": "Test endpoint working"}