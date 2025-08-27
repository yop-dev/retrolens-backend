"""Camera endpoints - simplified for initial testing."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from app.db.supabase import supabase_client
from app.schemas.camera import CameraCreate, CameraUpdate, CameraPublic

router = APIRouter()


@router.get("/", response_model=List[CameraPublic])
async def list_cameras(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0)
):
    """List all public cameras."""
    try:
        result = supabase_client.table("cameras").select("*").eq("is_public", True).range(offset, offset + limit - 1).execute()
        return result.data if result.data else []
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{camera_id}", response_model=CameraPublic)
async def get_camera(camera_id: UUID):
    """Get a camera by ID."""
    try:
        result = supabase_client.table("cameras").select("*").eq("id", str(camera_id)).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        camera = result.data
        
        # Get camera images
        images = supabase_client.table("camera_images").select("*").eq("camera_id", str(camera_id)).order("display_order").execute()
        camera["images"] = images.data if images.data else []
        
        # Get owner info
        owner = supabase_client.table("users").select("username, avatar_url").eq("id", camera["user_id"]).single().execute()
        if owner.data:
            camera["owner_username"] = owner.data["username"]
            camera["owner_avatar"] = owner.data.get("avatar_url")
        
        # Increment view count
        supabase_client.table("cameras").update({"view_count": camera["view_count"] + 1}).eq("id", str(camera_id)).execute()
        
        return camera
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", response_model=CameraPublic)
async def create_camera(camera_in: CameraCreate, user_id: UUID):
    """Create a new camera."""
    try:
        camera_data = camera_in.model_dump()
        camera_data["user_id"] = str(user_id)
        
        result = supabase_client.table("cameras").insert(camera_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to create camera")
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
