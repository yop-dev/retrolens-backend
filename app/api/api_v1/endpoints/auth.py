"""Authentication endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import get_current_user, require_user
from app.db.supabase import supabase_client
from app.schemas.user import UserCreate, UserPublic

router = APIRouter()


@router.get("/me")
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(require_user)
) -> Dict[str, Any]:
    """Get current authenticated user information."""
    return {
        "clerk_id": current_user.get("sub"),
        "email": current_user.get("email"),
        "name": current_user.get("name"),
        "authenticated": True
    }


@router.post("/sync-user", response_model=UserPublic)
async def sync_user_with_database(
    current_user: Dict[str, Any] = Depends(require_user)
):
    """Sync authenticated user with database (create if not exists)."""
    clerk_id = current_user.get("sub")
    email = current_user.get("email")
    name = current_user.get("name", "")
    
    # Extract first name and username
    first_name = name.split()[0] if name else ""
    username = email.split("@")[0] if email else f"user_{clerk_id[:8]}"
    
    try:
        # Check if user exists
        existing = supabase_client.table("users").select("*").eq("id", clerk_id).execute()
        
        if existing.data:
            # User exists, return it
            return existing.data[0]
        
        # Create new user
        user_data = {
            "id": clerk_id,
            "username": username,
            "display_name": name or username,
            "email": email
        }
        
        # Check if username is taken
        username_check = supabase_client.table("users").select("id").eq("username", username).execute()
        if username_check.data:
            # Username taken, append random number
            import random
            user_data["username"] = f"{username}_{random.randint(1000, 9999)}"
        
        result = supabase_client.table("users").insert(user_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to create user")
        
        return result.data[0]
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/verify-token")
async def verify_token(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Verify if the token is valid."""
    return {
        "valid": True,
        "user_id": current_user.get("sub")
    }
