"""
Command processor module for handling bot commands.
"""
import logging
from typing import Optional, List, Any, Dict

from telegram import Update
from telegram.ext import ContextTypes, CallbackContext, Application

logger = logging.getLogger(__name__)

class CommandProcessor:
    """Processes bot commands and routes them to appropriate handlers."""
    
    def __init__(self, application: Application):
        """Initialize the command processor."""
        self.application = application
        self.handlers = []
    
    async def process_command(self, command: str, chat_id: int = 12345) -> None:
        """Process a command from CLI."""
        update = self._create_fake_update(command, chat_id)
        context = self._create_fake_context()
        
        # Set up context args based on command
        parts = command.split()
        if parts and parts[0].startswith('/'):
            parts[0] = parts[0][1:]  # Remove leading slash
        
        context.args = parts[1:] if len(parts) > 1 else []
        
        if not parts:
            await update.message.reply_text("❌ No command provided. Type /help for available commands.")
            return
        
        command_name = parts[0].lower()
        logger.info(f"Processing command: {command_name} with args: {context.args}")
        
        # Special case for project commands
        if command_name == 'project':
            await self._handle_project_command(update, context)
            return
        
        # Try to find a handler for the command
        await self._route_to_handlers(command_name, update, context)
    
    async def _handle_project_command(self, update: Update, context: CallbackContext) -> None:
        """Handle project-related commands."""
        for handler in self.handlers:
            if hasattr(handler, 'handle_project_command'):
                try:
                    await handler.handle_project_command(update, context)
                    return
                except Exception as e:
                    logger.error(f"Error in ProjectHandler: {e}", exc_info=True)
        
        await update.message.reply_text("❌ Project commands are not available.")
    
    async def _route_to_handlers(self, command_name: str, update: Update, context: CallbackContext) -> None:
        """Route command to appropriate handlers."""
        for handler in self.handlers:
            try:
                # Try direct command handling
                if hasattr(handler, 'handle_command'):
                    result = await handler.handle_command(command_name, update=update, context=context)
                    if result is not None:
                        await update.message.reply_text(str(result))
                        return
                
                # Try the standard handle method
                if hasattr(handler, 'handle'):
                    result = await handler.handle(command_name, update=update, context=context)
                    if result is not None:
                        await update.message.reply_text(str(result))
                        return
                        
            except Exception as e:
                logger.error(f"Error in handler {handler.__class__.__name__}: {e}", exc_info=True)
        
        # If no handler was found
        await update.message.reply_text("❌ Command not recognized. Type /help for help.")
    
    def _create_fake_update(self, text: str, chat_id: int) -> Update:
        """Create a fake update object for CLI commands."""
        class FakeUpdate:
            def __init__(self, text, chat_id):
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
                        self.id = chat_id
                        self.first_name = "CLI"
                        self.last_name = "User"
                        self.username = "cli_user"
                
                async def reply_text(self, text, **kwargs):
                    print(f"\nBot response:\n{text}\n")
                    return True
        
        return FakeUpdate(text, chat_id)
    
    def _create_fake_context(self) -> CallbackContext:
        """Create a fake context object for CLI commands."""
        return CallbackContext(Application.builder().token("dummy").build())
