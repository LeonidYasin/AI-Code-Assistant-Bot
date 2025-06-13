#!/usr/bin/env python3
"""
Command Line Interface for AI Code Assistant
"""
import os
import sys
import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Union

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = str(Path(__file__).parent.absolute())
sys.path.insert(0, project_root)

from core.project.manager import ProjectManager
from core.nlp.command_processor import NLPCommandProcessor, CommandContext

def print_help() -> None:
    """Print help information."""
    print("""
AI Code Assistant - CLI

Project Commands:
  list                     List all projects
  create <name>            Create a new project
  switch <name>            Switch to a project
  info                     Show current project info
  analyze                  Analyze current project
  help                     Show this help message
""")

async def process_natural_language(query: str, project_manager: ProjectManager) -> int:
    """Process a natural language command.
    
    Args:
        query: The natural language query
        project_manager: The project manager instance
        
    Returns:
        int: Exit code
    """
    try:
        # Initialize NLP processor
        processor = NLPCommandProcessor()
        
        # Create command context
        current_project = project_manager.current_project
        context = CommandContext(
            chat_id="cli",
            user_id="cli_user",
            bot_data={},
            project_manager=project_manager,
            current_project=current_project
        )
        
        # Process the command
        success, response = await processor.process_command(
            text=query,
            context={"chat_id": "cli"},
            chat_id="cli",
            user_id="cli_user"
        )
        
        # Print response with UTF-8 encoding to handle Unicode characters
        try:
            print(response)
        except UnicodeEncodeError:
            # If we can't print with default encoding, try UTF-8
            import sys
            sys.stdout.buffer.write(response.encode('utf-8') + b'\n')
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"Error processing natural language command: {e}", exc_info=True)
        print(f"Error: {str(e)}")
        return 1

def main() -> int:
    """Main CLI entry point."""
    # Initialize project manager
    base_path = Path.cwd()
    project_manager = ProjectManager(base_path=base_path, llm_enabled=True)
    
    # Get command from command line
    if len(sys.argv) < 2:
        print("Error: No command provided")
        print_help()
        return 1
    
    # If the first argument is not a known command, treat it as natural language
    command = sys.argv[1].lower()
    
    # Check if this is a natural language command (not a known command)
    known_commands = ["list", "create", "switch", "info", "analyze", "help"]
    if command not in known_commands:
        # Join all arguments as a single natural language query
        query = " ".join(sys.argv[1:])
        return asyncio.run(process_natural_language(query, project_manager))
    args = sys.argv[2:]
    
    try:
        if command == "list":
            success, result = project_manager.list_projects()
            if success:
                print("\nProjects:")
                for i, project in enumerate(result, 1):
                    status = "*" if project.get('has_config', False) else " "
                    print(f"{i:2}. [{status}] {project['name']} - {project['path']}")
                return 0
            else:
                print(f"Error: {result}", file=sys.stderr)
                return 1
                
        elif command == "create" and args:
            project_name = args[0]
            success, result = project_manager.create_project(project_name)
            if success:
                print(f"Project '{project_name}' created successfully at {result}")
                return 0
            else:
                print(f"Error: {result}", file=sys.stderr)
                return 1
                
        elif command == "switch" and args:
            project_name = args[0]
            success = project_manager.switch_project(project_name)
            if success:
                print(f"Switched to project: {project_name}")
                return 0
            else:
                print(f"Error: Could not switch to project '{project_name}'", file=sys.stderr)
                return 1
                
        elif command == "info":
            if not project_manager.current_project:
                print("No project selected")
                return 1
                
            result = project_manager.get_project_info()
            if 'error' in result:
                print(f"Error: {result['error']}", file=sys.stderr)
                return 1
                
            print("\nProject Information:")
            print(f"Name: {result.get('name', 'N/A')}")
            print(f"Path: {result.get('path', 'N/A')}")
            print(f"Created: {result.get('created_at', 'N/A')}")
            print(f"Files: {result.get('file_count', 0)} files")
            print(f"Current Project: {result.get('current_project', 'N/A')}")
            return 0
                
        elif command == "analyze":
            if not project_manager.current_project:
                print("Error: No project selected. Use 'switch' to select a project first.", file=sys.stderr)
                return 1
                
            print(f"Analyzing project: {project_manager.current_project}")
            # Add analysis logic here
            return 0
            
        elif command in ("help", "--help", "-h"):
            print_help()
            return 0
            
        else:
            print(f"Error: Unknown command '{command}'", file=sys.stderr)
            print_help()
            return 1
            
    except Exception as e:
        logger.exception("An error occurred:")
        return 1

if __name__ == "__main__":
    sys.exit(main())
