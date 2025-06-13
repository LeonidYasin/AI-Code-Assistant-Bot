"""
Integration test for the NLP processor.
"""
import asyncio
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import importlib

# Set UTF-8 encoding for stdout
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import the mock LLM client first
try:
    from tests.mocks.mock_llm_client import MockLLMClient, LazyLLMClient

    # Create the mock LLM client instance
    mock_llm = LazyLLMClient()

    # Patch the LLM client imports before importing the command processor
    with patch('core.llm.client.llm_client', mock_llm), \
         patch('core.nlp.command_processor.llm_client', mock_llm):
        
        # Now import the modules that depend on the LLM client
        from core.nlp.command_processor import NLPCommandProcessor
        from core.project.manager import ProjectManager
        
        # Reload the module to ensure patches are applied
        import core.nlp.command_processor
        importlib.reload(core.nlp.command_processor)

except ImportError as e:
    print(f"Error importing modules: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

async def test_nlp_processor():
    """Test the NLP processor with basic commands."""
    print("=== Testing NLP processor ===")
    
    # Create test directory
    test_dir = Path.cwd() / "test_projects"
    test_dir.mkdir(exist_ok=True)
    
    # Initialize components
    try:
        print("\n[DEBUG] Initializing ProjectManager...")
        project_manager = ProjectManager(test_dir)
        
        print("[DEBUG] Creating LazyLLMClient instance...")
        # Ensure the mock client is initialized
        mock_llm._ensure_initialized()
        print(f"[DEBUG] Using mock LLM client: {mock_llm}")
        
        # Create the NLP command processor
        print("[DEBUG] Creating NLPCommandProcessor instance...")
        processor = NLPCommandProcessor()
        
        # Make sure the processor is using our mock LLM client
        if hasattr(processor, 'llm_client'):
            print("[DEBUG] Setting processor.llm_client to our mock")
            processor.llm_client = mock_llm
            
    except Exception as e:
        print(f"Failed to initialize components: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test context - create a proper CommandContext-like object
    class CommandContext:
        def __init__(self, chat_id, user_id, bot_data, project_manager, current_project):
            self.chat_id = chat_id
            self.user_id = user_id
            self.bot_data = bot_data
            self.project_manager = project_manager
            self.current_project = current_project
            
            # Add project_manager to bot_data for backward compatibility
            self.bot_data['project_manager'] = project_manager
    
    # Initialize context with required attributes
    context = CommandContext(
        chat_id="test_chat",
        user_id="test_user",
        bot_data={"active_projects": {}},
        project_manager=project_manager,
        current_project=None
    )
    
    # Create a function to get a fresh context for each test
    def get_fresh_context():
        # Create a deep copy of the context to avoid reference issues
        new_bot_data = {}
        if hasattr(context, 'bot_data'):
            new_bot_data = context.bot_data.copy()
            if 'active_projects' in new_bot_data:
                new_bot_data['active_projects'] = new_bot_data['active_projects'].copy()
        
        # Ensure project_manager is in bot_data
        if 'project_manager' not in new_bot_data:
            new_bot_data['project_manager'] = project_manager
            
        # Get current project, either from context or from active_projects
        current_project = getattr(context, 'current_project', None)
        if not current_project and 'active_projects' in new_bot_data:
            current_project = new_bot_data['active_projects'].get("test_chat")
            
        return CommandContext(
            chat_id="test_chat",
            user_id="test_user",
            bot_data=new_bot_data,
            project_manager=project_manager,
            current_project=current_project
        )
    
    # Test commands with expected responses
    test_commands = [
        ("Создай проект test_project", "test_project"),
        ("Активируй проект test_project", "Switched to project 'test_project'"),
        ("Создай файл main.py с кодом print('Hello')", "main.py", {"project": "test_project"}),
        ("Покажи список проектов", "test_project"),
    ]
    
    passed = 0
    
    # Run test commands
    for i, test_item in enumerate(test_commands, 1):
        # Handle both (command, expected) and (command, expected, kwargs) formats
        if len(test_item) == 2:
            command, expected = test_item
            command_kwargs = {}
        else:
            command, expected, command_kwargs = test_item
            
        print(f"\n[TEST] {command}")
        print(f"Expected: {expected}")
        
        # Get a fresh context for each test
        test_context = get_fresh_context()
        
        # Skip create project test if project already exists
        if i == 1:
            # Check if project directory exists
            project_path = test_context.project_manager.projects_dir / 'test_project'
            if project_path.exists():
                print("[SKIPPED] Project already exists")
                continue
        
        # Apply any command-specific context updates
        if 'project' in command_kwargs:
            print(f"[DEBUG] Setting project in context: {command_kwargs['project']}")
            test_context.current_project = command_kwargs['project']
            if not hasattr(test_context, 'bot_data'):
                print("[DEBUG] Initializing empty bot_data in context")
                test_context.bot_data = {}
            if 'active_projects' not in test_context.bot_data:
                print("[DEBUG] Initializing empty active_projects in bot_data")
                test_context.bot_data['active_projects'] = {}
            test_context.bot_data['active_projects'][str(test_context.chat_id)] = command_kwargs['project']
            print(f"[DEBUG] Updated bot_data['active_projects']: {test_context.bot_data['active_projects']}")
            print(f"[DEBUG] Context state after update - current_project: {getattr(test_context, 'current_project', None)}")
            print(f"[DEBUG] Context state after update - bot_data: {getattr(test_context, 'bot_data', {})}")
        
        try:
            # Process the command
            with patch('core.llm.client.llm_client', mock_llm):
                success, response = await processor.process_command(
                    text=command,
                    context=test_context,
                    chat_id=test_context.chat_id,
                    user_id=test_context.user_id
                )
                
                # Update the main context with any state changes from the test context
                if hasattr(test_context, 'current_project') and test_context.current_project:
                    context.current_project = test_context.current_project
                    print(f"[DEBUG] Updated context.current_project: {context.current_project}")
                
                if hasattr(test_context, 'bot_data') and test_context.bot_data:
                    print(f"[DEBUG] Updating context with bot_data: {test_context.bot_data}")
                    
                    # Initialize bot_data if it doesn't exist
                    if not hasattr(context, 'bot_data') or not context.bot_data:
                        context.bot_data = {}
                    
                    # Update active_projects if it exists in test_context
                    if 'active_projects' in test_context.bot_data:
                        if 'active_projects' not in context.bot_data:
                            context.bot_data['active_projects'] = {}
                        
                        print(f"[DEBUG] Updating active_projects. Before: {context.bot_data['active_projects']}")
                        context.bot_data['active_projects'].update(test_context.bot_data['active_projects'])
                        print(f"[DEBUG] After update: {context.bot_data['active_projects']}")
                        
                        # Update current_project from active_projects if it's set there
                        if context.chat_id in test_context.bot_data['active_projects']:
                            context.current_project = test_context.bot_data['active_projects'][context.chat_id]
                            print(f"[DEBUG] Updated current_project from active_projects: {context.current_project}")
                    
                    # Copy other bot_data fields
                    for key, value in test_context.bot_data.items():
                        if key != 'active_projects':  # We already handled this
                            context.bot_data[key] = value
            
            print(f"Response: {response}")
            
            # Check if the response contains the expected text
            if expected.lower() in str(response).lower():
                print("[PASSED]")
                passed += 1
            else:
                print(f"[FAILED] Expected to find: {expected}")
                print(f"Full response: {response}")
        except Exception as e:
            print(f"[ERROR] Test failed with exception: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    # Set up asyncio event loop policy for Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(test_nlp_processor())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Unexpected error: {e}")
