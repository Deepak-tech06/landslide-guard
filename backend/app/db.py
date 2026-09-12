"""Supabase client initialization for LandslideGuard."""

from supabase import create_client, Client
from app.config import get_settings

_client: Client | None = None


def get_supabase() -> Client:
    """Get or create the Supabase client singleton."""
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set. "
                "See .env.example for required environment variables."
            )
        _client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    return _client


async def check_supabase_health() -> dict:
    """Check if Supabase is reachable and responsive."""
    try:
        client = get_supabase()
        # Simple query to verify connectivity
        result = client.table("data_source_status").select("id").limit(1).execute()
        return {"status": "ONLINE", "latency_ms": None}
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}
