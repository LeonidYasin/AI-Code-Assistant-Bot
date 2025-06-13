"""Test script to directly test the ProjectManager.list_projects method."""
import sys
import io
from pathlib import Path

# Set console output encoding to UTF-8
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from core.project.manager import ProjectManager

def main():
    print("[TEST] Testing ProjectManager.list_projects()")
    print("=" * 50)
    
    # Initialize the project manager
    project_manager = ProjectManager()
    
    # Enable debug logging
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Call list_projects and print the result
    print("\n[TEST] Calling project_manager.list_projects()...")
    success, result = project_manager.list_projects()
    
    print("\n" + "=" * 50)
    print(f"[TEST] Success: {success}")
    
    if success:
        print(f"[TEST] Found {len(result)} projects:")
        for i, project in enumerate(result, 1):
            try:
                print(f"{i}. {project.get('name', 'N/A')} (has_config: {project.get('has_config', False)})")
                print(f"   Path: {project.get('path', 'N/A')}")
                if 'error' in project:
                    print(f"   Error: {project.get('error')}")
            except Exception as e:
                print(f"Error printing project {i}: {e}")
    else:
        print(f"[TEST] Error: {result}")

if __name__ == "__main__":
    main()
