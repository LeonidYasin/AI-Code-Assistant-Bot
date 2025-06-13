import os
import sys
from pathlib import Path
from core.project.manager import ProjectManager

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

def test_direct_commands():
    # Initialize project manager
    test_dir = Path("test_projects")
    test_dir.mkdir(exist_ok=True)
    
    try:
        # Test 1: Create project
        print("\n=== Testing project creation ===")
        pm = ProjectManager(base_path=str(test_dir.absolute()))
        project_name = "test_direct_cmd"
        
        # Create project
        success = pm.create_project(project_name)
        status = "SUCCESS" if success else "FAILED"
        print(f"Create project '{project_name}': {status}")
        
        # Verify project exists
        project_path = test_dir / "projects" / project_name
        exists = project_path.exists()
        print(f"Project path exists: {'YES' if exists else 'NO'}")
        
        # Test 2: Switch project
        print("\n=== Testing project switching ===")
        success = pm.switch_project(project_name)
        status = "SUCCESS" if success else "FAILED"
        print(f"Switch to project '{project_name}': {status}")
        print(f"Current project: {pm.current_project}")
        
        # Test 3: Create file
        print("\n=== Testing file creation ===")
        file_name = "test_file.txt"
        file_content = "Test content"
        
        success, result = pm.create_file(file_name, file_content)
        status = "SUCCESS" if success else f"FAILED: {result}"
        print(f"Create file '{file_name}': {status}")
        
        # Verify file exists and has correct content
        file_path = project_path / file_name
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            matches = content == file_content
            print(f"File content matches: {'YES' if matches else 'NO'}")
            if not matches:
                print(f"Expected: {file_content}")
                print(f"Actual: {content}")
        else:
            print("❌ File was not created")
            
    finally:
        # Cleanup
        import shutil
        if test_dir.exists():
            shutil.rmtree(test_dir)

if __name__ == "__main__":
    test_direct_commands()
