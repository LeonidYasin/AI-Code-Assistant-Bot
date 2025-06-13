"""
CLI command handlers for the AI Code Assistant.

This package contains modules for handling command-line interface commands
and interactions with CLI module for handling command-line interface functionality.
"""

from .direct_commands import DirectCommandHandler, get_help_text
from .utils import (
    is_cli_command,
    is_simple_project_command,
    format_project_list,
    is_direct_command,
    should_show_help
)
from .context import CLIContext
from .command_processor import (
    process_cli_command,
    process_async_cli_command,
    process_direct_command
)

__all__ = [
    'DirectCommandHandler',
    'get_help_text',
    'is_cli_command',
    'is_simple_project_command',
    'format_project_list',
    'is_direct_command',
    'should_show_help',
    'CLIContext',
    'process_cli_command',
    'process_async_cli_command',
    'process_direct_command'
]
