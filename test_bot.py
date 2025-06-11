import asyncio
import os
import sys
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, ContextTypes

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the bot components
from handlers.project_handlers import ProjectHandlers
from core.llm.client import LLMClient  # Assuming this is your LLM client class

# Load environment variables
load_dotenv()

class TestBot:
    def __init__(self):
        self.llm_client = LLMClient()
        self.handlers = ProjectHandlers(self.llm_client)
        self.chat_id = 12345  # Test chat ID
        
    async def send_message(self, text: str):
        """Simulate sending a message to the bot"""
        print(f"\n{'='*50}")
        print(f"YOU: {text}")
        print(f"{'='*50}")
        
        # Create a mock update
        update = Update(
            update_id=1,
            message={
                'message_id': 1,
                'from': {'id': self.chat_id, 'is_bot': False, 'first_name': 'TestUser'},
                'chat': {'id': self.chat_id, 'type': 'private'},
                'date': 1234567890,
                'text': text
            }
        )
        
        # Create a mock context
        context = ContextTypes.DEFAULT_TYPE
        context.bot = {
            'token': 'test_token',
            'send_message': self._mock_send_message
        }
        context.user_data = {}
        
        # Process the message
        if text.startswith('/'):
            # Handle commands
            command = text.split()[0].lstrip('/')
            if command == 'test':
                await self.handlers.test_command(update, context)
            elif command == 'project':
                await self.handlers.handle_project_command(update, context)
            elif command == 'list':
                await self.handlers._handle_list_files(update, context)
            elif command == 'analyze':
                await self.handlers._handle_analyze(update, context)
            else:
                await self.handlers.handle_project_message(update, context)
        else:
            await self.handlers.handle_project_message(update, context)
    
    async def _mock_send_message(self, chat_id=None, text=None, **kwargs):
        """Mock the send_message method to print the bot's response"""
        print(f"\nBOT: {text}")
        if 'reply_markup' in kwargs:
            print("Buttons:", kwargs['reply_markup'])
        return {'message_id': 2}

    async def run(self):
        """Run the test bot in interactive mode"""
        print("Test Bot started. Type 'exit' to quit.")
        print("Available commands:")
        print("- /test - Show test menu")
        print("- /project list - List projects")
        print("- /analyze <code> - Analyze code")
        print("- Or type any natural language request")
        
        while True:
            try:
                text = input("\nYou: ").strip()
                if text.lower() in ('exit', 'quit', 'q'):
                    break
                if text:
                    await self.send_message(text)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    bot = TestBot()
    asyncio.run(bot.run())
