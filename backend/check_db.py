import asyncio
from app.db import get_supabase

async def check_schema():
    client = get_supabase()
    try:
        res = client.table("user_roles").select("count", count="exact").limit(1).execute()
        print(f"Table user_roles exists. Roles count: {res.count}")
    except Exception as e:
        print(f"Error accessing user_roles: {e}")

asyncio.run(check_schema())
