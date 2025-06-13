"""Test script for executing natural language commands."""
import asyncio
import sys
import os
import logging
from pathlib import Path

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

try:
    from core.llm.client import LLMClient
    from core.project.manager import ProjectManager
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure you're running this script from the project root directory.")
    sys.exit(1)

# Set console encoding to UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def main():
    print("Initializing LLM client...")
    try:
        # Initialize LLM client
        llm_client = LLMClient()
        
        # Initialize project manager with LLM
        project_manager = ProjectManager()
        project_manager.llm = llm_client  # Set the LLM client
        
        # Get the command from command line arguments or use a default test command
        if len(sys.argv) > 1:
            command = " ".join(sys.argv[1:])
        else:
            command = "list all projects"  # Default test command
        
        print(f"\nExecuting command: {command}")
        
        # Process the natural language command
        print("\nProcessing command...")
        result = project_manager.process_natural_language(command)
        
        print("\n=== Command Result ===")
        if result.get('success'):
            print("✅ Success!")
            print(f"Command type: {result.get('type', 'unknown')}")
            if 'params' in result and result['params']:
                print("\nParameters:")
                for key, value in result['params'].items():
                    print(f"  {key}: {value}")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
        print("====================")
            
    except Exception as e:
        print(f"\n❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nTest completed.")

if __name__ == "__main__":
    asyncio.run(main())
