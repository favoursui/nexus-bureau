from supabase import create_client, Client
from app.config import get_settings
from functools import lru_cache

settings = get_settings()

@lru_cache()
def get_supabase() -> Client:
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_KEY
    )