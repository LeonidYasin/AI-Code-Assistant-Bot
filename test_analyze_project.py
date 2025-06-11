#!/usr/bin/env python3
"""
Test script for the analyze_project command.
"""
import asyncio
import logging
from pathlib import Path
from unittest.mock import MagicMock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_analyze_project():
    """Test the analyze_project command."""
    try:
        # Import the ProjectHandlers class
        from handlers.project_handlers import ProjectHandlers
        from core.project.manager import ProjectManager
        from core.llm.client import LLMClient
        
        # Initialize the LLM client
        llm_client = LLMClient()
        
        # Create a test project directory
        base_dir = Path(__file__).parent.absolute()
        test_project_dir = base_dir / "projects" / "test_analysis_project"
        test_project_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a test file
        test_file = test_project_dir / "test_file.py"
        test_file.write_text("""
        def hello():
            print("Hello, World!")
            return 42
        """)
        
        # Initialize the project manager
        project_manager = ProjectManager(base_dir)
        project_manager.current_project = "test_analysis_project"
        
        # Initialize the project handlers
        project_handlers = ProjectHandlers(llm_client)
        
        # Create a mock update object
        update = MagicMock()
        update.effective_chat.id = 12345
        update.message.reply_text = MagicMock()
        
        # Create a mock context object
        context = MagicMock()
        context.bot_data = {
            'project_manager': project_manager,
            'active_projects': {}
        }
        
        # Call the analyze_project method directly
        logger.info("Testing analyze_project command...")
        await project_handlers._handle_analyze_project(update, context)
        
        # Check if the reply_text was called
        update.message.reply_text.assert_called()
        logger.info("analyze_project command executed successfully!")
        
        # Print the calls to reply_text for debugging
        for call in update.message.reply_text.call_args_list:
            args, kwargs = call
            logger.info(f"Reply text: {args[0]}")
            
    except Exception as e:
        logger.error(f"Error in test_analyze_project: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(test_analyze_project())
