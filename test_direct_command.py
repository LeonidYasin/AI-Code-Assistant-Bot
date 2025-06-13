"""Direct command test script for project management."""
import sys
import os
from pathlib import Path

# Configure console encoding for Windows
if sys.platform == 'win32':
    import io
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

try:
    from core.project.manager import ProjectManager
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure you're running this script from the project root directory.")
    sys.exit(1)

def main():
    """Main function to test direct project commands."""
    # Get the command from command line arguments or use a default test command
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
    else:
        command = "list"  # Default command
    
    try:
        # Initialize project manager
        project_manager = ProjectManager()
        
        # Process the command
        if command == "list":
            print("Listing all projects...")
            success, result = project_manager.list_projects()
            if success:
                print("\nProjects:")
                for i, project in enumerate(result, 1):
                    print(f"{i}. {project['name']} - {project['path']}")
            else:
                print(f"Error: {result}")
                
        elif command == "create" and len(sys.argv) > 2:
            project_name = sys.argv[2]
            print(f"Creating project: {project_name}")
            success, result = project_manager.create_project(project_name)
            if success:
                print(f"Successfully created project: {result}")
            else:
                print(f"Error: {result}")
                
        elif command == "info" and len(sys.argv) > 2:
            project_name = sys.argv[2]
            print(f"Getting info for project: {project_name}")
            
            # First switch to the project
            if not project_manager.switch_project(project_name):
                print("Error: Failed to switch to project")
                return
                
            # Now get the project info
            info = project_manager.get_project_info()
            if 'error' in info:
                print(f"Error: {info['error']}")
            else:
                print("\nProject Info:")
                for key, value in info.items():
                    print(f"{key}: {value}")
                    
        else:
            print("\nAvailable commands:")
            print("  list                     - List all projects")
            print("  create <project_name>    - Create a new project")
            print("  info <project_name>      - Get project information")
            
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\nTest completed.")

if __name__ == "__main__":
    main()
