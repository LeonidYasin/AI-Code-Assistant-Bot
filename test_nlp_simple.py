"""Simple test script for executing natural language commands."""
import asyncio
import sys
import os
import json
from pathlib import Path

# Configure console encoding for Windows
if sys.platform == 'win32':
    import io
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

try:
    from core.nlp.command_processor import NLPCommandProcessor
    from core.nlp.prompt_builder import PromptBuilder
    from core.nlp.response_parser import ResponseParser
    from core.project.manager import ProjectManager
    from core.nlp.handlers import (
        ProjectCommandHandler,
        FileCommandHandler,
        CodeCommandHandler
    )
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure you're running this script from the project root directory.")
    sys.exit(1)

class MockLLMClient:
    """Mock LLM client for testing."""
    
    def __init__(self):
        self.responses = {
            "list all projects": {
                "type": "list_projects",
                "params": {},
                "confidence": 0.95,
                "explanation": "User wants to see all available projects"
            },
            "create a new project called test": {
                "type": "create_project",
                "params": {"name": "test"},
                "confidence": 0.9,
                "explanation": "User wants to create a new project named 'test'"
            },
            "run python code print('hello')": {
                "type": "run_code",
                "params": {
                    "code": "print('hello')",
                    "language": "python"
                },
                "confidence": 0.85,
                "explanation": "User wants to run Python code that prints 'hello'"
            }
        }
    
    async def generate(self, prompt, **kwargs):
        """Mock generate method that returns predefined responses."""
        # Extract the user message from the prompt
        user_message = None
        for msg in reversed(prompt):
            if msg.get('role') == 'user':
                user_message = msg.get('content', '').lower()
                break
        
        # Find a matching response
        for query, response in self.responses.items():
            if query.lower() in user_message:
                return json.dumps(response)
        
        # Default response if no match found
        return json.dumps({
            "type": "unknown",
            "params": {},
            "confidence": 0.0,
            "explanation": "Could not understand the command"
        })

async def process_command(processor, command):
    """Process a single command with the given processor."""
    print("\nProcessing command...")
    
    # Create a mock context
    class MockContext:
        def __init__(self):
            self.chat_id = "test_chat"
            self.user_id = "test_user"
            self.bot_data = {}
            self.current_project = None
    
    context = MockContext()
    
    # Process the command
    success, result = await processor.process_command(
        text=command,
        context={"bot_data": {}},
        chat_id="test_chat",
        user_id="test_user"
    )
    
    # Print results
    print("\n=== Command Result ===")
    print(f"Success: {success}")
    print(f"Response: {result}")
    
    # If we have a command to execute, try to handle it
    if success and isinstance(result, dict):
        print("\n=== Command Details ===")
        print(f"Type: {result.get('type')}")
        print(f"Params: {json.dumps(result.get('params', {}), indent=2)}")
    
    return success, result

async def main():
    """Main async function to test natural language processing."""
    # Get the command from command line arguments or use a default test command
    if len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])
    else:
        command = "list all projects"  # Default test command
    
    print(f"Testing natural language command: {command}")
    
    try:
        # Initialize components
        llm_client = MockLLMClient()
        prompt_builder = PromptBuilder()
        response_parser = ResponseParser()
        
        # Initialize command processor with mock LLM
        processor = NLPCommandProcessor()
        processor.prompt_builder = prompt_builder
        processor.response_parser = response_parser
        processor.llm = llm_client
        
        # Process the command
        await process_command(processor, command)
            
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\nTest completed.")

if __name__ == "__main__":
    asyncio.run(main())
