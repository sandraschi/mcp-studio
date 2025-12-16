import threading
import time

import requests

BASE_URL = "http://localhost:8330/api"


def check_endpoint(url):
    print(f"Checking {url}...")
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        try:
            data = response.json()
            print(f"Response: {str(data)[:200]}...")  # Truncate
            return data
        except Exception:
            print(f"Response (text): {response.text[:200]}...")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None


print("=== Verifying MCP Studio API Migration ===")

# 1. Check Progress (should be 'idle' or similar initially)
data = check_endpoint(f"{BASE_URL}/repos/progress")

# 2. Trigger Scan (might block)
print("\nTriggering Scan...")


def trigger_scan():
    print("  [Thread] Triggering blocking scan...")
    try:
        r = requests.get(f"{BASE_URL}/repos", timeout=60)
        print(f"  [Thread] Scan finished. Status: {r.status_code}")
    except Exception as e:
        print(f"  [Thread] Scan trigger failed/timed out: {e}")


# 2. Trigger Scan in background thread (since it blocks)
scan_thread = threading.Thread(target=trigger_scan)
scan_thread.start()
time.sleep(2)  # Give it a moment to start

# 3. Poll Progress
print("Polling progress...")
for i in range(5):
    data = check_endpoint(f"{BASE_URL}/repos/progress")
    if data:
        status = data.get("status")
        total = data.get("total")
        done = data.get("done")
        print(f"  Poll {i + 1}: Status={status}, Progress={done}/{total}")
        if status == "complete":
            break
    time.sleep(1)


print("\n--- HTML Route Verification ---")
html_base = "http://localhost:8330"
for route in ["/", "/dashboard", "/repos"]:
    print(f"Checking HTML {route}...")
    try:
        r = requests.get(f"{html_base}{route}", timeout=5)
        print(f"Status: {r.status_code}")
        if r.status_code == 200 and "<html" in r.text.lower():
            print("✅ Valid HTML response")
        else:
            print(f"❌ Invalid response: {r.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

print("\nVerification Complete.")
