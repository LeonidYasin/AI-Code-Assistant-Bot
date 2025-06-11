import asyncio
import logging
from pathlib import Path
import sys
import io
import sys
from typing import Dict, Any

# Set up console encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

# Import the project handler
from handlers.project import ProjectHandler
from core.project.manager import ProjectManager

class FakeUpdate:
    def __init__(self, text, chat_id=12345):
        self.message = self.Message(text, chat_id)
        self.effective_chat = self.message.chat
        self.effective_user = self.message.from_user
        
    class Message:
        def __init__(self, text, chat_id):
            self.text = text
            self.chat = self.Chat(chat_id)
            self.from_user = self.User()
            
        class Chat:
            def __init__(self, id):
                self.id = id
                
        class User:
            def __init__(self):
                self.id = 12345
                self.first_name = "Test"
                self.last_name = "User"
                self.username = "testuser"
        
        async def reply_text(self, text, **kwargs):
            try:
                print(f"\nBot response:\n{text}\n")
            except UnicodeEncodeError:
                # Fallback for Windows console
                cleaned = text.encode('utf-8', errors='replace').decode('utf-8')
                print(f"\nBot response:\n{cleaned}\n")
            return True

class FakeContext:
    def __init__(self):
        self.args = []

async def test_project_commands():
    # Initialize the project manager and handler
    project_manager = ProjectManager()
    handler = ProjectHandler()
    
    # Test project list
    print("\n=== Testing project list ===")
    update = FakeUpdate("/project list")
    context = FakeContext()
    context.args = ["list"]
    await handler.handle_project_command(update, context)
    
    # Test project info (no project selected)
    print("\n=== Testing project info (no project) ===")
    update = FakeUpdate("/project info")
    context.args = ["info"]
    await handler.handle_project_command(update, context)
    
    # Test project create
    print("\n=== Testing project create ===")
    update = FakeUpdate("/project create test_project")
    context.args = ["create", "test_project"]
    await handler.handle_project_command(update, context)
    
    # Test project list again
    print("\n=== Testing project list after creation ===")
    update = FakeUpdate("/project list")
    context.args = ["list"]
    await handler.handle_project_command(update, context)
    
    # Test project switch
    print("\n=== Testing project switch ===")
    update = FakeUpdate("/project switch test_project")
    context.args = ["switch", "test_project"]
    await handler.handle_project_command(update, context)
    
    # Test project info
    print("\n=== Testing project info ===")
    update = FakeUpdate("/project info")
    context.args = ["info"]
    await handler.handle_project_command(update, context)

if __name__ == "__main__":
    asyncio.run(test_project_commands())
