import threading
import time

import requests

BASE_URL = "http://localhost:8330"


def poll_progress():
    print("⏳ Starting progress polling...")
    for _ in range(20):
        try:
            resp = requests.get(f"{BASE_URL}/api/progress")
            if resp.status_code == 200:
                data = resp.json()
                print(
                    f"📊 Progress: {data.get('status')} | {data.get('done', 0)}/{data.get('total', 0)} | Found: {data.get('mcp_repos_found')} | Log: {len(data.get('activity_log', []))}"
                )
                if data.get("status") == "complete":
                    print("✅ Scan reported complete!")
                    break
            else:
                print(f"❌ Polling failed: {resp.status_code}")
        except Exception as e:
            print(f"❌ Polling error: {e}")
        time.sleep(0.5)


def trigger_scan():
    print("🚀 Triggering scan via /api/repos...")
    try:
        resp = requests.get(f"{BASE_URL}/api/repos")
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Scan API returned {len(data)} repos")
        else:
            print(f"❌ Scan API failed: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"❌ Scan API error: {e}")


if __name__ == "__main__":
    # Start polling in background (like frontend)
    t = threading.Thread(target=poll_progress)
    t.start()

    # Trigger scan
    trigger_scan()

    t.join()
