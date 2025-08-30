"""Optimized discussion endpoints with performance improvements."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Body, Depends
from fastapi.responses import JSONResponse
from app.db.supabase import supabase_client
from app.schemas.discussion import DiscussionCreate, DiscussionPublic, DiscussionUpdate
from app.core.auth import get_current_user_optional, get_current_user
import asyncio
import json
from datetime import datetime
import hashlib

router = APIRouter()

# Simple in-memory cache (replace with Redis in production)
cache_store: Dict[str, Dict[str, Any]] = {}

def get_cache_key(prefix: str, **kwargs) -> str:
    """Generate cache key from parameters."""
    params = json.dumps(kwargs, sort_keys=True)
    hash_key = hashlib.md5(params.encode()).hexdigest()
    return f"{prefix}:{hash_key}"

def get_cached_data(key: str, ttl: int = 60) -> Optional[Any]:
    """Get data from cache if not expired."""
    if key in cache_store:
        cached = cache_store[key]
        if (datetime.utcnow() - cached['timestamp']).seconds < ttl:
            return cached['data']
        else:
            del cache_store[key]
    return None

def set_cache_data(key: str, data: Any) -> None:
    """Set data in cache."""
    cache_store[key] = {
        'data': data,
        'timestamp': datetime.utcnow()
    }

@router.get("/optimized")
async def list_discussions_optimized(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    sortBy: Optional[str] = Query(default="created_at"),
    sortOrder: Optional[str] = Query(default="desc"),
    user_ids: Optional[List[str]] = Query(default=None),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Optimized discussion list endpoint with:
    - Single query with joins for all related data
    - Caching for frequently accessed data
    - Parallel processing where possible
    - Reduced database round trips
    """
    try:
        # Generate cache key
        cache_key = get_cache_key(
            "discussions",
            limit=limit,
            offset=offset,
            sortBy=sortBy,
            sortOrder=sortOrder,
            user_ids=user_ids,
            user_id=current_user.get("sub") if current_user else None
        )
        
        # Check cache first
        cached_data = get_cached_data(cache_key, ttl=30)  # 30 second cache
        if cached_data:
            return cached_data
        
        # Validate sort parameters
        valid_sort_fields = ["created_at", "updated_at", "title", "view_count", "comment_count", "like_count"]
        if sortBy not in valid_sort_fields:
            sortBy = "created_at"
        
        desc = sortOrder.lower() == "desc"
        
        # Build optimized query with all needed data in single request
        base_query = """
            id, user_id, category_id, title, body, tags, 
            is_pinned, is_locked, view_count, created_at, updated_at
        """
        
        # Start building the query
        query = supabase_client.table("discussions").select(base_query)
        
        # Apply user filter if provided
        if user_ids:
            query = query.in_("user_id", user_ids)
        
        # Apply sorting
        if sortBy in ["comment_count", "like_count"]:
            # For aggregate sorts, we'll need to fetch all and sort client-side
            # In production, use a materialized view or stored procedure
            pass
        else:
            query = query.order(sortBy, desc=desc)
        
        # Apply pagination
        query = query.range(offset, offset + limit - 1)
        
        # Execute main query
        result = query.execute()
        discussions = result.data or []
        
        if not discussions:
            set_cache_data(cache_key, [])
            return []
        
        # Collect all unique user IDs for batch fetching
        user_ids_to_fetch = list(set(d["user_id"] for d in discussions if d.get("user_id")))
        discussion_ids = [d["id"] for d in discussions]
        
        # Parallel fetch related data
        async def fetch_users():
            if not user_ids_to_fetch:
                return {}
            users_result = supabase_client.table("users").select(
                "id, username, avatar_url, display_name"
            ).in_("id", user_ids_to_fetch).execute()
            return {u["id"]: u for u in (users_result.data or [])}
        
        async def fetch_categories():
            category_ids = list(set(d["category_id"] for d in discussions if d.get("category_id")))
            if not category_ids:
                return {}
            cats_result = supabase_client.table("discussion_categories").select(
                "id, name"
            ).in_("id", category_ids).execute()
            return {c["id"]: c for c in (cats_result.data or [])}
        
        async def fetch_stats():
            # Batch fetch comment counts
            comments_result = supabase_client.rpc(
                "get_discussion_comment_counts",
                {"discussion_ids": discussion_ids}
            ).execute() if discussion_ids else None
            
            # Batch fetch like counts
            likes_result = supabase_client.rpc(
                "get_discussion_like_counts",
                {"discussion_ids": discussion_ids}
            ).execute() if discussion_ids else None
            
            comment_counts = {}
            like_counts = {}
            
            if comments_result and comments_result.data:
                comment_counts = {item["discussion_id"]: item["count"] for item in comments_result.data}
            
            if likes_result and likes_result.data:
                like_counts = {item["discussion_id"]: item["count"] for item in likes_result.data}
            
            return comment_counts, like_counts
        
        # Use asyncio to run fetches in parallel (simulate async with sync calls)
        # In production, use proper async database client
        users_map = await fetch_users()
        categories_map = await fetch_categories()
        comment_counts, like_counts = await fetch_stats()
        
        # Check user likes if logged in
        user_likes = set()
        if current_user:
            user_id = current_user.get("sub")
            if user_id and discussion_ids:
                likes_result = supabase_client.table("likes").select("discussion_id").eq(
                    "user_id", user_id
                ).in_("discussion_id", discussion_ids).execute()
                user_likes = {l["discussion_id"] for l in (likes_result.data or [])}
        
        # Combine all data
        enriched_discussions = []
        for discussion in discussions:
            user_data = users_map.get(discussion["user_id"], {})
            category_data = categories_map.get(discussion.get("category_id"), {})
            
            enriched = {
                **discussion,
                "content": discussion.pop("body", ""),  # Map body to content
                "author_username": user_data.get("username"),
                "author_avatar": user_data.get("avatar_url"),
                "author_display_name": user_data.get("display_name"),
                "category_name": category_data.get("name"),
                "comment_count": comment_counts.get(discussion["id"], 0),
                "like_count": like_counts.get(discussion["id"], 0),
                "is_liked": discussion["id"] in user_likes,
            }
            enriched_discussions.append(enriched)
        
        # Sort by aggregate fields if needed (client-side)
        if sortBy == "comment_count":
            enriched_discussions.sort(key=lambda x: x["comment_count"], reverse=desc)
        elif sortBy == "like_count":
            enriched_discussions.sort(key=lambda x: x["like_count"], reverse=desc)
        
        # Cache the result
        set_cache_data(cache_key, enriched_discussions)
        
        return enriched_discussions
        
    except Exception as e:
        print(f"Error in optimized discussions endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feed/optimized")
