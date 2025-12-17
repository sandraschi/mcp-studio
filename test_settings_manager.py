"""
Test script for Client Settings Manager
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from mcp_studio.app.services.client_settings_manager import ClientSettingsManager
import json
import tempfile
from pathlib import Path

def test_settings_manager():
    """Test the client settings manager functionality."""
    print("Testing Client Settings Manager...")
    print("=" * 50)

    # Create test settings file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        test_settings = {
            'editor.fontSize': 14,
            'workbench.colorTheme': 'Solarized Dark',
            'terminal.integrated.shell.windows': 'C:\\\\Windows\\\\System32\\\\cmd.exe',
            'diffEditor.codeLens': True,
            'explorer.confirmDragAndDrop': False,
            'cline.vsCodeLmModelSelector': {},
            'geminicodeassist.project': 'test-project'
        }
        json.dump(test_settings, f, indent=2)
        config_path = Path(f.name)

    try:
        manager = ClientSettingsManager()

        # Test discovery
        config = manager.discover_client_settings('test-client', config_path)
        print(f"[OK] Discovered {len(config.settings)} settings")

        # Test getting settings
        settings = manager.get_client_settings('test-client')
        print(f"[OK] Organized into {len(settings['categories'])} categories")
        print(f"[OK] Total: {settings['total_settings']}, Editable: {settings['editable_settings']}")

        # Test categories
        categories = manager.get_setting_categories()
        print(f"[OK] Found {len(categories)} setting categories")

        # Test getting a specific setting
        font_setting = manager.get_setting('test-client', 'editor.fontSize')
        print(f"[OK] Font size setting: {font_setting['value']}")

        print("[OK] All settings manager tests passed!")

    finally:
        config_path.unlink()

if __name__ == "__main__":
    test_settings_manager()
