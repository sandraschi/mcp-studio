"""
Test Cline settings discovery with multiple config files
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from mcp_studio.app.services.client_settings_manager import ClientSettingsManager

def test_cline_settings():
    """Test Cline settings discovery with multiple config files."""
    print("Testing Cline settings discovery...")
    print("=" * 50)

    manager = ClientSettingsManager()

    # Test Cline settings discovery
    print("Discovering Cline settings...")
    config = manager.discover_client_settings('cline-vscode')

    if config:
        print(f"[OK] Discovered {len(config.settings)} settings for Cline")

        # Show some setting keys
        setting_keys = list(config.settings.keys())
        print(f"Sample settings: {setting_keys[:5]}...")

        # Check for MCP settings
        mcp_settings = [k for k in setting_keys if k.startswith('mcp.')]
        print(f"[OK] Found {len(mcp_settings)} MCP-related settings")

        if mcp_settings:
            print(f"MCP settings: {mcp_settings[:3]}...")

        # Get categorized settings
        settings_info = manager.get_client_settings('cline-vscode')
        if settings_info:
            categories = list(settings_info["categories"].keys())
            print(f"[OK] Organized into {len(categories)} categories: {categories}")
            print(f"[OK] Total: {settings_info['total_settings']}, Editable: {settings_info['editable_settings']}")

            # Show category breakdown
            for category, settings in settings_info["categories"].items():
                print(f"  {category}: {len(settings)} settings")

    else:
        print("[WARNING] No Cline config found - this is expected if Cline is not configured")

    print("[OK] Cline settings discovery test completed")

if __name__ == "__main__":
    test_cline_settings()
