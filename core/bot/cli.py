"""CLI module for the bot application."""
import sys
import asyncio
import logging
from typing import List, Optional, Dict, Any, Callable, Awaitable

from telegram import Update
from telegram.ext import CallbackContext, ContextTypes, Application

from core.bot.types import CommandCallback

logger = logging.getLogger(__name__)

class CLICommand:
    """Represents a CLI command."""
    
    def __init__(
        self,
        name: str,
        callback: Callable,
        help_text: str = "",
        aliases: Optional[List[str]] = None
    ):
        self.name = name
        self.callback = callback
        self.help_text = help_text
        self.aliases = aliases or []

class CLIRunner:
    """Runs CLI commands with a fake Telegram update."""
    
    def __init__(self, application: Application):
        """Initialize the CLI runner."""
        self.application = application
        self.commands: Dict[str, CLICommand] = {}
        
        # Register built-in commands
        self.register_command(
            CLICommand(
                name="help",
                callback=self._show_help,
                help_text="Show this help message"
            )
        )
        
        # Register custom commands
        from core.bot.cli_commands import register_cli_commands
        register_cli_commands(self)
    
    def register_command(self, command: CLICommand) -> None:
        """Register a CLI command."""
        self.commands[command.name] = command
        for alias in command.aliases:
            self.commands[alias] = command
    
    async def _show_help(self, args: List[str], update: Update, context: CallbackContext) -> None:
        """Show help message."""
        help_text = ["Available commands:"]
        for cmd in sorted(set(cmd.name for cmd in self.commands.values())):
            cmd_obj = self.commands[cmd]
            help_text.append(f"  {cmd}: {cmd_obj.help_text}")
        
        await update.message.reply_text("\n".join(help_text))
    
    async def run(self, args: List[str]) -> int:
        """Run a CLI command.
        
        Args:
            args: Command line arguments.
            
        Returns:
            int: Exit code.
        """
        if not args:
            args = ["help"]
        
        command_name = args[0].lower()
        command_args = args[1:]
        
        if command_name not in self.commands:
            print(f"Unknown command: {command_name}", file=sys.stderr)
            print("Use 'help' to see available commands.", file=sys.stderr)
            return 1
        
        # Create a fake update
        update = self._create_fake_update(" ".join(args))
        context = self._create_fake_context()
        
        # Run the command
        try:
            await self.commands[command_name].callback(command_args, update, context)
            return 0
        except Exception as e:
            logger.error(f"Error executing command '{command_name}': {e}", exc_info=True)
            return 1
    
    def _create_fake_update(self, text: str) -> Update:
        """Create a fake update object for CLI commands."""
        class FakeUpdate:
            def __init__(self, text):
                self.message = self.Message(text)
                self.effective_chat = self.message.chat
                self.effective_user = self.message.from_user
                
            class Message:
                def __init__(self, text):
                    self.text = text
                    self.chat = self.Chat()
                    self.from_user = self.User()
                    
                class Chat:
                    def __init__(self):
                        self.id = 12345
                        self.type = "private"
                        
                class User:
                    def __init__(self):
                        self.id = 12345
                        self.first_name = "CLI"
                        self.last_name = "User"
                        self.username = "cli_user"
                        self.is_bot = False
                
                async def reply_text(self, text: str, **kwargs) -> None:
                    """Print the response to stdout."""
                    print(f"\n{text}")
                    return True
        
        return FakeUpdate(text)
    
    def _create_fake_context(self) -> CallbackContext:
        """Create a fake context object for CLI commands."""
        return CallbackContext(application=self.application)

def run_cli() -> int:
    """Run the CLI interface."""
    # Create a minimal application
    app = Application.builder().token("dummy").build()
    
    # Create and run the CLI
    cli = CLIRunner(app)
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, use create_task
            task = loop.create_task(cli.run(sys.argv[1:]))
            return loop.run_until_complete(task)
        else:
            # Otherwise, use run_until_complete
            return loop.run_until_complete(cli.run(sys.argv[1:]))
    except RuntimeError as e:
        if "no running event loop" in str(e):
            # If no event loop is running, create a new one
            return asyncio.run(cli.run(sys.argv[1:]))
        raise
