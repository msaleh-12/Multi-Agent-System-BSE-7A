import pytest
import requests
import time
import os

SUPERVISOR_URL = "http://localhost:8000"
GEMINI_WRAPPER_URL = "http://localhost:5010"

# A simple integration test to run after services are up.
# This is not a pytest file, but a script to be run manually.

def wait_for_service(url, service_name):
    retries = 5
    while retries > 0:
        try:
            response = requests.get(f"{url}/health")
            if response.status_code == 200:
                print(f"{service_name} is up!")
                return True
        except requests.ConnectionError:
            print(f"Waiting for {service_name}...")
            time.sleep(2)
            retries -= 1
    print(f"Failed to connect to {service_name}.")
    return False

def run_integration_test():
    if not wait_for_service(SUPERVISOR_URL, "Supervisor"):
        return
    if not wait_for_service(GEMINI_WRAPPER_URL, "Gemini Wrapper"):
        return

    # 1. Login
    login_payload = {"email": "test@example.com", "password": "password"}
    response = requests.post(f"{SUPERVISOR_URL}/api/auth/login", json=login_payload)
    assert response.status_code == 200
    token = response.json()["token"]
    print("Login successful.")

    # 2. Call Supervisor
    headers = {"Authorization": f"Bearer {token}"}
    request_payload = {
        "agentId": "gemini-wrapper",
        "request": "Explain the theory of relativity in simple terms.",
        "priority": 1
    }
    
    print("Sending request to supervisor...")
    response = requests.post(f"{SUPERVISOR_URL}/api/supervisor/request", headers=headers, json=request_payload)
    
    assert response.status_code == 200
    response_data = response.json()
    
    print("Received response:")
    print(response_data)
    
    assert response_data["agentId"] == "gemini-wrapper"
    assert response_data["response"] is not None
    assert "mock response" in response_data["response"] # Assuming mock mode
    
    print("\nIntegration test passed!")

if __name__ == "__main__":
    run_integration_test()
