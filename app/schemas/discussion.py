"""Discussion schemas for request/response validation."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


class DiscussionBase(BaseModel):
    """Base discussion schema."""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)  # Changed from 'body' to 'content' to match frontend
    category_id: Optional[int] = None  # Changed from UUID to int for simplicity
    tags: Optional[List[str]] = []


class DiscussionCreate(DiscussionBase):
    """Schema for creating a discussion."""
    pass


class DiscussionUpdate(BaseModel):
    """Schema for updating a discussion."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)  # Changed from 'body' to 'content'
    tags: Optional[List[str]] = None
    is_pinned: Optional[bool] = None
    is_locked: Optional[bool] = None


class DiscussionInDB(DiscussionBase):
    """Discussion schema with database fields."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str  # Changed from UUID to str to match Supabase
    user_id: str  # Changed from UUID to str for Clerk IDs
    is_pinned: bool = False
    is_locked: bool = False
    view_count: int = 0
    created_at: datetime
    updated_at: datetime


class DiscussionPublic(BaseModel):
    """Public discussion schema for API responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str  # Changed from UUID to str
    user_id: str  # Changed from UUID to str for Clerk IDs
    category_id: Optional[int] = None  # Changed from UUID to int
    title: str
    content: str  # Changed from 'body' to 'content'
    tags: List[str] = []
    is_pinned: bool = False
    is_locked: bool = False
    view_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    # Related data (populated separately)
    author_username: Optional[str] = None
    author_avatar: Optional[str] = None
    category_name: Optional[str] = None
    comment_count: Optional[int] = 0
    like_count: Optional[int] = 0
    is_liked: Optional[bool] = False
    last_comment_at: Optional[datetime] = None


class CategoryBase(BaseModel):
    """Base category schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)
    display_order: int = 0


class CategoryCreate(CategoryBase):
    """Schema for creating a category."""
    pass


class Category(CategoryBase):
    """Category with database fields."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    created_at: datetime


class CommentBase(BaseModel):
    """Base comment schema."""
    body: str = Field(..., min_length=1)
    parent_id: Optional[UUID] = None


class CommentCreate(CommentBase):
    """Schema for creating a comment."""
    discussion_id: Optional[UUID] = None
    camera_id: Optional[UUID] = None


class CommentUpdate(BaseModel):
    """Schema for updating a comment."""
    body: str = Field(..., min_length=1)


class CommentInDB(CommentBase):
    """Comment schema with database fields."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    discussion_id: Optional[UUID] = None
    camera_id: Optional[UUID] = None
    is_edited: bool = False
    created_at: datetime
    updated_at: datetime


class CommentPublic(BaseModel):
    """Public comment schema for API responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    discussion_id: Optional[UUID] = None
    camera_id: Optional[UUID] = None
    parent_id: Optional[UUID] = None
    body: str
    is_edited: bool = False
    created_at: datetime
    updated_at: datetime
    
    # Related data (populated separately)
    author_username: Optional[str] = None
    author_avatar: Optional[str] = None
    like_count: Optional[int] = 0
    is_liked: Optional[bool] = False
    replies: List['CommentPublic'] = []


# Update forward references
CommentPublic.model_rebuild()
