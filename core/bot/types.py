"""Type definitions for the bot application."""
from typing import Union, Callable, Awaitable, Any, Dict, List, Optional
from telegram import Update
from telegram.ext import CallbackContext, ContextTypes, BaseHandler

# Type aliases
HandlerType = Union[
    BaseHandler,
    Callable[[Update, CallbackContext], Awaitable[None]]
]

CommandCallback = Callable[[Update, CallbackContext], Awaitable[None]]

class CommandInfo:
    """Information about a bot command."""
    def __init__(
        self,
        command: str,
        description: str,
        handler: CommandCallback,
        hidden: bool = False,
        admin_only: bool = False,
        usage: str = ""
    ):
        self.command = command
        self.description = description
        self.handler = handler
        self.hidden = hidden
        self.admin_only = admin_only
        self.usage = usage

class ModuleInfo:
    """Information about a bot module."""
    def __init__(
        self,
        name: str,
        description: str,
        commands: List[CommandInfo],
        handlers: Optional[List[HandlerType]] = None,
        startup: Optional[Callable] = None,
        shutdown: Optional[Callable] = None
    ):
        self.name = name
        self.description = description
        self.commands = commands
        self.handlers = handlers or []
        self.startup = startup
        self.shutdown = shutdown
