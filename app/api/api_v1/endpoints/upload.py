"""Upload endpoints for images."""

from fastapi import APIRouter, UploadFile, File, HTTPException
from app.db.supabase import supabase_client
import uuid
from typing import Dict

router = APIRouter()


@router.post("/camera-image", response_model=Dict[str, str])
async def upload_camera_image(
    file: UploadFile = File(...),
    user_id: str = None
):
    """Upload a camera image to Supabase storage."""
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Generate unique filename
        file_ext = file.filename.split(".")[-1]
        file_name = f"{user_id}/{uuid.uuid4()}.{file_ext}"
        
        # Read file content
        file_content = await file.read()
        
        # Upload to Supabase storage
        result = supabase_client.storage.from_("camera-images").upload(
            path=file_name,
            file=file_content,
            file_options={"content-type": file.content_type}
        )
        
        # Get public URL
        public_url = supabase_client.storage.from_("camera-images").get_public_url(file_name)
        
        return {
            "url": public_url,
            "path": file_name
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/avatar", response_model=Dict[str, str])
async def upload_avatar(
    file: UploadFile = File(...),
    user_id: str = None
):
    """Upload a user avatar to Supabase storage."""
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Generate filename
        file_ext = file.filename.split(".")[-1]
        file_name = f"{user_id}/avatar.{file_ext}"
        
        # Read file content
        file_content = await file.read()
        
        # Upload to Supabase storage (will overwrite existing)
        result = supabase_client.storage.from_("user-avatars").upload(
            path=file_name,
            file=file_content,
            file_options={"content-type": file.content_type, "upsert": "true"}
        )
        
        # Get public URL
        public_url = supabase_client.storage.from_("user-avatars").get_public_url(file_name)
        
        return {
            "url": public_url,
            "path": file_name
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
