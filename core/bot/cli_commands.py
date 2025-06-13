"""
CLI commands for the bot application.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional

from telegram import Update
from telegram.ext import CallbackContext

from core.commands.run_code import execute_run_code
from core.project.manager import ProjectManager
from core.llm.client import LLMClient

logger = logging.getLogger(__name__)

async def cli_run_code(args: List[str], update: Update, context: CallbackContext) -> None:
    """
    CLI command to run Python code and analyze its output.
    
    Usage: run_code <python_code>
    """
    # Initialize required components
    project_manager = ProjectManager()
    llm_client = LLMClient()
    
    # Execute the code
    await execute_run_code(update, context, args, project_manager, llm_client)

def register_cli_commands(cli_runner) -> None:
    """Register all CLI commands."""
    cli_runner.register_command(
        cli_runner.CLICommand(
            name="run_code",
            callback=cli_run_code,
            help_text="Run Python code and analyze its output. Usage: run_code <python_code>"
        )
    )
