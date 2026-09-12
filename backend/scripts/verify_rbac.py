import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

ENDPOINTS_TO_TEST = [
    ("POST", "/api/v1/alerts"),
    ("POST", "/api/v1/simulation/shillong-storm"),
    ("POST", "/api/v1/field-reports"),
    ("PATCH", "/api/v1/field-reports/123"),
]

def check_endpoint(method, url):
    try:
        if method == "POST":
            res = client.post(url, json={})
        elif method == "PATCH":
            res = client.patch(url, json={})
        elif method == "GET":
            res = client.get(url)
            
        print(f"Testing {method} {url}")
        if res.status_code in [401, 403]:
            print(f"  PASS: Returns {res.status_code}")
        else:
            print(f"  FAIL: Returns {res.status_code} - Expected 401/403")
            print(f"  Response: {res.text}")
    except Exception as e:
        print(f"  Error: {e}")

def main():
    print("Verifying RBAC / Authentication on backend endpoints...")
    for method, url in ENDPOINTS_TO_TEST:
        check_endpoint(method, url)

if __name__ == "__main__":
    main()
