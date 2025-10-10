"""
Test script for Working Set Manager
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from working_sets.manager import WorkingSetManager

def test_working_set_manager():
    """Test the working set manager functionality."""
    
    # Initialize manager
    config_path = "C:/Users/sandr/AppData/Roaming/Claude/claude_desktop_config.json"
    backup_dir = "C:/Users/sandr/AppData/Roaming/Claude/backup"
    templates_dir = "templates"
    
    manager = WorkingSetManager(config_path, backup_dir, templates_dir)
    
    print("🎯 MCP Studio Working Set Manager Test")
    print("=" * 50)
    
    # Test 1: List working sets
    print("\n1. Available Working Sets:")
    working_sets = manager.list_working_sets()
    for ws in working_sets:
        print(f"   {ws['icon']} {ws['name']} ({ws['id']})")
        print(f"      {ws['description']}")
        print(f"      Servers: {len(ws['servers'])}")
    
    # Test 2: Current working set
    print("\n2. Current Working Set:")
    current = manager.get_current_working_set()
    if current:
        current_ws = manager.get_working_set(current)
        print(f"   Current: {current_ws.icon} {current_ws.name}")
        print(f"   Active servers: {len(current_ws.get_server_names())}")
    else:
        print("   No matching working set detected")
    
    # Test 3: Validation
    print("\n3. Working Set Validation:")
    for ws in working_sets:
        validation = manager.validate_working_set(ws['id'])
        status = "✅ Valid" if validation['valid'] else f"❌ Missing: {validation['missing_servers']}"
        print(f"   {ws['icon']} {ws['name']}: {status}")
    
    # Test 4: Preview a working set
    print("\n4. Preview Dev Work Set:")
    try:
        preview = manager.preview_working_set_config("dev_work")
        print(f"   Current servers: {len(preview['current_servers'])}")
        print(f"   New servers: {len(preview['new_servers'])}")
        print(f"   Added: {preview['added_servers']}")
        print(f"   Removed: {preview['removed_servers']}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 5: List backups
    print("\n5. Available Backups:")
    backups = manager.list_backups()
    if backups:
        for backup in backups[:3]:  # Show first 3
            print(f"   📁 {backup['name']} ({backup['created']})")
    else:
        print("   No backups found")
    
    print("\n🎉 Working Set Manager test completed!")

if __name__ == "__main__":
    test_working_set_manager()
