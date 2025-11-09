
# Frontend Integration Specification

This document provides the technical specification for integrating the frontend application with the Multi-Agent System backend. It includes API endpoint definitions, data contracts, sample requests/responses, and verification artifacts.

## 1. Overview

### 1.1. Summary

The backend is a multi-agent system managed by a Supervisor. The frontend's primary role is to authenticate users, discover available agents, and submit tasks (requests) to them through the Supervisor. All communication is JSON over HTTP.

### 1.2. Assumptions

- The backend is running and accessible at the base URL.
- The frontend is responsible for managing JWT tokens (storing on login, sending in headers, clearing on logout).
- The `gemini-wrapper` agent is expected to be available for processing requests.

### 1.3. Base URL

All API endpoints are relative to the following base URL:

```
http://127.0.0.1:8000
```

### 1.4. Authentication

Authentication is handled via JSON Web Tokens (JWT).

1.  The frontend sends user credentials (`email`, `password`) to `POST /api/auth/login`.
2.  The backend validates the credentials and returns a JWT (`access_token`).
3.  For all subsequent requests to protected endpoints, the frontend must include the token in the `Authorization` header.

**Header Format:**

```
Authorization: Bearer <your_jwt_token>
```

---

## 2. Data Contracts (TypeScript Interfaces)

The frontend must adhere to the following TypeScript interfaces for all communication. This file (`interfaces.ts`) should be used to define the shapes of the data exchanged with the backend.

```typescript
// interfaces.ts

export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
}

export interface Agent {
  id: string;
  name: string;
  description?: string;
  capabilities: string[];
}

export type MessageType = 'user' | 'agent' | 'error';

export interface Message {
  type: MessageType;
  content: string;
  timestamp: string; // ISO
}

export interface RequestPayload {
  agentId: string;
  request: string;
  priority: number;
  modelOverride?: string | null;
  autoRoute: boolean;
}

export interface RequestResponseMetadata {
  executionTime: number; // milliseconds
  agentTrace: string[];
  participatingAgents: string[];
}

export interface ErrorInfo {
  code?: string;
  message?: string;
  details?: string;
}

export interface RequestResponse {
  response?: string;
  agentId?: string;
  timestamp: string; // ISO
  metadata?: RequestResponseMetadata;
  error?: ErrorInfo;
}
```

---

## 3. API Endpoints

### 3.1. Authentication

#### `POST /api/auth/login`

Authenticates a user and returns a JWT.

-   **Method:** `POST`
-   **Path:** `/api/auth/login`
-   **Headers:**
    -   `Content-Type: application/json`
-   **Request Body (Example):**

    ```json
    {
      "email": "test@example.com",
      "password": "password123"
    }
    ```

