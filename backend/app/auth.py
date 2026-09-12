"""Authentication and RBAC dependencies for FastAPI."""

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from typing import Optional

from app.db import get_supabase

logger = logging.getLogger("landslide_guard.auth")
security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)):
    """Extract and verify Supabase JWT."""
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    token = credentials.credentials
    supabase = get_supabase()
    
    try:
        # Verify token with Supabase server
        user_resp = supabase.auth.get_user(token)
        user = user_resp.user
        if not user:
            raise ValueError("Invalid token")
            
        # Fetch user role from user_roles table
        role_resp = supabase.table("user_roles").select("role").eq("user_id", user.id).execute()
        role = "CITIZEN" # Default
        if role_resp.data and len(role_resp.data) > 0:
            role = role_resp.data[0]["role"]
            
        return {
            "id": user.id,
            "email": user.email,
            "role": role
        }
    except Exception as e:
        logger.warning(f"Auth failed: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_role(allowed_roles: list[str]):
    """Dependency factory for RBAC."""
    async def role_checker(user: dict = Depends(get_current_user)):
        if user["role"] not in allowed_roles and user["role"] != "ADMIN":
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker

# Pre-configured dependencies
require_authority = require_role(["AUTHORITY"])
require_field_team = require_role(["AUTHORITY", "FIELD_TEAM"])
require_citizen = require_role(["AUTHORITY", "FIELD_TEAM", "CITIZEN"])
