"""Supabase client configuration and database connection."""

import sys
from typing import Optional
from supabase import create_client, Client
from app.core.config import settings


# Singleton instance
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Get Supabase client instance (lazy initialization)."""
    global _supabase_client
    
    if _supabase_client is None:
        try:
            _supabase_client = create_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_SERVICE_KEY
            )
            print(f"✅ Supabase client initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Supabase client: {e}")
            print(f"   URL: {settings.SUPABASE_URL}")
            print(f"   Check your SUPABASE_URL and SUPABASE_SERVICE_KEY in Railway")
            raise
    
    return _supabase_client


# For backward compatibility - will initialize on first use
class LazySupabaseClient:
    """Lazy wrapper for Supabase client."""
    
    def __getattr__(self, name):
        return getattr(get_supabase_client(), name)


supabase_client = LazySupabaseClient()
