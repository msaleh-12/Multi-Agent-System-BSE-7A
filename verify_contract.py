
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
