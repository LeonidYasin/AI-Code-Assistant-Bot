"""Simple script to list projects using the ProjectManager directly."""
import sys
import os
import logging
from pathlib import Path

# Set up console encoding
if sys.platform.startswith('win'):
    import io
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Add the project root to the Python path
project_root = str(Path(__file__).parent.absolute())
sys.path.insert(0, project_root)

def main():
    """List all projects using the ProjectManager."""
    try:
        from core.project.manager import ProjectManager
        
        print("[INIT] Initializing ProjectManager...")
        project_manager = ProjectManager()
        
        print("[INFO] Fetching project list...")
        success, result = project_manager.list_projects()
        
        if success:
            if not result:
                print("[INFO] No projects found.")
                return
                
            print("\n=== List of projects ===")
            print("-" * 50)
            for i, project in enumerate(result, 1):
                status = "[OK] " if project.get('has_config', False) else "[!] "
                config_status = "" if project.get('has_config', False) else " (no config)"
                print(f"{i}. {status}{project.get('name', 'Unnamed')}{config_status}")
                print(f"   Path: {project.get('path', 'N/A')}")
                print("-" * 50)
        else:
            print(f"[ERROR] {result}")
            
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
