from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class BaseHandler(ABC):
    """Base class for all command handlers"""
    
    def __init__(self, bot=None):
        self.bot = bot
        self.commands = self.get_commands()
    
    @abstractmethod
    def get_commands(self) -> Dict[str, dict]:
        """Return supported commands and their handlers"""
        return {}
    
    async def handle(self, command: str, *args, **kwargs) -> Optional[str]:
        """Handle a command"""
        import logging
        logger = logging.getLogger(__name__)
        
        cmd = command.lstrip('/').lower()
        if cmd in self.commands:
            handler = self.commands[cmd].get('handler')
            if handler:
                logger.debug(f"Handling command '{cmd}' with handler {handler.__name__}")
                # Create a copy of kwargs without 'self' if it exists
                handler_kwargs = {k: v for k, v in kwargs.items() if k != 'self'}
                return await handler(self, *args, **handler_kwargs)
        return None
    
    def register_handlers(self, application):
        """Register command handlers with the application"""
        for cmd, config in self.commands.items():
            if 'handler' in config:
                application.add_handler(
                    config.get('handler_type', CommandHandler)(
                        cmd, 
                        getattr(self, config['handler'].__name__)
                    )
                )
