#!/usr/bin/env python3
"""Test script for Assignment Coach Agent."""
import requests
import json
import time

SUPERVISOR_URL = "http://127.0.0.1:8000"
ASSIGNMENT_COACH_URL = "http://127.0.0.1:5020"

def test_assignment_coach_direct():
    """Test the assignment coach agent directly."""
    print("Testing Assignment Coach Agent directly...\n")
    
    # Test health endpoint
    try:
        response = requests.get(f"{ASSIGNMENT_COACH_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✅ Assignment Coach Agent is running")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return
    except requests.ConnectionError:
        print("❌ Assignment Coach Agent is not running!")
        print("   Start it with: venv\\Scripts\\activate && run_assignment_coach.bat")
        return
    
    # Test assignment guidance request
    test_payload = {
        "message_id": "test-001",
        "sender": "SupervisorAgent_Main",
        "recipient": "assignment-coach",
        "type": "task_assignment",
        "task": {
            "name": "process_request",
            "parameters": {
                "intent": "generate_assignment_guidance",
                "payload": {
                    "student_id": "stu_001",
                    "assignment_title": "AI Chatbot Design Report",
                    "assignment_description": "Prepare a detailed report explaining the architecture and training process of a conversational AI chatbot.",
                    "subject": "Artificial Intelligence",
                    "deadline": "2025-10-20",
                    "difficulty": "Intermediate",
                    "student_profile": {
                        "learning_style": "visual",
                        "progress": 0.25,
                        "skills": ["writing", "communication"],
                        "weaknesses": ["time management"]
                    }
                }
            }
        }
    }
    
    print("\nSending test request...")
    response = requests.post(
        f"{ASSIGNMENT_COACH_URL}/process",
        json=test_payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Request successful!")
        print("\nResponse:")
        print(json.dumps(result, indent=2))
        
        # Try to parse the output
        if "results" in result and "output" in result["results"]:
            try:
                output_json = json.loads(result["results"]["output"])
                print("\n✅ Parsed JSON output:")
                print(json.dumps(output_json, indent=2))
            except json.JSONDecodeError:
                print("\n⚠️  Output is not valid JSON")
    else:
        print(f"❌ Request failed: {response.status_code}")
        print(response.text)

def test_via_supervisor():
    """Test assignment coach via supervisor."""
    print("\n\nTesting Assignment Coach via Supervisor...\n")
    
    # Check supervisor
    try:
        response = requests.get(f"{SUPERVISOR_URL}/health", timeout=2)
        if response.status_code != 200:
            print("❌ Supervisor is not running!")
            return
    except requests.ConnectionError:
        print("❌ Supervisor is not running!")
        return
    
    # Login
    print("Logging in...")
    login_response = requests.post(
        f"{SUPERVISOR_URL}/api/auth/login",
        json={"email": "test@example.com", "password": "password"}
    )
    
    if login_response.status_code != 200:
        print("❌ Login failed!")
        return
    
    token = login_response.json()["token"]
    print("✅ Login successful")
    
    # Send assignment request
    print("\nSending assignment request via supervisor...")
    assignment_request = {
        "agentId": "assignment-coach",
        "request": json.dumps({
            "intent": "generate_assignment_guidance",
            "payload": {
                "student_id": "stu_001",
                "assignment_title": "AI Chatbot Design Report",
                "assignment_description": "Prepare a detailed report explaining the architecture and training process of a conversational AI chatbot.",
                "subject": "Artificial Intelligence",
                "deadline": "2025-10-20",
                "difficulty": "Intermediate",
                "student_profile": {
                    "learning_style": "visual",
                    "progress": 0.25,
                    "skills": ["writing", "communication"],
                    "weaknesses": ["time management"]
                }
            }
        }),
        "priority": 1
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{SUPERVISOR_URL}/api/supervisor/request",
        json=assignment_request,
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Request successful!")
        print("\nResponse:")
        print(json.dumps(result, indent=2))
        
        # Try to parse the response
        if "response" in result and result["response"]:
            try:
                response_json = json.loads(result["response"])
                print("\n✅ Parsed JSON response:")
                print(json.dumps(response_json, indent=2))
            except (json.JSONDecodeError, TypeError):
                print(f"\n⚠️  Response is not JSON: {result['response']}")
    else:
        print(f"❌ Request failed: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    print("=" * 60)
    print("Assignment Coach Agent Test")
    print("=" * 60)
    
    test_assignment_coach_direct()
    test_via_supervisor()
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)

