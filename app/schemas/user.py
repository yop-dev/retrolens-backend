from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: EmailStr
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    expertise_level: Optional[str] = "beginner"  # beginner, intermediate, expert
    website_url: Optional[str] = None
    instagram_url: Optional[str] = None

class UserCreate(UserBase):
    pass  # No additional fields needed, id will be handled separately

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    expertise_level: Optional[str] = None
    website_url: Optional[str] = None
    instagram_url: Optional[str] = None

class UserPublic(UserBase):
    id: str
    created_at: datetime
    
    # Computed fields for counts
    camera_count: int = 0
    discussion_count: int = 0
    follower_count: int = 0
    following_count: int = 0