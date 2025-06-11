"""Module for registering all bot handlers."""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Type

from telegram.ext import Application, CommandHandler
from core.bot import BotApplication
from core.bot.types import ModuleInfo, CommandInfo, HandlerType

logger = logging.getLogger(__name__)

# Import all handler modules
from .project import ProjectHandler
from .file_handlers import FileHandler
from .code_handlers import CodeHandler

# Import additional handlers
from .project_handlers import register_project_handlers
from .message_handler import handle_message

# List of handler classes to register
HANDLER_CLASSES = [
    ProjectHandler,
    FileHandler,
    CodeHandler,
]

# Global instances
project_manager = None
llm_client = None

def get_module_info() -> List[ModuleInfo]:
    """Get information about all modules and their commands."""
    modules = []
    
    # Get module info from handler classes
    for handler_class in HANDLER_CLASSES:
        if hasattr(handler_class, 'get_module_info'):
            module_info = handler_class.get_module_info()
            if module_info:
                modules.append(module_info)
    
    return modules

async def register_handlers(bot: BotApplication) -> None:
    """Register all handlers with the bot application.
    
    Args:
        bot: The bot application instance.
    """
    global project_manager, llm_client
    
    # Initialize project manager if not already done
    if project_manager is None:
        from core.project.manager import ProjectManager
        project_manager = ProjectManager()
    
    # Initialize LLM client if not already done
    if llm_client is None:
        from core.llm.client import llm_client as llm
        llm.initialize(use_gigachat=True)
        llm_client = llm
    
    # Store instances in bot_data for later use
    bot.app.bot_data['project_manager'] = project_manager
    bot.app.bot_data['llm_client'] = llm_client
    
    # Register module commands and handlers
    for module in get_module_info():
        try:
            # Register commands
            for cmd in module.commands:
                bot.add_command(cmd.command, cmd.handler)
                logger.debug(f"Registered command: {cmd.command}")
            
            # Register additional handlers if any
            if hasattr(module, 'handlers') and module.handlers:
                for handler in module.handlers:
                    if isinstance(handler, tuple) and len(handler) == 2:
                        # Handler with callback
                        bot.app.add_handler(handler[0](handler[1]))
                    else:
                        # Direct handler instance
                        bot.app.add_handler(handler)
                    logger.debug(f"Registered handler: {handler.__class__.__name__}")
            
            logger.info(f"Registered module: {module.name}")
            
        except Exception as e:
            logger.error(f"Error registering module {module.name}: {e}", exc_info=True)
    
    # Register additional handlers
    try:
        # Register project handlers
        if 'register_project_handlers' in globals():
            await register_project_handlers(bot.app, llm_client)
        
        # Register message handler for natural language processing
        try:
            from telegram.ext import MessageHandler, filters
            bot.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
            logger.info("Message handler for natural language processing registered")
        except Exception as e:
            logger.error(f"Failed to register message handler: {e}", exc_info=True)
        
        logger.info("All handlers registered successfully")
    except Exception as e:
        logger.error(f"Error registering additional handlers: {e}", exc_info=True)
        raise
