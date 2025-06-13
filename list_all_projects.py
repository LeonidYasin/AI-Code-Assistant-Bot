"""Simple script to list all projects directly from the projects directory."""
import sys
from pathlib import Path

# Set console output encoding to UTF-8
if sys.platform.startswith('win'):
    import io
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def list_all_projects():
    projects_dir = Path("projects")
    if not projects_dir.exists():
        print("❌ Projects directory not found!")
        return []
    
    # List all directories in the projects folder
    projects = [d for d in projects_dir.iterdir() if d.is_dir()]
    return sorted(projects, key=lambda x: x.name.lower())

if __name__ == "__main__":
    print("📂 All projects in the projects directory:")
    projects = list_all_projects()
    
    # Prepare project info
    project_info = []
    for i, project in enumerate(projects, 1):
        # Count files
        file_count = sum(1 for f in project.rglob('*') if f.is_file())
        size_bytes = sum(f.stat().st_size for f in project.rglob('*') if f.is_file())
        
        # Format size
        size_str = "0 B"
        if size_bytes > 0:
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024.0 or unit == 'GB':
                    size_str = f"{size_bytes:.1f} {unit}"
                    break
                size_bytes /= 1024.0
        
        project_info.append({
            'name': project.name,
            'path': str(project.absolute()),
            'file_count': file_count,
            'size': size_str
        })
    
    # Print results
    if not project_info:
        print("No projects found in the projects directory.")
    else:
        for i, proj in enumerate(project_info, 1):
            print(f"{i}. {proj['name']}")
            print(f"   📁 Path: {proj['path']}")
            print(f"   📄 Files: {proj['file_count']}")
            print(f"   📊 Size: {proj['size']}")
            print()