-   **Success Response (200 OK):**

    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer",
      "user": {
        "id": "1",
        "name": "Test User",
        "email": "test@example.com",
        "avatar": "https://example.com/avatar.png"
      }
    }
    ```

-   **Error Response (400 Bad Request):**

    ```json
    {
      "detail": "Email and password required"
    }
    ```

#### `GET /api/auth/me`

Retrieves the profile of the currently authenticated user.

-   **Method:** `GET`
-   **Path:** `/api/auth/me`
-   **Headers:**
    -   `Authorization: Bearer <token>`
-   **Success Response (200 OK):**

    ```json
    {
      "id": "1",
      "name": "Test User",
      "email": "test@example.com",
      "avatar": "https://example.com/avatar.png"
    }
    ```

### 3.2. Supervisor

#### `GET /api/supervisor/registry`

Fetches the list of all available agents registered with the Supervisor.

-   **Method:** `GET`
-   **Path:** `/api/supervisor/registry`
-   **Headers:**
    -   `Authorization: Bearer <token>`
-   **Success Response (200 OK):**

    ```json
    {
      "agents": [
        {
          "id": "gemini-wrapper",
          "name": "Gemini Wrapper",
          "description": "A worker that interacts with Google's Gemini model.",
          "capabilities": ["summarization", "translation", "text-generation"]
        }
      ]
    }
    ```

#### `POST /api/supervisor/request`

Submits a new task/request to a specific agent or for auto-routing.

-   **Method:** `POST`
-   **Path:** `/api/supervisor/request`
-   **Headers:**
    -   `Authorization: Bearer <token>`
    -   `Content-Type: application/json`
-   **Request Body (`RequestPayload`):**

    ```json
    {
      "agentId": "gemini-wrapper",
      "request": "Summarize the following text: ...",
      "priority": 1,
      "modelOverride": null,
      "autoRoute": false
    }
    ```

-   **Success Response (200 OK - `RequestResponse`):**

    ```json
    {
      "response": "This is the summary of the text.",
      "agentId": "gemini-wrapper",
      "timestamp": "2025-11-01T10:00:00Z",
      "metadata": {
        "executionTime": 1234,
        "agentTrace": ["supervisor", "gemini-wrapper"],
        "participatingAgents": ["gemini-wrapper"]
      },
      "error": null
    }
    ```

-   **Slow Response (Still 200 OK):**
    The structure is the same, but `metadata.executionTime` will be higher. The frontend should show a progress indicator after 2 seconds and have a timeout of at least 10 seconds.

-   **Error Response (Handled by Supervisor):**

    ```json
    {
      "response": null,
      "agentId": "gemini-wrapper",
      "timestamp": "2025-11-01T10:05:00Z",
      "metadata": null,
      "error": {
        "code": "AGENT_EXECUTION_ERROR",
        "message": "The agent failed to process the request.",
        "details": "Underlying error from the worker."
      }
    }
    ```

### 3.3. Agent

#### `GET /api/agent/{agentId}/health`

Checks the health status of a specific agent.

-   **Method:** `GET`
-   **Path:** `/api/agent/gemini-wrapper/health`
-   **Headers:**
    -   `Authorization: Bearer <token>`
-   **Success Response (200 OK):**

    ```json
    {
      "status": "healthy"
    }
    ```
    *Possible values for `status`: `healthy`, `degraded`, `offline`.*

---

## 4. Verification Artifacts

### 4.1. Curl Commands for Manual Verification

Run these commands in your terminal to manually verify backend connectivity and data contracts.

**Step 1: Login and Export Token**

```bash
# Use a valid email/password for the backend
# The default user is test@example.com / password123
export TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}' | jq -r .access_token)

echo "Token: $TOKEN"
```

**Step 2: Test Authenticated Endpoints**

```bash
# Get current user
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/api/auth/me

# Get agent registry
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/api/supervisor/registry

# Check gemini-wrapper health
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/api/agent/gemini-wrapper/health

# Submit a request
curl -X POST http://127.0.0.1:8000/api/supervisor/request \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agentId": "gemini-wrapper",
    "request": "Hello, world!",
    "priority": 1,
    "autoRoute": false
  }'
```

### 4.2. Contract Test Script (Python)

This script automates the verification of the API contracts.

**Setup:**

```bash
pip install requests jsonschema
```

**Script (`verify_contract.py`):**

```python
# verify_contract.py
import os
import sys
import requests
from jsonschema import validate

BASE_URL = "http://127.0.0.1:8000"
EMAIL = os.getenv("API_USER_EMAIL", "test@example.com")
PASSWORD = os.getenv("API_USER_PASSWORD", "password123")

# JSON Schemas based on TypeScript interfaces
AGENT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "capabilities": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["id", "name", "capabilities"],
}

REQUEST_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "response": {"type": ["string", "null"]},
        "agentId": {"type": ["string", "null"]},
        "timestamp": {"type": "string", "format": "date-time"},
        "metadata": {
            "type": ["object", "null"],
            "properties": {
                "executionTime": {"type": "number"},
                "agentTrace": {"type": "array", "items": {"type": "string"}},
                "participatingAgents": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["executionTime", "agentTrace", "participatingAgents"],
        },
        "error": {
            "type": ["object", "null"],
            "properties": {
                "code": {"type": "string"},
                "message": {"type": "string"},
                "details": {"type": "string"},
            },
        },
    },
    "required": ["timestamp"],
}

