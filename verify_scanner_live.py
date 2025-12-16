import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Import logic
try:
    import studio_dashboard
    from studio_dashboard import scan_repos, state
except ImportError as e:
    print(f"Error importing studio_dashboard: {e}")
    sys.exit(1)


def verify_live():
    print("🚀 Starting Live Repo Scanner Verification...")
    print(f"📂 Repos Directory: {studio_dashboard.REPOS_DIR}")

    # Run scan
    results = scan_repos()

    print(f"\n✅ Scan Complete. Found {len(results)} MCP repos.")
    print("-" * 50)

    for r in results:
        print(f"{r['zoo_emoji']} {r['name']} (v{r['fastmcp_version'] or '?'})")
        if r.get("is_fullstack"):
            stack = []
            if r["frontend"]:
                stack.append(f"Frontend: {', '.join(r['frontend'])}")
            if r["backend"]:
                stack.append(f"Backend: {', '.join(r['backend'])}")
            if r["infrastructure"]:
                stack.append(f"Infra: {', '.join(r['infrastructure'])}")
            print(f"   🏗️ Fullstack: {' | '.join(stack)}")

    print("-" * 50)
    print("\n📋 Activity Log (Last 5):")
    for log in state["scan_progress"]["activity_log"][-5:]:
        print(f"   {log}")


if __name__ == "__main__":
    verify_live()
