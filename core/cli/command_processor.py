"""
CLI command processing utilities.
"""
import asyncio
import logging
import os
import sys
from typing import Optional, Tuple, Any, Dict, List

from core.cli.direct_commands import DirectCommandHandler
from core.cli.utils import is_direct_command
from core.cli.context import CLIContext

logger = logging.getLogger(__name__)

# ---------- NEW: Multi-LLM helpers ----------
import click
from core.ai.ai_router import ask  # маршрутизатор LLM


# ---------- существующие функции ----------
async def process_direct_command(command: str, bot=None) -> int:
    """Process a direct CLI command (starts with /)."""
    # Remove leading slash and split into parts
    command_parts = command[1:].split()
    if not command_parts:
        return 1
    return 0


def process_cli_command(bot=None) -> int:
    """Process the CLI command.

    This function handles CLI commands directly without requiring async/await.
    It's optimized for simple project management tasks.

    Args:
        bot: Optional bot instance (not used in CLI mode)

    Returns:
        int: Exit code (0 for success, non-zero for errors)
    """
    try:
        import sys
        from core.cli.direct_commands import get_help_text

        # Initialize command handler
        handler = DirectCommandHandler(llm_enabled=False)

        # Handle case when no command is provided
        if len(sys.argv) < 2:
            print(get_help_text())
            return 0

        command = sys.argv[1].lower()

        # --- новые команды ---
        if command == "analyze":
            return _run_analyze()
        if command == "switch-model":
            return _run_switch_model()

        # Handle help command
        if command in ('help', '--help', '-h'):
            print(get_help_text())
            return 0

        # Handle version command
        if command in ('--version', '-v'):
            try:
                from core import __version__
                print(f"AI Code Assistant v{__version__}")
            except ImportError:
                print("AI Code Assistant (version information not available)")
            return 0

        # Handle list_project command (support both singular and plural)
        if command in ['list_project', '/list_project', 'list_projects', '/list_projects']:
            success, result = handler.handle_list_projects()
            print(f"\n{result}")
            return 0 if success else 1

        # Handle project subcommands
        if command == 'project' and len(sys.argv) > 2:
            subcommand = sys.argv[2].lower()

            if subcommand == 'list':
                success, result = handler.handle_list_projects()
                print(f"\n{result}")
                return 0 if success else 1

            elif subcommand == 'info':
                success, result = handler.handle_project_info()
                print(f"\n{result}")
                return 0 if success else 1

            elif subcommand == 'switch' and len(sys.argv) > 3:
                project_name = sys.argv[3]
                success, result = handler.handle_switch_project(project_name)
                print(f"\n{result}")
                return 0 if success else 1

            elif subcommand == 'create' and len(sys.argv) > 3:
                project_name = sys.argv[3]
                success, result = handler.handle_create_project(project_name)
                print(f"\n{result}")
                return 0 if success else 1

            else:
                print(f"\n❌ Unknown project subcommand: {subcommand}")
                return 1

        # Handle file subcommands
        if command == 'file' and len(sys.argv) > 2:
            subcommand = sys.argv[2].lower()

            if subcommand == 'list':
                path = sys.argv[3] if len(sys.argv) > 3 else "."
                success, result = handler.handle_file_list(path)
                print(f"\n{result}")
                return 0 if success else 1

            elif subcommand == 'view' and len(sys.argv) > 3:
                file_path = sys.argv[3]
                success, result = handler.handle_file_view(file_path)
                print(f"\n{result}")
                return 0 if success else 1

            elif subcommand == 'create' and len(sys.argv) > 3:
                file_path = sys.argv[3]
                success, result = handler.handle_file_create(file_path)
                print(f"\n{result}")
                return 0 if success else 1

            else:
                print(f"\n❌ Unknown file subcommand: {subcommand}")
                return 1

        # If we get here, the command wasn't recognized
        print("\n❌ Unknown command. Use --help for usage information.")
        return 1

    except Exception as e:
        logger.error(f"Error processing CLI command: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        return 1


# ---------- NEW: реализация команд ----------
def _run_analyze() -> int:
    """python main.py analyze <path> [--model <provider>]"""
    if len(sys.argv) < 3:
        print("Usage: python main.py analyze <file_or_dir> [--model deepseek|kimi|gigachat]")
        return 1

    path = sys.argv[2]
    model = "hf_deepseek"
    if "--model" in sys.argv:
        idx = sys.argv.index("--model")
        if idx + 1 < len(sys.argv):
            model = sys.argv[idx + 1]

    asyncio.run(_async_analyze(path, model))
    return 0


async def _async_analyze(path: str, model: str):
    os.environ["PROVIDER"] = model
    with open(path, encoding="utf-8") as f:
        code = f.read()
    messages = [{"role": "user", "content": f"Проанализируй код:\n{code}"}]
    result = await ask(messages)
    print(result)


def _run_switch_model() -> int:
    """python main.py switch-model <provider>"""
    if len(sys.argv) < 3:
        print("Usage: python main.py switch-model deepseek|kimi|gigachat")
        return 1

    provider = sys.argv[2]
    print(f"✅ Для переключения на {provider} отредактируй .env:")
    print(f"   PROVIDER={provider}")
    return 0


# ---------- существующая async-версия ----------
async def process_async_cli_command(bot=None) -> int:
    """Process the CLI command with full async support.

    This is the original async version that's used for more complex commands
    that require async/await functionality.

    Args:
        bot: Optional bot instance

    Returns:
        int: Exit code (0 for success, non-zero for errors)
    """
    import sys
    try:
        # Create a CLI context
        context = CLIContext()

        # Handle case when no command is provided
        if len(sys.argv) < 2:
            from core.cli.direct_commands import get_help_text
            print(get_help_text())
            return 0

        command = sys.argv[1].lower()

        # Handle help command
        if command in ('help', '--help', '-h'):
            from core.cli.direct_commands import get_help_text
            print(get_help_text())
            return 0

        # Handle version command
        if command in ('--version', '-v'):
            try:
                from core import __version__
                print(f"AI Code Assistant v{__version__}")
            except ImportError:
                print("AI Code Assistant (version information not available)")
            return 0

        # Handle direct commands (starting with /)
        if is_direct_command(command):
            return await process_direct_command(command, bot)

        # Handle project commands
        if command == 'project':
            if len(sys.argv) < 3:
                print("\n❌ Project subcommand not specified. Use 'project list', 'project create <name>', etc.")
                return 1

            subcommand = sys.argv[2].lower()

            if subcommand == 'list':
                success, projects = context.project_manager.list_projects()
                if success:
                    from core.cli.utils import format_project_list
                    print(format_project_list(projects))
                    return 0
                else:
                    print(f"\n❌ Error: {projects}")
                    return 1

            elif subcommand == 'create' and len(sys.argv) > 3:
                project_name = sys.argv[3]
                success, result = context.project_manager.create_project(project_name)
                if success:
                    print(f"\n✅ Project created: {result}")
                    return 0
                else:
                    print(f"\n❌ Error creating project: {result}")
                    return 1

            elif subcommand == 'switch' and len(sys.argv) > 3:
                project_name = sys.argv[3]
                if context.project_manager.switch_project(project_name):
                    print(f"\n✅ Switched to project: {project_name}")
                    return 0
                else:
                    print(f"\n❌ Failed to switch to project: {project_name}")
                    return 1

            elif subcommand == 'info':
                info = context.project_manager.get_project_info()
                if 'error' in info:
                    print(f"\n❌ Error: {info['error']}")
                    return 1

                print("\n📋 Project information:")
                print(f"Name: {info.get('name', 'Unknown')}")
                print(f"Path: {info.get('path', 'Not specified')}")
                print(f"Created: {info.get('created_at', 'Unknown')}")
                print(f"Files: {info.get('file_count', 0)}")
                return 0

            else:
                print(f"\n❌ Unknown project subcommand: {subcommand}")
                return 1

        # If we get here, the command wasn't recognized
        print("\n❌ Unknown command. Use --help for usage information.")
        return 1

    except Exception as e:
        logger.error(f"Error in async CLI command: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        return 1