def main():
    print("--- Starting Backend Contract Verification ---")
    failures = []

    # 1. Login and get token
    try:
        print("\n[1/4] Testing: POST /api/auth/login")
        res = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": EMAIL, "password": PASSWORD},
            timeout=5
        )
        res.raise_for_status()
        token = res.json().get("access_token")
        if not token:
            failures.append("Login failed: access_token not found in response.")
        else:
            print("  - PASSED: Login successful, token received.")
            headers = {"Authorization": f"Bearer {token}"}
    except requests.RequestException as e:
        failures.append(f"Login request failed: {e}")
        sys.exit(1) # Cannot continue without a token

    # 2. Get registry and validate schema
    try:
        print("\n[2/4] Testing: GET /api/supervisor/registry")
        res = requests.get(f"{BASE_URL}/api/supervisor/registry", headers=headers, timeout=5)
        res.raise_for_status()
        agents = res.json().get("agents", [])
        gemini_agent = next((a for a in agents if a["id"] == "gemini-wrapper"), None)

        if not gemini_agent:
            failures.append("Registry check failed: 'gemini-wrapper' agent not found.")
        else:
            validate(instance=gemini_agent, schema=AGENT_SCHEMA)
            print("  - PASSED: 'gemini-wrapper' found and matches Agent schema.")
    except Exception as e:
        failures.append(f"Registry check failed: {e}")

    # 3. Get agent health
    try:
        print("\n[3/4] Testing: GET /api/agent/gemini-wrapper/health")
        res = requests.get(f"{BASE_URL}/api/agent/gemini-wrapper/health", headers=headers, timeout=5)
        res.raise_for_status()
        status = res.json().get("status")
        if status not in ["healthy", "degraded", "offline"]:
            failures.append(f"Health check failed: Invalid status '{status}'.")
        else:
            print(f"  - PASSED: Health status is '{status}'.")
    except Exception as e:
        failures.append(f"Health check failed: {e}")

    # 4. Submit request and validate response
    try:
        print("\n[4/4] Testing: POST /api/supervisor/request")
        payload = {
            "agentId": "gemini-wrapper",
            "request": "Test request: Hello!",
            "priority": 1,
            "modelOverride": None,
            "autoRoute": False,
        }
        res = requests.post(f"{BASE_URL}/api/supervisor/request", headers=headers, json=payload, timeout=15)
        res.raise_for_status()
        response_data = res.json()
        validate(instance=response_data, schema=REQUEST_RESPONSE_SCHEMA)
        print("  - PASSED: RequestResponse schema is valid.")

        if response_data.get("metadata") and "executionTime" in response_data["metadata"]:
             print("  - PASSED: metadata.executionTime is present.")
        else:
            failures.append("Request test failed: metadata.executionTime is missing.")

    except Exception as e:
        failures.append(f"Request test failed: {e}")


    # Final Summary
    print("\n--- Verification Summary ---")
    if failures:
        print(f"Result: FAILED ({len(failures)} checks failed)\n")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("Result: PASSED. All contract checks were successful.")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

**How to Run:**

```bash
python verify_contract.py
```

The script will exit with code `0` on success and `1` on failure, printing a summary of what went wrong.

### 4.3. Mock Service Worker (MSW) Handlers

For frontend development when the backend is unavailable, use these MSW handlers.

