#!/usr/bin/env python3
import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from mcp_studio.app.services.mcp_client_metadata import get_all_clients

def test_clients():
    try:
        clients = get_all_clients()
        print(f"Found {len(clients)} clients:")
        for i, client in enumerate(clients[:5]):  # Show first 5
            client_id = getattr(client, 'id', 'unknown')
            name = getattr(client, 'name', 'unknown')
            platform = getattr(client, 'platform', 'unknown')
            client_type = getattr(client, 'client_type', 'unknown')
            print(f"  {i+1}. {client_id}: {name} ({platform}, {client_type})")
        return len(clients)
    except Exception as e:
        print(f"Error getting clients: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    test_clients()
