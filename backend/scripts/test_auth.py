import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.auth import get_current_user
from fastapi import HTTPException

client = TestClient(app)

ENDPOINTS = [
    ("POST", "/api/v1/alerts"),
    ("POST", "/api/v1/simulation/shillong-storm"),
    ("POST", "/api/v1/field-reports"),
    ("PATCH", "/api/v1/field-reports/123"),
]

def check_401():
    print("--- Checking 401 Unauthorized (No Token) ---")
    app.dependency_overrides = {} # ensure no overrides
    for method, url in ENDPOINTS:
        if method == "POST":
            res = client.post(url, json={})
        else:
            res = client.patch(url, json={})
        
        if res.status_code == 403: # Wait, FastAPI HTTPBearer returns 403 if no header is present, per spec?
            print(f"{method} {url} -> {res.status_code} {res.json()}")
        else:
            print(f"{method} {url} -> {res.status_code} (Expected 403 or 401) {res.json()}")

def mock_citizen_user():
    return {"id": "citizen-123", "email": "cit@example.com", "role": "CITIZEN"}

def check_403():
    print("\n--- Checking 403 Forbidden (Insufficient Role: CITIZEN) ---")
    app.dependency_overrides[get_current_user] = mock_citizen_user
    
    # We test AUTHORITY-only endpoints
    authority_endpoints = [
        ("POST", "/api/v1/alerts"),
        ("POST", "/api/v1/simulation/shillong-storm"),
        ("PATCH", "/api/v1/field-reports/123"),
    ]
    for method, url in authority_endpoints:
        if method == "POST":
            res = client.post(url, json={})
        else:
            res = client.patch(url, json={})
            
        print(f"{method} {url} -> {res.status_code}")

if __name__ == "__main__":
    check_401()
    check_403()
