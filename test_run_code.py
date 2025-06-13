"""
Test script for the run_code command.
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.absolute())
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

from core.project.manager import ProjectManager
from core.llm.client import LLMClient
from core.commands.run_code import CodeRunner

async def main():
    """Test the code runner."""
    # Initialize components
    project_manager = ProjectManager()
    llm_client = LLMClient()
    
    # Create a test project if it doesn't exist
    test_project = "test_project"
    try:
        project_path = project_manager.create_project(test_project)
        print(f"Created test project at: {project_path}")
    except Exception as e:
        print(f"Using existing test project: {e}")
    
    # Test code with proper indentation
    test_code = """
def greet(name):
    return f"Hello, {name}!"

print(greet("World"))
print("2 + 2 =", 2 + 2)
"""
    
    # Run the code
    runner = CodeRunner(project_manager, llm_client)
    success, result = await runner.run_code(
        code=test_code,
        project_name=test_project,
        analyze=True
    )
    
    # Print results with proper encoding
    import sys
    import io
    
    # Set stdout to handle Unicode
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    print("\n=== Test Results ===")
    print(f"Success: {success}")
    try:
        print(f"Result:\n{result}")
    except UnicodeEncodeError:
        # Fallback for terminals that can't handle certain Unicode
        print("Result (with Unicode replaced):")
        print(result.encode('ascii', 'replace').decode('ascii'))

if __name__ == "__main__":
    asyncio.run(main())
