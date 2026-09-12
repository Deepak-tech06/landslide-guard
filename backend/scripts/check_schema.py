import os
import sys
import httpx
from dotenv import load_dotenv

# Load env vars
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

def main():
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("Missing Supabase credentials")
        sys.exit(1)
        
    print("Fetching OpenAPI schema from PostgREST...")
    url = f"{SUPABASE_URL}/rest/v1/?apikey={SUPABASE_SERVICE_ROLE_KEY}"
    res = httpx.get(url)
    
    if res.status_code != 200:
        print(f"Failed to fetch schema: {res.status_code}")
        sys.exit(1)
        
    data = res.json()
    defs = data.get("definitions", {})
    
    if "user_roles" in defs:
        print("SUCCESS: public.user_roles exists in the remote schema.")
        print("Columns:")
        for col, props in defs["user_roles"].get("properties", {}).items():
            print(f"  - {col}: {props.get('type')} {props.get('description', '')}")
            
    else:
        print("ERROR: public.user_roles does not exist!")
        sys.exit(1)

if __name__ == "__main__":
    main()
