#!/usr/bin/env python3
"""Quick script to check if both services are running."""
import requests
import sys

def check_service(url, name):
    try:
        response = requests.get(f"{url}/health", timeout=2)
        if response.status_code == 200:
            print(f"✅ {name} is running at {url}")
            return True
        else:
            print(f"❌ {name} responded with status {response.status_code}")
            return False
    except requests.ConnectionError:
        print(f"❌ {name} is NOT running at {url}")
        return False
    except requests.Timeout:
        print(f"⏳ {name} is slow to respond at {url}")
        return False
    except Exception as e:
        print(f"❌ Error checking {name}: {e}")
        return False

if __name__ == "__main__":
    print("Checking services...\n")
    
    supervisor_ok = check_service("http://127.0.0.1:8000", "Supervisor")
    gemini_ok = check_service("http://127.0.0.1:5010", "Gemini Wrapper")
    
    print()
    if supervisor_ok and gemini_ok:
        print("✅ Both services are running! You can run the integration test now.")
        sys.exit(0)
    else:
        print("❌ One or more services are not running.")
        print("\nTo start the services:")
        print("  Terminal 1: venv\\Scripts\\activate && run_supervisor.bat")
        print("  Terminal 2: venv\\Scripts\\activate && run_gemini.bat")
        sys.exit(1)

