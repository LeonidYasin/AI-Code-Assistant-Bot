"""Bot application module."""
import asyncio
import logging
from typing import Optional, List, Dict, Any, Callable, Awaitable, Union

from telegram import Update, Bot
from telegram.ext import (
    Application as TelegramApplication,
    ApplicationBuilder,
    CallbackContext,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters
)

from core.bot.config import BOT_TOKEN, LOGGING_CONFIG
from core.bot.types import HandlerType, CommandCallback
from core.bot.command_processor import CommandProcessor

logger = logging.getLogger(__name__)

class BotApplication:
    """Main application class for the Telegram bot."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(BotApplication, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, token: str = None, cli_mode: bool = False):
        """Initialize the bot application.
        
        Args:
            token: Telegram bot token. If not provided, will be taken from config.
            cli_mode: If True, initialize in CLI mode without requiring a bot token.
        """
        if not BotApplication._initialized:
            if cli_mode:
                # In CLI mode, we don't need a real bot token
                self.token = "cli_mode"
            else:
                self.token = token or BOT_TOKEN
            
            self.app: Optional[TelegramApplication] = None
            self._handlers: List[HandlerType] = []
            self._commands: Dict[str, CommandCallback] = {}
            self._startup_callbacks: List[Callable] = []
            self._shutdown_callbacks: List[Callable] = []
            self.bot_data: Dict[str, Any] = {}
            # Initialize command processor with this instance
            self.command_processor = CommandProcessor(self)
            BotApplication._initialized = True
    
    def add_handler(self, handler: HandlerType) -> None:
        """Add a handler to the application."""
        self._handlers.append(handler)
    
    def add_command(self, command: str, callback: CommandCallback) -> None:
        """Add a command handler."""
        self._commands[command] = callback
    
    def on_startup(self, callback: Callable) -> Callable:
        """Register a callback to be called on bot startup."""
        self._startup_callbacks.append(callback)
        return callback
    
    def on_shutdown(self, callback: Callable) -> Callable:
        """Register a callback to be called on bot shutdown."""
        self._shutdown_callbacks.append(callback)
        return callback
        
    async def process_command(self, command_text: str, chat_id: int = None) -> None:
        """Process a command from the CLI or another source.
        
        Args:
            command_text: The full command text (e.g., "/project list")
            chat_id: The chat ID to send responses to. If None, runs in CLI mode.
        """
        await self.command_processor.process_command(command_text, chat_id)

    async def _send_response(self, chat_id: int, text: str) -> None:
        """Send a response to the specified chat or print to console.
        
        Args:
            chat_id: The chat ID to send the message to. If None, prints to console.
            text: The message text to send or print.
        """
        if hasattr(self, 'command_processor'):
            await self.command_processor._send_response(chat_id, text)
        else:
            # Fallback if command_processor is not available
            if chat_id is None or self.app is None or not hasattr(self.app, 'bot'):
                try:
                    print("\n" + "="*50)
                    print("BOT RESPONSE:")
                    print("-"*50)
                    print(text)
                    print("="*50 + "\n")
                except Exception as e:
                    logger.error(f"Error printing to console: {e}")
            else:
                try:
                    await self.app.bot.send_message(chat_id=chat_id, text=text)
                except Exception as e:
                    logger.error(f"Failed to send message to chat {chat_id}: {e}")
                    # Fall back to console if sending fails
                    print(f"\n[ERROR] Failed to send message to chat {chat_id}:")
                    print(text)
                    print()
    
    async def _setup_handlers(self) -> None:
        """Set up all registered handlers."""
        if not self.app:
            raise RuntimeError("Application not initialized")
        
        # Add command handlers
        for command, callback in self._commands.items():
            self.app.add_handler(CommandHandler(command, callback))
        
        # Add other handlers
        for handler in self._handlers:
            self.app.add_handler(handler)
    
    async def _on_startup(self, app: TelegramApplication) -> None:
        """Handle application startup."""
        logger.info("Starting bot application")
        
        # Call registered startup callbacks
        for callback in self._startup_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(app)
                else:
                    callback(app)
            except Exception as e:
                logger.error(f"Error in startup callback {callback.__name__}: {e}", exc_info=True)
    
    async def _on_shutdown(self, app: TelegramApplication) -> None:
        """Handle application shutdown."""
        logger.info("Shutting down bot application")
        
        # Call registered shutdown callbacks
        for callback in self._shutdown_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(app)
                else:
                    callback(app)
            except Exception as e:
                logger.error(f"Error in shutdown callback {callback.__name__}: {e}", exc_info=True)
    
    async def initialize(self) -> None:
        """Initialize the bot application."""
        if not self.token:
            raise ValueError("Bot token is not set")
        
        # Create application
        self.app = (
            ApplicationBuilder()
            .token(self.token)
            .post_init(self._on_startup)
            .post_shutdown(self._on_shutdown)
            .build()
        )
        
        # Set up handlers
        await self._setup_handlers()
    
    async def run_polling(self) -> None:
        """Run the bot in polling mode."""
        if not self.app:
            await self.initialize()
        
        logger.info("Starting bot in polling mode")
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        
        try:
            # Keep the application running
            while True:
                await asyncio.sleep(3600)  # Sleep for 1 hour
        except (KeyboardInterrupt, SystemExit):
            logger.info("Shutdown signal received")
        finally:
            # Stop the bot
            if self.app.updater.running:
                await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
    
    async def run_webhook(self, webhook_url: str, **kwargs) -> None:
        """Run the bot with webhook.
        
        Args:
            webhook_url: The URL to set as webhook.
            **kwargs: Additional arguments for webhook setup.
        """
        if not self.app:
            await self.initialize()
        
        logger.info(f"Starting bot with webhook: {webhook_url}")
        await self.app.initialize()
        await self.app.start()
        
        # Set webhook
        await self.app.bot.set_webhook(
            url=webhook_url,
            **kwargs
        )
        
        try:
            # Keep the application running
            while True:
                await asyncio.sleep(3600)  # Sleep for 1 hour
        except (KeyboardInterrupt, SystemExit):
            logger.info("Shutdown signal received")
        finally:
            # Stop the bot
            await self.app.stop()
            await self.app.shutdown()
            await self.app.bot.delete_webhook()

    def run(self, use_webhook: bool = False, webhook_url: str = None) -> None:
        """Run the bot application.
        
        Args:
            use_webhook: If True, use webhook mode instead of polling.
            webhook_url: The webhook URL (required if use_webhook=True).
        """
        try:
            if use_webhook:
                if not webhook_url:
                    raise ValueError("webhook_url is required when use_webhook=True")
                asyncio.run(self.run_webhook(webhook_url))
            else:
                asyncio.run(self.run_polling())
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Error running bot: {e}", exc_info=True)
            raise