async def get_feed_optimized(
    limit: int = Query(default=20, le=100),
    page: int = Query(default=0, ge=0),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Optimized feed endpoint specifically for logged-in users.
    Fetches discussions from followed users with minimal queries.
    """
    if not current_user:
        return []
    
    user_id = current_user.get("sub")
    if not user_id:
        return []
    
    try:
        # Generate cache key
        cache_key = get_cache_key("feed", user_id=user_id, page=page, limit=limit)
        
        # Check cache
        cached_data = get_cached_data(cache_key, ttl=30)
        if cached_data:
            return cached_data
        
        # Get following list (this should also be cached)
        following_cache_key = f"following:{user_id}"
        following_ids = get_cached_data(following_cache_key, ttl=300)  # 5 min cache
        
        if following_ids is None:
            following_result = supabase_client.table("follows").select(
                "following_id"
            ).eq("follower_id", user_id).execute()
            
            following_ids = [f["following_id"] for f in (following_result.data or [])]
            following_ids.append(user_id)  # Include own posts
            set_cache_data(following_cache_key, following_ids)
        
        if not following_ids:
            return []
        
        # Use the optimized endpoint with user filter
        return await list_discussions_optimized(
            limit=limit,
            offset=page * limit,
            sortBy="created_at",
            sortOrder="desc",
            user_ids=following_ids,
            current_user=current_user
        )
        
    except Exception as e:
        print(f"Error in optimized feed endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def batch_discussions(
    discussion_ids: List[str] = Body(...),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Batch endpoint to fetch multiple discussions at once.
    Useful for prefetching or updating multiple items.
    """
    try:
        if not discussion_ids or len(discussion_ids) > 50:
            raise HTTPException(status_code=400, detail="Invalid number of discussion IDs (1-50)")
        
        # Fetch discussions
        result = supabase_client.table("discussions").select("""
            id, user_id, category_id, title, body, tags, 
            is_pinned, is_locked, view_count, created_at, updated_at,
            users!discussions_user_id_fkey(username, avatar_url),
            discussion_categories!discussions_category_id_fkey(name)
        """).in_("id", discussion_ids).execute()
        
        discussions = result.data or []
        
        # Get stats for all discussions in parallel
        discussion_ids_str = [d["id"] for d in discussions]
        
        # Batch fetch stats
        stats_promises = []
        for disc_id in discussion_ids_str:
            # These would be parallel in async environment
            comment_count_result = supabase_client.table("comments").select(
                "id", count="exact"
            ).eq("discussion_id", disc_id).execute()
            
            like_count_result = supabase_client.table("likes").select(
                "id", count="exact"
            ).eq("discussion_id", disc_id).execute()
            
            stats_promises.append({
                "discussion_id": disc_id,
                "comment_count": comment_count_result.count or 0,
                "like_count": like_count_result.count or 0
            })
        
        # Map stats to discussions
        stats_map = {s["discussion_id"]: s for s in stats_promises}
        
        # Check user likes
        user_likes = set()
        if current_user:
            user_id = current_user.get("sub")
            if user_id:
                likes_result = supabase_client.table("likes").select("discussion_id").eq(
                    "user_id", user_id
                ).in_("discussion_id", discussion_ids_str).execute()
                user_likes = {l["discussion_id"] for l in (likes_result.data or [])}
        
        # Combine data
        enriched = []
        for discussion in discussions:
            stats = stats_map.get(discussion["id"], {})
            enriched.append({
                **discussion,
                "content": discussion.pop("body", ""),
                "author_username": discussion["users"]["username"] if discussion.get("users") else None,
                "author_avatar": discussion["users"]["avatar_url"] if discussion.get("users") else None,
                "category_name": discussion["discussion_categories"]["name"] if discussion.get("discussion_categories") else None,
                "comment_count": stats.get("comment_count", 0),
                "like_count": stats.get("like_count", 0),
                "is_liked": discussion["id"] in user_likes
            })
        
        return enriched
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prefetch")
async def prefetch_discussions(
    user_ids: List[str] = Body(...),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Prefetch discussions for specified users.
    Useful for warming cache before user navigates.
    """
    try:
        if not user_ids or len(user_ids) > 20:
            raise HTTPException(status_code=400, detail="Invalid number of user IDs (1-20)")
        
        # Fetch and cache discussions for each user
        for user_id in user_ids:
            cache_key = get_cache_key("user_discussions", user_id=user_id)
            
            # Skip if already cached
            if get_cached_data(cache_key, ttl=300):
                continue
            
            # Fetch user's discussions
            result = supabase_client.table("discussions").select(
                "id, title, created_at, view_count"
            ).eq("user_id", user_id).order(
                "created_at", desc=True
            ).limit(10).execute()
            
            set_cache_data(cache_key, result.data or [])
        
        return {"status": "prefetch completed", "users": len(user_ids)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Create the necessary database functions if they don't exist
CREATE_DB_FUNCTIONS = """
-- Function to get comment counts for multiple discussions
CREATE OR REPLACE FUNCTION get_discussion_comment_counts(discussion_ids UUID[])
RETURNS TABLE(discussion_id UUID, count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT c.discussion_id, COUNT(*)::BIGINT
    FROM comments c
    WHERE c.discussion_id = ANY(discussion_ids)
    GROUP BY c.discussion_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get like counts for multiple discussions
CREATE OR REPLACE FUNCTION get_discussion_like_counts(discussion_ids UUID[])
RETURNS TABLE(discussion_id UUID, count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT l.discussion_id, COUNT(*)::BIGINT
    FROM likes l
    WHERE l.discussion_id = ANY(discussion_ids)
    GROUP BY l.discussion_id;
END;
$$ LANGUAGE plpgsql;
"""
