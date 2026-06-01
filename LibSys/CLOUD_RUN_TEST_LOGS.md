# CLOUD_RUN_TEST_LOGS.md

## Test Run Environment
*   **Target Cloud Run URL:** `https://libsys-932534087542.asia-southeast1.run.app`
*   **Region:** `asia-southeast1`
*   **GCP Authentication Account:** `website@civic-source-463118-a0.iam.gserviceaccount.com`

---

## Live Integration Execution Outcomes

### 🔴 Test 1: `GET /dashboard/`
*   **Status:** `FAILED`
*   **Response / Error Details:** `HTTPSConnectionPool(host='libsys-932534087542.asia-southeast1.run.app', port=443): Read timed out. (read timeout=5)`
*   **Root Cause:** Cloud Run instance cold-start latency exceeded the standard 5-second test timeout.

### 🔴 Test 2: `POST /api/issue/create/` (Schema Rejection validation)
*   **Status:** `FAILED`
*   **Response / Error Details:** `HTTP 404 Not Found`
*   **Root Cause:** The active live container is running an outdated codebase deployment (last deployed 2025-10-03). The old router maps this API route differently (e.g. without trailing slashes, or using legacy URL mappings).

### 🔴 Test 3: `GET /api/books/` (Retrieve Books Inventory)
*   **Status:** `FAILED`
*   **Response / Error Details:** `HTTPSConnectionPool(host='libsys-932534087542.asia-southeast1.run.app', port=443): Read timed out. (read timeout=5)`
*   **Root Cause:** Cold start scaling lag or live DB connectivity timeout in active container.
