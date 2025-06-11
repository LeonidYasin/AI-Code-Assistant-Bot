#!/usr/bin/env python3
"""
Main entry point for the AI Code Assistant bot.

This module initializes the bot and sets up all command handlers.
"""
import asyncio
import logging
import sys
from pathlib import Path

# Import core bot components
from core.bot.application import BotApplication

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import and register modules
from handlers import register_handlers

async def run_cli() -> int:
    """Run the bot in CLI mode."""
    if len(sys.argv) < 2:
        print("Usage: python main.py <command or natural language request>")
    # Initialize the bot
    bot = BotApplication()
    await bot.initialize()
    
    # Initialize project manager if needed
    if not hasattr(bot, 'project_manager'):
        from core.project.manager import ProjectManager
        # Use the bot's base directory as the base path
        base_dir = Path(__file__).parent.absolute()
        bot.project_manager = ProjectManager(base_dir)
        
        # Set a default project for CLI mode
        default_project = 'default_cli_project'
        bot.project_manager.current_project = default_project
        
        # Create projects directory if it doesn't exist
        projects_dir = base_dir / 'projects'
        projects_dir.mkdir(exist_ok=True)
        
        # Create default project directory if it doesn't exist
        default_project_dir = projects_dir / default_project
        default_project_dir.mkdir(exist_ok=True)
        
        # Save project info
        bot.project_manager._save_config()
        bot.bot_data['project_manager'] = bot.project_manager
    
    # Register all handlers
    await register_handlers(bot)
    
    # Debug: Print registered commands
    print("\n[DEBUG] Registered commands:")
    for cmd in sorted(bot._commands.keys()):
        print(f"- {cmd}")
    print()
    
    # Get user input
    user_input = " ".join(sys.argv[1:])
    if not user_input:
        print("Usage: python main.py <command>")
        print("Or use natural language like: python main.py \"Create a new project\"")
        return 0
        
    # Process the input (could be a command or natural language)
    try:
        # Create or reuse context for CLI mode
        if not hasattr(bot, '_cli_context'):
            class Context:
                def __init__(self):
                    from core.project.manager import ProjectManager
                    
                    # Initialize project manager
                    self.project_manager = ProjectManager()
                    
                    # Initialize bot data
                    self._bot_data = {
                        'active_projects': {},
                        'project_states': {},
                        'project_manager': self.project_manager  # Add project manager to bot_data
                    }
                    self._chat_id = 0  # Use 0 for CLI mode
                    
                    # Initialize active_projects if not exists
                    if '0' not in self._bot_data['active_projects']:
                        self._bot_data['active_projects']['0'] = None
                    
                    # Set active project from project_manager if available
                    if self.project_manager.current_project:
                        self._bot_data['active_projects']['0'] = self.project_manager.current_project
                
                @property
                def bot_data(self):
                    return self._bot_data
                    
                @bot_data.setter
                def bot_data(self, value):
                    self._bot_data = value
                    
                async def send_message(self, chat_id, text, **kwargs):
                    print("\n" + "="*50)
                    print(f"BOT RESPONSE:")
                    print("-"*50)
                    print(text)
                    print("="*50 + "\n")
                    return text
            
            bot._cli_context = Context()
            
            # Set the project_manager attribute on the bot for backward compatibility
            bot.project_manager = bot._cli_context.project_manager
        
        # Check for analyze_project command
        if user_input.strip().lower() in ['analyze_project', '/analyze_project']:
            try:
                # Import the NLP processor
                from handlers.nlp_processor import nlp_processor
                
                # Create a context object for the CLI
                class CliContext:
                    def __init__(self, bot):
                        self.bot_data = {
                            'project_manager': bot._cli_context.project_manager,
                            'active_projects': {'0': bot._cli_context.project_manager.current_project}
                        }
                    
                    @property
                    def _chat_id(self):
                        return 0  # Use 0 as the default chat ID for CLI
                
                # Create the context
                context = CliContext(bot)
                
                # Call the analyze_project handler
                success, result = await nlp_processor._handle_analyze_project(context)
                
                # Print the result
                print("\n" + "="*50)
                print("📊 Project Analysis Result")
                print("="*50)
                print(result)
                
                if not success:
                    return 1
                    
            except Exception as e:
                print(f"❌ Error analyzing project: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc()
                return 1
                
            return 0
        
        # Process other commands with the existing context
        success, response = await bot.command_processor.process_command(user_input, bot._cli_context)
        
        # Print the response
        if response:
            print("\n[CLI RESPONSE]" + "="*40)
            print(response)
            print("="*40 + "\n")
            
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"Error in CLI mode: {e}", exc_info=True)
        return 1
    finally:
        # Clean up resources
        if hasattr(bot, 'close'):
            await bot.close()
        elif hasattr(bot, 'shutdown'):
            await bot.shutdown()

async def main() -> int:
    """Main entry point for the application."""
    # Set up output encoding for Windows
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, 
            encoding='utf-8', 
            errors='replace',
            line_buffering=True
        )
    
    # Check if running in CLI mode
    if len(sys.argv) > 1:
        return await run_cli()
    
    # Initialize and run the bot
    bot = BotApplication()
    
    try:
        # Register all handlers
        await register_handlers(bot)
        
        # Run the bot
        await bot.initialize()
        await bot.run_polling()
        
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        return 1
    
    return 0

def run():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
        return 0
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(run())