"""
Utility functions for CLI operations.
"""
import sys
from typing import List, Dict, Any

def is_cli_command() -> bool:
    """Check if we're running a CLI command that doesn't need full initialization."""
    if len(sys.argv) < 2:
        return False
    
    # List of commands that should avoid full initialization
    cli_commands = [
        '--help', '-h', 'help',
        '--version', '-v', 'version',
        'list_project', '/list_project',
        'list_projects', '/list_projects',
        'project',
        'file',
        'analyze',
        'chat',
        'run',
        'python',
        'install'
    ]
    
    return any(cmd in ' '.join(sys.argv).lower() for cmd in cli_commands)

def is_simple_project_command() -> bool:
    """Check if the command is a simple project management command that doesn't require LLM."""
    if len(sys.argv) < 2:
        return False
        
    command = sys.argv[1].lower()
    
    # Handle both /list_project and project list formats
    if command == 'project':
        if len(sys.argv) < 3:
            return False
        subcommand = sys.argv[2].lower()
        return subcommand in ['list', 'switch', 'create', 'info']
    elif command == 'file':
        if len(sys.argv) < 3:
            return False
        subcommand = sys.argv[2].lower()
        return subcommand in ['list', 'view', 'create']
    elif command == 'list_project' or command == '/list_project':
        return True
    elif command == 'analyze':
        return False  # analyze требует AI и должна обрабатываться асинхронно
    return False

def format_project_list(projects: List[Dict[str, Any]]) -> str:
    """Format project list for console output."""
    if not projects:
        return "❌ No projects available"
        
    result = ["\n📋 Projects list:"]
    for i, project in enumerate(projects, 1):
        status = '✅' if project.get('has_config', False) else '⚠️'
        config_note = '' if project.get('has_config', False) else ' (no config)'
        result.append(f"{i}. {status} {project['name']}{config_note}")
        result.append(f"   📁 {project['path']}")
    return "\n".join(result)

def is_direct_command(command: str) -> bool:
    """Check if the command is a direct command (starts with /)."""
    return command.startswith('/')

def should_show_help() -> bool:
    """Check if help should be shown based on command line arguments."""
    if len(sys.argv) < 2:
        return True
        
    first_arg = sys.argv[1].lower()
    help_flags = ['--help', '-h', 'help']
    
    return first_arg in help_flags
