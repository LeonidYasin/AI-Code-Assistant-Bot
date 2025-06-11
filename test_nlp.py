"""Test script for NLP processor with command confirmation"""
import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from core.bot.command_processor import CommandProcessor
from core.project.manager import ProjectManager
from telegram.ext import Application

async def main():
    # Initialize the application
    application = Application.builder().token("dummy").build()
    
    # Initialize project manager
    project_manager = ProjectManager(base_path=os.path.join("projects"))
    
    # Initialize command processor
    command_processor = CommandProcessor(application, project_manager)
    
    # Test natural language command
    test_command = "Создай файл test.txt с текстом 'Привет, мир!'"
    print(f"\n{'='*50}")
    print(f"Testing command: {test_command}")
    print(f"{'='*50}\n")
    
    # Process the command
    success, response = await command_processor.process_command(test_command, chat_id=0)
    
    if success:
        print(f"\n✅ Success: {response}")
    else:
        print(f"\n❌ Error: {response}")

if __name__ == "__main__":
    asyncio.run(main())
