import sys
import os
import httpx
import asyncio
import json
import re
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

# Add backend directory to path to import settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import get_settings

FRONTEND_URL = "https://landslide-guard-chi.vercel.app"
BACKEND_URL = "https://landslide-guard-api.onrender.com"
settings = get_settings()

async def run_checks():
    results = {}
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        # 1. SPA Routing Check (Frontend)
        try:
            r1 = await client.get(f"{FRONTEND_URL}/dashboard")
            r2 = await client.get(f"{FRONTEND_URL}/login")
            if r1.status_code == 200 and r2.status_code == 200 and "GeoSense" in r1.text:
                results["spa_routing"] = "PASS"
            else:
                results["spa_routing"] = f"FAIL (Dashboard: {r1.status_code}, Login: {r2.status_code})"
        except Exception as e:
            results["spa_routing"] = f"FAIL ({str(e)})"
            
        # 2. Frontend Secrets Leak Check
        try:
            r_js = await client.get(f"{FRONTEND_URL}")
            # Search for JS script src
            js_files = re.findall(r'src="(/assets/index-.*?\.js)"', r_js.text)
            secrets_found = False
            for js in js_files:
                js_content = await client.get(f"{FRONTEND_URL}{js}")
                if settings.supabase_service_role_key in js_content.text or "SUPABASE_SERVICE_ROLE_KEY" in js_content.text:
                    secrets_found = True
                    break
            results["secrets_leak"] = "FAIL" if secrets_found else "PASS"
        except Exception as e:
            results["secrets_leak"] = f"FAIL ({str(e)})"

        # 3. Backend Health Check
        try:
            r = await client.get(f"{BACKEND_URL}/health")
            data = r.json()
            checks = data.get("checks", {})
            if r.status_code == 200 and checks.get("database") == "ONLINE" and checks.get("open_meteo") == "ONLINE":
                results["health"] = f"PASS (DB: {checks.get('database')}, Meteo: {checks.get('open_meteo')})"
            else:
                results["health"] = f"FAIL ({data})"
        except Exception as e:
            results["health"] = f"FAIL ({str(e)})"

        # 4. CORS Check
        try:
            headers = {"Origin": FRONTEND_URL, "Access-Control-Request-Method": "GET"}
            r = await client.options(f"{BACKEND_URL}/health", headers=headers)
            cors_origin = r.headers.get("access-control-allow-origin")
            if cors_origin == FRONTEND_URL or cors_origin == "*":
                results["cors"] = f"PASS ({cors_origin})"
            else:
                results["cors"] = f"FAIL (Got {cors_origin})"
        except Exception as e:
            results["cors"] = f"FAIL ({str(e)})"

        # 5. RBAC 401 Unauthorized Check
        try:
            r = await client.post(f"{BACKEND_URL}/api/v1/alerts", json={
                "type": "EVACUATION",
                "severity": "CRITICAL",
                "message": "Test",
                "location": {"lat": 0, "lng": 0}
            })
            if r.status_code == 401:
                results["rbac_401"] = "PASS"
            else:
                results["rbac_401"] = f"FAIL (Got {r.status_code})"
        except Exception as e:
            results["rbac_401"] = f"FAIL ({str(e)})"
            
        # 6. Supabase Auth & RBAC 403 / Workflow Check
        try:
            email = os.environ.get("DEMO_AUTHORITY_EMAIL", "demo@landslideguard.in")
            password = os.environ.get("DEMO_AUTHORITY_PASSWORD", "demo1234")
            
            # Load frontend env
            frontend_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", ".env")
            anon_key = ""
            if os.path.exists(frontend_env_path):
                with open(frontend_env_path, "r") as f:
                    for line in f:
                        if line.startswith("VITE_SUPABASE_ANON_KEY="):
                            anon_key = line.strip().split("=", 1)[1]
                            break
            
            auth_url = f"{settings.supabase_url}/auth/v1/token?grant_type=password"
            auth_res = await client.post(auth_url, 
                json={"email": email, "password": password},
                headers={"apikey": anon_key}
            )
            
            if auth_res.status_code == 200:
                token = auth_res.json().get("access_token")
                # Try creating an alert as AUTHORITY
                alert_res = await client.post(f"{BACKEND_URL}/api/v1/alerts", json={
                    "type": "WARNING",
                    "severity": "HIGH",
                    "message": "Production Test Alert",
                    "location_name": "Test Location",
                    "latitude": 25.57,
                    "longitude": 91.89,
                    "risk_score": 0.8,
                    "risk_level": "HIGH",
                    "source": "AUTHORITY"
                }, headers={"Authorization": f"Bearer {token}"})
                
                if alert_res.status_code in (200, 201):
                    results["rbac_auth_workflow"] = "PASS"
                    # Try field report verification as AUTHORITY (should work)
                    verify_res = await client.patch(f"{BACKEND_URL}/api/v1/field-reports/1/verify", 
                        headers={"Authorization": f"Bearer {token}"})
                    if verify_res.status_code not in (401, 403):
                        results["field_report_workflow"] = "PASS"
                    else:
                        results["field_report_workflow"] = f"FAIL (Got {verify_res.status_code})"
                else:
                    results["rbac_auth_workflow"] = f"FAIL (Creating alert got {alert_res.status_code}: {alert_res.text})"
            else:
                results["rbac_auth_workflow"] = f"FAIL (Auth failed: {auth_res.status_code} - {auth_res.text})"
                results["field_report_workflow"] = "FAIL (Skipped due to auth failure)"
        except Exception as e:
            results["rbac_auth_workflow"] = f"FAIL ({str(e)})"
            results["field_report_workflow"] = f"FAIL ({str(e)})"
            
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    asyncio.run(run_checks())
