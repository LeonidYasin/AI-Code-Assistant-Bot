"""Test script for code execution with natural language commands."""
import asyncio
import logging
import sys
import json
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

async def main():
    """Main function to test code execution."""
    from core.nlp import default_processor
    from core.project.manager import ProjectManager
    
    try:
        # Initialize project manager
        project_manager = ProjectManager()
        
        # Create a unique test project name with timestamp
        import time
        timestamp = int(time.time())
        test_project_name = f"test_project_{timestamp}"
        
        # Create the test project in the projects directory
        try:
            # Create the project
            project_path = project_manager.create_project(test_project_name)
            print(f"Created test project at: {project_path}")
            
            # Verify the project was created
            if not project_path or not Path(project_path).exists():
                print("Failed to create test project directory")
                return
                
            # Ensure the project directory exists and has a config file
            project_config = Path(project_path) / ".project.json"
            if not project_config.exists():
                print(f"Project config file not found at: {project_config}")
                return
                
            # Debug: List all projects before switching
            print("\n=== Debug: Listing all projects ===")
            success, projects = project_manager.list_projects()
            if success:
                print(f"Found {len(projects)} projects:")
                for i, p in enumerate(projects, 1):
                    print(f"  {i}. {p.get('name')} (path: {p.get('path')})")
            else:
                print(f"Failed to list projects: {projects}")
            
            # Switch to the created project using the project name
            print(f"\n=== Debug: Switching to project '{test_project_name}' ===")
            if not project_manager.switch_project(test_project_name):
                print("Failed to switch to test project")
                return
                
            print(f"Current project after switch: {project_manager.current_project}")
            
            # Verify the project path is set correctly
            project_path = project_manager.get_project_path()
            print(f"Project path from get_project_path(): {project_path}")
            if not project_path:
                print("get_project_path() returned None")
                return
                
            if not project_path.exists():
                print(f"Project path does not exist: {project_path}")
                # Try to find the project in the projects directory
                projects_dir = project_manager.projects_dir
                print(f"Checking projects directory: {projects_dir}")
                if projects_dir.exists():
                    print(f"Projects in directory:")
                    for p in projects_dir.iterdir():
                        print(f"  - {p.name} (dir: {p.is_dir()})")
                return
                
            # Verify the project is active
            if not project_manager.current_project:
                print("No active project after switch")
                # Check project state file
                state_file = project_manager._get_state_file_path()
                print(f"Checking state file: {state_file}")
                if state_file.exists():
                    try:
                        with open(state_file, 'r') as f:
                            state = json.load(f)
                            print(f"State file content: {json.dumps(state, indent=2)}")
                    except Exception as e:
                        print(f"Error reading state file: {e}")
                else:
                    print("State file does not exist")
                return
                
            # Print project info for debugging
            project_info = project_manager.get_project_info()
            print(f"Project info: {project_info}")
            
        except Exception as e:
            print(f"Failed to setup project: {str(e)}")
            import traceback
            traceback.print_exc()
            return
        
        # Test natural language command with explicit project
        command = f"Run a Python script that prints 'Hello, World!'"
        
        print(f"\n=== Executing command ===\n{command}")
        print(f"Project: {test_project_name}")
        print(f"Project path: {project_path}")
        
        # Create a context dictionary with required fields
        context = {
            'bot_data': {
                'current_project': test_project_name  # Explicitly set current project
            },
            'project_manager': project_manager,
            'project_name': test_project_name  # Also set project_name in context
        }
        
        # Debug: Print current project state
        print("\n=== Current Project State ===")
        print(f"project_manager.current_project: {project_manager.current_project}")
        print(f"project_manager.get_project_path(): {project_manager.get_project_path()}")
        
        # List all projects for debugging
        success, projects = project_manager.list_projects()
        if success:
            print("\nAvailable projects:")
            for p in projects:
                print(f"- {p.get('name')} (current: {p.get('is_current', False)}): {p.get('path')}")
        else:
            print(f"Failed to list projects: {projects}")
        
        # Patch the LLM client to ensure it returns the project in the response
        from unittest.mock import patch
        from core.llm.client import LLMClient
        
        # Create a patched version of the LLM client
        original_call = LLMClient.call
        
        def patched_call(self, *args, **kwargs):
            # Call the original method
            response = original_call(self, *args, **kwargs)
            
            # Parse the response as JSON
            import json
            try:
                response_data = json.loads(response)
                # Ensure the project is set in the response
                if 'params' in response_data and 'project' in response_data['params']:
                    response_data['params']['project'] = test_project_name
                # Convert back to string
                response = json.dumps(response_data)
            except (json.JSONDecodeError, TypeError):
                # If response is not JSON, try to inject the project
                if '"project": null' in response:
                    response = response.replace('"project": null', f'"project": "{test_project_name}"')
                elif '"project":null' in response:
                    response = response.replace('"project":null', f'"project":"{test_project_name}"')
            return response
        
        # Apply the patch
        with patch.object(LLMClient, 'call', patched_call):
            # Process the command with the patched LLM client
            success, response = await default_processor.process_command(
                text=command,
                context=context,
                chat_id="test_chat",
                user_id="test_user"
            )
        
        # Format the result
        result = {
            'success': success,
            'response': response
        }
        
        print("\n=== Result ===")
        try:
            # Try to print the result as JSON for better formatting
            print(json.dumps(result, indent=2, ensure_ascii=False))
        except Exception as e:
            # Fall back to regular printing if JSON serialization fails
            print(f"Success: {result.get('success', False)}")
            response = result.get('response', 'No response')
            if isinstance(response, (dict, list)):
                try:
                    print("Response:", json.dumps(response, indent=2, ensure_ascii=False))
                except:
                    print("Response:", str(response)[:500])  # Truncate long responses
            else:
                print("Response:", str(response)[:500])  # Truncate long responses
            
            if 'error' in result:
                print("Error:", str(result['error'])[:500])  # Truncate long errors
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
