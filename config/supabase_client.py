from supabase import create_client, Client
from config.settings import settings
from typing import Optional

# Lazy-load Supabase client
_supabase_client: Optional[Client] = None


def get_supabase() -> Client:
    """Get Supabase client instance (lazy-loaded)"""
    global _supabase_client

    if _supabase_client is None:
        _supabase_client = create_client(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_SERVICE_KEY
        )

    return _supabase_client
