import asyncio
import os
import sys
from pydantic import __version__ as pydantic_version

# Fix pydantic warning for model_ config
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from app.db import get_supabase
from app.config import get_settings

async def setup_auth():
    settings = get_settings()
    client = get_supabase()
    
    print("Checking if user_roles table exists...")
    try:
        res = client.table("user_roles").select("count", count="exact").limit(1).execute()
        print(f"Table user_roles exists. Roles count: {res.count}")
    except Exception as e:
        print(f"Error accessing user_roles. You may need to run 002_auth_schema.sql. Error: {e}")
        return

    email = os.environ.get("DEMO_AUTHORITY_EMAIL")
    password = os.environ.get("DEMO_AUTHORITY_PASSWORD")
    
    if not email or not password:
        print("DEMO_AUTHORITY_EMAIL or DEMO_AUTHORITY_PASSWORD environment variables not set.")
        return

    print(f"Ensuring demo user {email} exists...")
    
    print("Verifying user_roles RLS policies...")
    anon_key = os.environ.get("SUPABASE_ANON_KEY")
    url = os.environ.get("SUPABASE_URL")
    if anon_key and url:
        try:
            from supabase import create_client
            anon_client = create_client(url, anon_key)
            anon_res = anon_client.table("user_roles").select("*").limit(1).execute()
            if len(anon_res.data) > 0:
                print("CRITICAL WARNING: user_roles table returned data to an anonymous request. RLS is not enabled or policies are too permissive! Aborting.")
                return
            else:
                print("RLS verification passed (no rows exposed to anonymous user).")
        except Exception as e:
            print(f"RLS check encountered an error: {e}")
            
    # Try to find existing user first
    try:
        users_res = client.auth.admin.list_users()
        users_list = getattr(users_res, 'users', users_res)
        user = next((u for u in users_list if getattr(u, 'email', '') == email), None)
        
        if not user:
            print("Demo user not found, creating...")
            res = client.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": True
            })
            user = res.user
            print(f"Created demo user: {user.id}")
        else:
            print(f"User {email} already exists with ID: {user.id}")
            
    except Exception as e:
        print(f"Error managing user: {e}")
        return
            
    print(f"Ensuring {email} has AUTHORITY role...")
    try:
        # Update the role instead of insert to avoid trigger collision
        client.table("user_roles").update({
            "role": "AUTHORITY"
        }).eq("user_id", user.id).execute()
        print("Successfully assigned AUTHORITY role.")
    except Exception as e:
        print(f"Error assigning role: {e}")

if __name__ == "__main__":
    asyncio.run(setup_auth())
