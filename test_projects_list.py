"""Test script to list all projects in the projects directory."""
import sys
from pathlib import Path

# Set console output encoding to UTF-8
if sys.platform.startswith('win'):
    import io
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def list_projects():
    # Get the projects directory path
    projects_dir = Path("projects")
    
    print(f"\n{'='*50}")
    print(f"Checking projects directory: {projects_dir.absolute()}")
    print(f"Directory exists: {projects_dir.exists()}")
    
    if not projects_dir.exists():
        print("❌ Projects directory does not exist!")
        return []
    
    # List all items in the directory
    print("\nDirectory contents:")
    for i, item in enumerate(projects_dir.iterdir(), 1):
        print(f"{i}. {item.name} (dir: {item.is_dir()}, exists: {item.exists()})")
    
    # List only directories
    projects = [d for d in projects_dir.iterdir() if d.is_dir()]
    
    print(f"\nFound {len(projects)} project directories:")
    for i, project in enumerate(sorted(projects, key=lambda x: x.name.lower()), 1):
        print(f"{i}. {project.name}")
    
    return projects

if __name__ == "__main__":
    print("📂 Testing project directory listing...")
    projects = list_projects()
    
    # Check for the specific project we're looking for
    target_project = "deployed_assistant_20250611_141300"
    print(f"\nLooking for project: {target_project}")
    
    project_path = Path("projects") / target_project
    print(f"Full path: {project_path.absolute()}")
    print(f"Exists: {project_path.exists()}")
    print(f"Is directory: {project_path.is_dir() if project_path.exists() else 'N/A'}")
    
    if project_path.exists() and project_path.is_dir():
        print("✅ Project found in filesystem!")
    else:
        print("❌ Project NOT found or not a directory")