```javascript
// mocks/handlers.js
import { http, HttpResponse } from 'msw';

const BASE_URL = 'http://127.0.0.1:8000';

export const handlers = [
  // Login
  http.post(`${BASE_URL}/api/auth/login`, () => {
    return HttpResponse.json({
      access_token: 'mock-jwt-token',
      token_type: 'bearer',
      user: {
        id: '1',
        name: 'Mock User',
        email: 'mock@example.com',
      },
    });
  }),

  // Get User
  http.get(`${BASE_URL}/api/auth/me`, () => {
    return HttpResponse.json({
      id: '1',
      name: 'Mock User',
      email: 'mock@example.com',
    });
  }),

  // Get Registry
  http.get(`${BASE_URL}/api/supervisor/registry`, () => {
    return HttpResponse.json({
      agents: [
        {
          id: 'gemini-wrapper',
          name: 'Gemini Wrapper (Mock)',
          description: 'A mocked worker.',
          capabilities: ['summarization'],
        },
      ],
    });
  }),

  // Agent Health
  http.get(`${BASE_URL}/api/agent/gemini-wrapper/health`, () => {
    return HttpResponse.json({ status: 'healthy' });
  }),

  // Supervisor Request
  http.post(`${BASE_URL}/api/supervisor/request`, async ({ request }) => {
    const payload = await request.json();
    
    // Simulate a delay
    await new Promise(res => setTimeout(res, 800));

    // Simulate an error
    if (payload.request.includes('error')) {
        return HttpResponse.json({
            response: null,
            agentId: payload.agentId,
            timestamp: new Date().toISOString(),
            metadata: null,
            error: {
                code: 'MOCK_ERROR',
                message: 'This is a mocked error response.',
            },
        }, { status: 500 });
    }

    return HttpResponse.json({
      response: `Mock response to: "${payload.request}"`,
      agentId: payload.agentId,
      timestamp: new Date().toISOString(),
      metadata: {
        executionTime: 800,
        agentTrace: ['supervisor', 'gemini-wrapper'],
        participatingAgents: ['gemini-wrapper'],
      },
      error: null,
    });
  }),
];
```

---

## 5. Verification and Acceptance

### 5.1. Verification Checklist

The frontend team must complete these steps to verify successful integration.

-   [ ] **Manual Curl Tests:** Run all commands in section 4.1 and confirm they execute without errors and return the expected JSON structures.
-   [ ] **Automated Contract Test:** Run the `verify_contract.py` script and ensure it exits with code 0.
-   [ ] **UI Login:** The user can log in via the UI, and the JWT is stored correctly.
-   [ ] **UI Registry Display:** After login, the UI calls `/api/supervisor/registry` and correctly displays the "Gemini Wrapper" agent.
-   [ ] **UI Health Status:** The UI can fetch and display the health status of the `gemini-wrapper` agent.
-   [ ] **UI Request/Response:** The user can submit a request to the `gemini-wrapper` agent via the UI, and the response is displayed correctly.

### 5.2. Acceptance Criteria

-   **Login:** A user can log in, and the frontend can use the returned token to successfully call `GET /api/auth/me`.
-   **Registry:** `GET /api/supervisor/registry` returns a list containing at least one agent with `id: "gemini-wrapper"`.
-   **Health:** `GET /api/agent/gemini-wrapper/health` returns a JSON object `{ "status": "healthy" }` (or `degraded`/`offline`).
-   **Request:** `POST /api/supervisor/request` with a valid payload returns a `RequestResponse` object where `metadata.executionTime` is a number.
-   **Contract Test:** The `verify_contract.py` script passes with exit code 0.

---

## 6. Error Handling & Edge Cases

The frontend should be prepared to handle the following HTTP status codes.

#### `401 Unauthorized`

-   **Cause:** The `Authorization` header is missing, or the JWT is invalid/expired.
-   **Sample Response:**
    ```json
    {
      "detail": "Not authenticated"
    }
    ```
-   **Frontend Action:** Invalidate any stored token and redirect the user to the login page.

#### `400 Bad Request`

-   **Cause:** The request payload is malformed or missing required fields (e.g., invalid JSON in a `POST` request).
-   **Sample Response (from FastAPI):**
    ```json
    {
      "detail": [
        {
          "loc": ["body", "request"],
          "msg": "field required",
          "type": "value_error.missing"
        }
      ]
    }
    ```
