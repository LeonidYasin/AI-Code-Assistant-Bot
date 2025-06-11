"""Test bot commands in CLI mode."""
import asyncio
import logging
import os
import sys
from core.bot.application import BotApplication
from handlers import register_handlers

# Configure console encoding for Windows
if sys.platform == 'win32':
    import io
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Lower level to reduce noise
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Disable some noisy loggers
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)

# Use None for chat_id to indicate CLI mode
TEST_CHAT_ID = None

async def test_commands():
    """Test bot commands."""
    # Initialize bot with a dummy token for testing
    bot = BotApplication()
    await bot.initialize()
    
    # Register handlers
    await register_handlers(bot)
    
    # Test project commands
    print("\n=== Testing project commands ===")
    
    # Test list projects
    print("\n=== Testing list projects ===")
    try:
        await bot.process_command("/project list", chat_id=TEST_CHAT_ID)
    except Exception as e:
        print(f"Error listing projects: {e}")
    
    # Test create project
    print("\n=== Testing create project ===")
    test_project_name = "test_project_new"
    try:
        await bot.process_command(f"/project create {test_project_name}", chat_id=TEST_CHAT_ID)
        print(f"Successfully created project: {test_project_name}")
    except Exception as e:
        if "already exists" in str(e):
            print(f"Project '{test_project_name}' already exists, skipping creation")
        else:
            print(f"Error creating project: {e}")
    
    # Test project info
    print("\n=== Testing project info ===")
    try:
        await bot.process_command("/project info", chat_id=TEST_CHAT_ID)
    except Exception as e:
        print(f"Error getting project info: {e}")
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    asyncio.run(test_commands())
