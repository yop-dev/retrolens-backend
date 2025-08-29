"""Camera endpoints - simplified for initial testing."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, Depends
from app.db.supabase import supabase_client
from app.schemas.camera import CameraCreate, CameraUpdate, CameraPublic
from app.core.auth import get_current_user_optional

router = APIRouter()


@router.get("/", response_model=List[CameraPublic])
async def list_cameras(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    sortBy: Optional[str] = Query(default="created_at"),
    sortOrder: Optional[str] = Query(default="desc"),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """List all public cameras."""
    try:
        # Validate sort parameters
        valid_sort_fields = ["created_at", "updated_at", "brand_name", "model", "view_count"]
        if sortBy not in valid_sort_fields:
            sortBy = "created_at"
        
        desc = sortOrder.lower() == "desc"
        
        # Get cameras with owner info
        result = supabase_client.table("cameras").select("""
            id, user_id, brand_id, brand_name, model, year, camera_type, film_format, condition,
            acquisition_story, technical_specs, market_value_min, market_value_max, is_for_sale,
            is_for_trade, is_public, view_count, created_at, updated_at,
            users!cameras_user_id_fkey(username, avatar_url)
        """).eq("is_public", True).order(sortBy, desc=desc).range(offset, offset + limit - 1).execute()
        
        cameras = []
        user_id = current_user.get("sub") if current_user else None
        
        for camera in result.data or []:
            # Get like count
            like_count_result = supabase_client.table("likes").select("id", count="exact").eq("camera_id", camera["id"]).execute()
            like_count = like_count_result.count or 0
            
            # Check if current user liked this camera
            is_liked = False
            if user_id:
                user_like = supabase_client.table("likes").select("id").eq("user_id", user_id).eq("camera_id", camera["id"]).execute()
                is_liked = bool(user_like.data)
            
            # Get comment count
            comment_count_result = supabase_client.table("comments").select("id", count="exact").eq("camera_id", camera["id"]).execute()
            comment_count = comment_count_result.count or 0
            
            # Get camera images
            images = supabase_client.table("camera_images").select("*").eq("camera_id", camera["id"]).order("display_order").execute()
            
            camera_data = {
                **camera,
                "owner_username": camera["users"]["username"] if camera.get("users") else None,
                "owner_avatar": camera["users"]["avatar_url"] if camera.get("users") else None,
                "like_count": like_count,
                "is_liked": is_liked,
                "comment_count": comment_count,
                "images": images.data if images.data else []
            }
            camera_data.pop("users", None)
            cameras.append(camera_data)
        
        return cameras
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{camera_id}", response_model=CameraPublic)
async def get_camera(
    camera_id: UUID,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get a camera by ID."""
    try:
        # Get camera with owner info
        result = supabase_client.table("cameras").select("""
            id, user_id, brand_id, brand_name, model, year, camera_type, film_format, condition,
            acquisition_story, technical_specs, market_value_min, market_value_max, is_for_sale,
            is_for_trade, is_public, view_count, created_at, updated_at,
            users!cameras_user_id_fkey(username, avatar_url)
        """).eq("id", str(camera_id)).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        camera = result.data
        user_id = current_user.get("sub") if current_user else None
        
        # Get camera images
        images = supabase_client.table("camera_images").select("*").eq("camera_id", str(camera_id)).order("display_order").execute()
        
        # Get like count
        like_count_result = supabase_client.table("likes").select("id", count="exact").eq("camera_id", str(camera_id)).execute()
        like_count = like_count_result.count or 0
        
        # Check if current user liked this camera
        is_liked = False
        if user_id:
            user_like = supabase_client.table("likes").select("id").eq("user_id", user_id).eq("camera_id", str(camera_id)).execute()
            is_liked = bool(user_like.data)
        
        # Get comment count
        comment_count_result = supabase_client.table("comments").select("id", count="exact").eq("camera_id", str(camera_id)).execute()
        comment_count = comment_count_result.count or 0
        
        # Increment view count
        supabase_client.table("cameras").update({"view_count": camera["view_count"] + 1}).eq("id", str(camera_id)).execute()
        
        camera_data = {
            **camera,
            "owner_username": camera["users"]["username"] if camera.get("users") else None,
            "owner_avatar": camera["users"]["avatar_url"] if camera.get("users") else None,
            "like_count": like_count,
            "is_liked": is_liked,
            "comment_count": comment_count,
            "images": images.data if images.data else []
        }
        camera_data.pop("users", None)
        
        return camera_data
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
