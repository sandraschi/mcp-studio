#!/usr/bin/env python3
"""
Simple test of the Working Set Manager
"""

import json
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_json_templates():
    """Test that all JSON templates are valid."""
    templates_dir = Path("templates")
    print("🧪 Testing JSON Templates")
    print("=" * 30)
    
    if not templates_dir.exists():
        print("❌ Templates directory not found")
        return False
    
    template_files = list(templates_dir.glob("*.json"))
    print(f"Found {len(template_files)} template files")
    
    for template_file in template_files:
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ {template_file.name}: {data.get('name', 'Unnamed')}")
        except Exception as e:
            print(f"❌ {template_file.name}: {e}")
            return False
    
    return True

def test_working_set_manager():
    """Test the WorkingSetManager class."""
    print("\n🔧 Testing WorkingSetManager")
    print("=" * 30)
    
    try:
        from working_sets.manager import WorkingSetManager
        
        # Initialize with test paths
        config_path = r"C:\Users\sandr\AppData\Roaming\Claude\claude_desktop_config.json"
        manager = WorkingSetManager(
            config_path=config_path,
            backup_dir="test_backup",
            templates_dir="templates"
        )
        
        # Test loading working sets
        working_sets = manager.list_working_sets()
        print(f"✅ Loaded {len(working_sets)} working sets")
        
        for ws in working_sets:
            print(f"   {ws.get('icon', '🔧')} {ws.get('name', 'Unnamed')} ({len(ws.get('servers', []))} servers)")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests."""
    print("🎯 MCP Studio Working Sets - Simple Test")
    print("=" * 50)
    
    # Test 1: JSON templates
    json_ok = test_json_templates()
    
    # Test 2: Working Set Manager
    manager_ok = test_working_set_manager()
    
    # Results
    print("\n📊 Test Results")
    print("=" * 20)
    print(f"JSON Templates: {'✅ PASS' if json_ok else '❌ FAIL'}")
    print(f"WorkingSetManager: {'✅ PASS' if manager_ok else '❌ FAIL'}")
    
    if json_ok and manager_ok:
        print("\n🎉 All tests passed! Working sets system is ready.")
        return 0
    else:
        print("\n💥 Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
