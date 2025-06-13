"""
Direct command handlers for CLI interface.

This module contains handlers for direct CLI commands that don't require
full bot initialization or async/await functionality.
"""

import logging
import os
import sys
from typing import Dict, Any, Tuple, List, Optional
from pathlib import Path

from core.project.manager import ProjectManager

logger = logging.getLogger(__name__)

# Check if running on Windows
IS_WINDOWS = sys.platform == 'win32'

# Text-based alternatives for all platforms to ensure consistent display
EMOJI_LIST = "[i]"
EMOJI_CHECK = "[v]"
EMOJI_WARN = "[!]"
EMOJI_ERROR = "[x]"
EMOJI_INFO = "[i]"
EMOJI_FOLDER = "[dir]"

# Only use emojis if explicitly enabled and not on Windows
if not IS_WINDOWS and os.environ.get('USE_EMOJIS', '').lower() in ('1', 'true', 'yes'):
    EMOJI_LIST = "📋"
    EMOJI_CHECK = "✅"
    EMOJI_WARN = "⚠️"
    EMOJI_ERROR = "❌"
    EMOJI_INFO = "ℹ️"
    EMOJI_FOLDER = "📁"

def format_project_list(projects: List[Dict[str, Any]]) -> str:
    """Format project list for console output.
    
    Args:
        projects: List of project dictionaries
        
    Returns:
        str: Formatted project list as a string
    """
    if not projects:
        return f"{EMOJI_INFO} No projects available"
        
    result = [f"{EMOJI_LIST} Projects list:"]
    for i, project in enumerate(projects, 1):
        status = EMOJI_CHECK if project.get('has_config', False) else EMOJI_WARN
        config_note = '' if project.get('has_config', False) else ' (no config)'
        result.append(f"{i}. {status} {project['name']}{config_note}")
        result.append(f"   {EMOJI_FOLDER} {project['path']}")
    return "\n".join(result)

class DirectCommandHandler:
    """Handler for direct CLI commands."""
    
    def __init__(self, llm_enabled: bool = False):
        """Initialize the command handler.
        
        Args:
            llm_enabled: Whether to enable LLM functionality
        """
        self.project_manager = ProjectManager(llm_enabled=llm_enabled)
    
    def handle_list_projects(self) -> Tuple[bool, str]:
        """Handle the list projects command.
        
        Returns:
            Tuple[bool, str]: Success status and result message
        """
        success, result = self.project_manager.list_projects()
        if success:
            return True, format_project_list(result)
        return False, f"❌ Ошибка при получении списка проектов: {result}"
    
    def handle_project_info(self) -> Tuple[bool, str]:
        """Handle the project info command.
        
        Returns:
            Tuple[bool, str]: Success status and result message
        """
        info = self.project_manager.get_project_info()
        if 'error' in info:
            return False, f"{EMOJI_ERROR} Error: {info['error']}"
            
        result = [f"{EMOJI_INFO} Project information:"]
        result.append(f"Name: {info.get('name', 'Unknown')}")
        result.append(f"Path: {info.get('path', 'Not specified')}")
        result.append(f"Created: {info.get('created_at', 'Unknown')}")
        result.append(f"Files: {info.get('file_count', 0)}")
        
        return True, "\n".join(result)
    
    def handle_switch_project(self, project_name: str) -> Tuple[bool, str]:
        """Handle the switch project command.
        
        Args:
            project_name: Name of the project to switch to
            
        Returns:
            Tuple[bool, str]: Success status and result message
        """
        if not project_name:
            return False, f"{EMOJI_ERROR} Ошибка: Не указано имя проекта"
            
        success = self.project_manager.switch_project(project_name)
        if success:
            return True, f"{EMOJI_CHECK} Switched to project: {project_name}"
        return False, f"{EMOJI_ERROR} Failed to switch to project: {project_name}"
    
    def handle_create_project(self, project_name: str) -> Tuple[bool, str]:
        """Handle the create project command.
        
        Args:
            project_name: Name of the project to create
            
        Returns:
            Tuple[bool, str]: Success status and result message
        """
        if not project_name:
            return False, f"{EMOJI_ERROR} Error: Project name not specified"
            
        success, result = self.project_manager.create_project(project_name)
        if success:
            return True, f"{EMOJI_CHECK} Project created: {result}"
        return False, f"{EMOJI_ERROR} Failed to create project: {result}"


def get_help_text() -> str:
    """Get the help text for the CLI.
    
    Returns:
        str: Comprehensive help text with all available commands
    """
    return """
AI Code Assistant - Command Line Interface

This tool provides a powerful interface for managing and analyzing code projects.

Project Management Commands:
  project list           List all available projects
  project create <name>  Create a new project with the specified name
  project switch <name>  Switch to an existing project
  project info          Show information about the current project
  project analyze       Analyze the current project's structure and code quality

File Operations:
  file list [path]      List files in the current or specified directory
  file create <path>    Create a new file at the specified path
  file edit <path>      Edit an existing file
  file view <path>      View contents of a file

Code Analysis:
  analyze project       Run a full analysis of the current project
  analyze file <path>   Analyze a specific file
  metrics               Show code metrics for the current project

Development Tools:
  run <command>         Execute a shell command in the project directory
  python <script>      Run a Python script in the project context
  install <package>     Install a Python package (adds to requirements.txt)

Help & Information:
  --help, -h           Show this help message
  --version, -v        Show version information
  --docs               Open online documentation

Examples:
  python main.py project create my_new_project
  python main.py project switch my_project
  python main.py file list
  python main.py analyze project
""".strip()
