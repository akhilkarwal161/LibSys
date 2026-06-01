import requests
import os
import sys

def run_integration_tests():
    token = os.environ.get("GCP_TEST_TOKEN")
    if not token:
        print("Error: GCP_TEST_TOKEN environment variable not set.")
        sys.exit(1)

    base_url = "https://libsys-932534087542.asia-southeast1.run.app"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    print(f"--- Starting Functional Verification against {base_url} ---")

    # 1. Assert GET /dashboard/ returns HTTP 200 or 302 (redirect to login)
    print("\n[Test 1] GET /dashboard/")
    try:
        response = requests.get(f"{base_url}/dashboard/", headers=headers, allow_redirects=False, timeout=5)
        print(f"Status Code: {response.status_code}")
        assert response.status_code in [200, 302], f"Unexpected status: {response.status_code}"
        print("Success: GET /dashboard/ verified.")
    except Exception as e:
        print(f"Fail: {e}")

    # 2. Assert REST API endpoint rejects invalid payload with HTTP 400
    print("\n[Test 2] POST /api/issue/create/ with invalid payload")
    invalid_payload = {
        "user": "",
        "book": "",
        "days": -5
    }
    try:
        response = requests.post(f"{base_url}/api/issue/create/", headers=headers, json=invalid_payload, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        assert response.status_code == 400, f"Expected HTTP 400, got: {response.status_code}"
        print("Success: Schema validation rejected invalid payload correctly.")
    except Exception as e:
        print(f"Fail: {e}")

    # 3. Assert REST API GET /api/books/ returns HTTP 200 list
    print("\n[Test 3] GET /api/books/")
    try:
        response = requests.get(f"{base_url}/api/books/", headers=headers, timeout=5)
        print(f"Status Code: {response.status_code}")
        assert response.status_code == 200, f"Expected HTTP 200, got: {response.status_code}"
        print(f"Found {len(response.json())} books in database.")
        print("Success: GET /api/books/ list fetched.")
    except Exception as e:
        print(f"Fail: {e}")


if __name__ == "__main__":
    run_integration_tests()