-   **Frontend Action:** Log the error for debugging. Display a generic "Bad Request" message to the user. This typically indicates a bug in the frontend code that constructs the request.

#### `504 Gateway Timeout`

-   **Cause:** The Supervisor timed out waiting for a response from the worker agent.
-   **Sample Response (from a gateway, if configured):** This may be HTML or a simple text response depending on the infrastructure.
-   **Frontend Action:** Inform the user that the request timed out and they can try again later. Implement a client-side timeout (e.g., 10-15 seconds) to avoid waiting indefinitely.

#### `500 Internal Server Error`

-   **Cause:** An unexpected error occurred on the backend.
-   **Sample Response:**
    ```json
    {
      "detail": "Internal Server Error"
    }
    ```
-   **Frontend Action:** Display a generic error message (e.g., "An unexpected error occurred. Please try again later."). Log the full error details for debugging.

---

## 7. Troubleshooting Guide

-   **Problem: `401 Unauthorized` or `Not authenticated`**
    -   **Check:** Is the `Authorization: Bearer <token>` header included in your request?
    -   **Check:** Did you copy the token correctly after logging in?
    -   **Check:** Has the token expired? Try logging in again to get a fresh one.

-   **Problem: Schema validation fails in `verify_contract.py`**
    -   **Check:** Compare the JSON response from the failing endpoint (e.g., using `curl`) with the schema defined in the script.
    -   **Look for:** Missing required fields, fields with wrong data types (e.g., `executionTime` is a string instead of a number), or `null` values where an object is expected.

-   **Problem: Connection Refused**
    -   **Check:** Is the backend server running? You should see logs from FastAPI/Uvicorn in the terminal.
    -   **Check:** Is the backend running on `http://127.0.0.1:8000`? Verify the host and port.

-   **Problem: `504 Gateway Timeout`**
    -   **Check:** Is the `gemini-wrapper` agent running and healthy? The Supervisor may not be able to reach it.
    -   **Check:** The agent might be taking too long to process. This could be normal for complex tasks. Consider increasing the frontend's request timeout. **Recommended default: 10 seconds.**

---

## 8. (Optional) Diagnostic Script

This shell script runs the basic `curl` checks and provides a simple pass/fail summary.

**`diagnose.sh`**
```bash
#!/bin/bash

BASE_URL="http://127.0.0.1:8000"
EMAIL="test@example.com"
PASSWORD="password123"
AGENT_ID="gemini-wrapper"

echo "--- Running Backend Diagnostics ---"

# 1. Check if server is running
if ! curl -s -o /dev/null "$BASE_URL/docs"; then
    echo "❌ FAIL: Backend server is not reachable at $BASE_URL"
    exit 1
fi
echo "✅ PASS: Backend server is reachable."

# 2. Login
TOKEN=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}" | jq -r .access_token)

if [ -z "$TOKEN" ] || [ "$TOKEN" == "null" ]; then
    echo "❌ FAIL: Could not log in to get a token."
    exit 1
fi
echo "✅ PASS: Login successful."

# 3. Check registry
AGENT_IN_REGISTRY=$(curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/supervisor/registry" | jq ".agents[] | select(.id==\"$AGENT_ID\")")
if [ -z "$AGENT_IN_REGISTRY" ]; then
    echo "❌ FAIL: Agent '$AGENT_ID' not found in registry."
    exit 1
fi
echo "✅ PASS: Agent '$AGENT_ID' found in registry."

# 4. Check health
HEALTH_STATUS=$(curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/agent/$AGENT_ID/health" | jq -r .status)
if [ "$HEALTH_STATUS" != "healthy" ]; then
    echo "⚠️ WARN: Agent '$AGENT_ID' health is '$HEALTH_STATUS' (expected 'healthy')."
else
    echo "✅ PASS: Agent '$AGENT_ID' is healthy."
fi

echo "--- Diagnostics Complete ---"
```
**How to Run:**
```bash
chmod +x diagnose.sh
./diagnose.sh
```
