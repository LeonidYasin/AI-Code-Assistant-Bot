"""
Natural Language Processing for command conversion - New Implementation

This is a refactored version of the NLP processor that uses a modular architecture
with separate components for command processing, prompt building, and response parsing.
"""
import logging
import asyncio
from typing import Dict, Any, Optional, Tuple, Union
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from core.nlp import default_processor as nlp_processor
from core.nlp.command_processor import CommandContext
from core.project.manager import ProjectManager

logger = logging.getLogger(__name__)

class NLPProcessorWrapper:
    """Wrapper around the NLP processor to handle Telegram-specific logic."""
    
    def __init__(self):
        """Initialize the NLP processor wrapper."""
        self.processor = nlp_processor
    
    async def process_command(
        self, 
        text: str, 
        context: Union[ContextTypes.DEFAULT_TYPE, Dict[str, Any]],
        chat_id: Optional[Union[int, str]] = None,
        user_id: Optional[Union[int, str]] = None
    ) -> Tuple[bool, str]:
        """Process a natural language command.
        
        Args:
            text: The user's input text
            context: The context object (Telegram or dict)
            chat_id: Optional chat ID (if not provided, will be extracted from context)
            user_id: Optional user ID (if not provided, will be extracted from context)
            
        Returns:
            Tuple of (success, response_message)
        """
        # Initialize context data
        if hasattr(context, 'bot_data'):
            # Telegram context
            bot_data = context.bot_data or {}
            chat_id = chat_id or getattr(context, '_chat_id', 0)
            user_id = user_id or getattr(update.effective_user, 'id', 0) if hasattr(context, 'update') and hasattr(context.update, 'effective_user') else 0
        else:
            # Plain dict context
            bot_data = context or {}
            chat_id = chat_id or 0
            user_id = user_id or 0
        
        # Convert IDs to strings for consistency
        chat_id = str(chat_id)
        user_id = str(user_id)
        
        # Ensure active_projects exists
        if 'active_projects' not in bot_data:
            bot_data['active_projects'] = {}
        
        # Get or initialize project manager
        if 'project_manager' not in bot_data:
            base_dir = Path(__file__).parent.parent.absolute()
            bot_data['project_manager'] = ProjectManager(base_dir)
        
        try:
            # Create command context
            cmd_context = CommandContext(
                chat_id=chat_id,
                user_id=user_id,
                bot_data=bot_data,
                project_manager=bot_data['project_manager'],
                current_project=bot_data['active_projects'].get(chat_id)
            )
            
            # Process the command
            success, response = await self.processor.process_command(
                text=text,
                context=cmd_context
            )
            
            # Update active projects in the original context
            if hasattr(context, 'bot_data'):
                context.bot_data['active_projects'] = bot_data['active_projects']
            else:
                context['active_projects'] = bot_data['active_projects']
            
            return success, response
            
        except Exception as e:
            logger.error(f"Error in process_command: {str(e)}", exc_info=True)
            return False, f"❌ An error occurred: {str(e)}"

# Global instance for backward compatibility
nlp_processor = NLPProcessorWrapper()

# For backward compatibility
async def process_nlp_command(text: str, context: Union[ContextTypes.DEFAULT_TYPE, Dict[str, Any]]) -> Tuple[bool, str]:
    """Process a natural language command (legacy interface)."""
    return await nlp_processor.process_command(text, context)
