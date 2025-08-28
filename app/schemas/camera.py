"""Camera schemas for request/response validation."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


class CameraBase(BaseModel):
    """Base camera schema."""
    brand_name: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., min_length=1, max_length=100)
    year: Optional[str] = Field(None, max_length=50)
    camera_type: Optional[str] = Field(None, max_length=50)
    film_format: Optional[str] = Field(None, max_length=50)
    condition: Optional[str] = Field(
        None, 
        pattern="^(mint|excellent|good|fair|poor|for_parts)$"
    )
    acquisition_story: Optional[str] = Field(None, max_length=1000)
    technical_specs: Optional[Dict[str, Any]] = None
    market_value_min: Optional[Decimal] = None
    market_value_max: Optional[Decimal] = None
    is_for_sale: bool = False
    is_for_trade: bool = False
    is_public: bool = True


class CameraCreate(CameraBase):
    """Schema for creating a camera."""
    pass


class CameraUpdate(BaseModel):
    """Schema for updating a camera."""
    brand_name: Optional[str] = Field(None, min_length=1, max_length=100)
    model: Optional[str] = Field(None, min_length=1, max_length=100)
    year: Optional[str] = Field(None, max_length=50)
    camera_type: Optional[str] = Field(None, max_length=50)
    film_format: Optional[str] = Field(None, max_length=50)
    condition: Optional[str] = Field(
        None, 
        pattern="^(mint|excellent|good|fair|poor|for_parts)$"
    )
    acquisition_story: Optional[str] = Field(None, max_length=1000)
    technical_specs: Optional[Dict[str, Any]] = None
    market_value_min: Optional[Decimal] = None
    market_value_max: Optional[Decimal] = None
    is_for_sale: Optional[bool] = None
    is_for_trade: Optional[bool] = None
    is_public: Optional[bool] = None


class CameraImageBase(BaseModel):
    """Base camera image schema."""
    image_url: str
    thumbnail_url: Optional[str] = None
    is_primary: bool = False
    display_order: int = 0


class CameraImageCreate(CameraImageBase):
    """Schema for creating a camera image."""
    camera_id: UUID


class CameraImage(CameraImageBase):
    """Camera image with database fields."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    camera_id: UUID
    created_at: datetime


class CameraInDB(CameraBase):
    """Camera schema with database fields."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    brand_id: Optional[UUID] = None
    view_count: int = 0
    created_at: datetime
    updated_at: datetime


class CameraPublic(BaseModel):
    """Public camera schema for API responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    brand_name: str
    model: str
    year: Optional[str] = None
    camera_type: Optional[str] = None
    film_format: Optional[str] = None
    condition: Optional[str] = None
    acquisition_story: Optional[str] = None
    technical_specs: Optional[Dict[str, Any]] = None
    market_value_min: Optional[Decimal] = None
    market_value_max: Optional[Decimal] = None
    is_for_sale: bool = False
    is_for_trade: bool = False
    is_public: bool = True
    view_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    # Related data (populated separately)
    images: List[CameraImage] = []
    owner_username: Optional[str] = None
    owner_avatar: Optional[str] = None
    like_count: Optional[int] = 0
    comment_count: Optional[int] = 0
    is_liked: Optional[bool] = False
