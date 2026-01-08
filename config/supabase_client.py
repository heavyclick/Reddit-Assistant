from supabase import create_client, Client
from config.settings import settings

# Initialize Supabase client
supabase: Client = create_client(
    supabase_url=settings.SUPABASE_URL,
    supabase_key=settings.SUPABASE_SERVICE_KEY
)


def get_supabase() -> Client:
    """Get Supabase client instance"""
    return supabase
