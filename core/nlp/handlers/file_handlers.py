"""
File operation command handlers.

This module contains handlers for file-related commands such as
creating, listing, and viewing files.
"""
import logging
import os
from typing import Dict, Any, Tuple, Optional, List

from ..response_parser import ResponseParser
from .base import CommandHandler

logger = logging.getLogger(__name__)

class FileCommandHandler(CommandHandler):
    """Handler for file-related commands."""
    
    async def handle(
        self, 
        command_data: Dict[str, Any], 
        context: 'CommandContext'
    ) -> Tuple[bool, str]:
        """Handle a file-related command."""
        command_type = command_data.get('type')
        
        try:
            if command_type == 'create_file':
                return await self._handle_create_file(command_data, context)
            elif command_type == 'list_files':
                return await self._handle_list_files(command_data, context)
            elif command_type == 'view_file':
                return await self._handle_view_file(command_data, context)
            else:
                return False, f"❌ Unknown file command: {command_type}"
        except Exception as e:
            logger.error(f"Error handling file command: {str(e)}", exc_info=True)
            return False, f"❌ Error: {str(e)}"
    
    async def _handle_create_file(
        self, 
        command_data: Dict[str, Any], 
        context: 'CommandContext'
    ) -> Tuple[bool, str]:
        """Handle file creation."""
        self._validate_command_type(command_data, 'create_file')
        params = command_data.get('params', {})
        
        # Debug output
        logger.debug(f"[DEBUG] File handler params: {params}")
        logger.debug(f"[DEBUG] Context current_project: {getattr(context, 'current_project', 'NOT SET')}")
        logger.debug(f"[DEBUG] Context bot_data: {getattr(context, 'bot_data', 'NOT SET')}")
        
        # Get required parameters
        path = self._get_param(params, 'path')
        content = params.get('content', '')
        project_name = params.get('project')
        
        # Debug: Print full context attributes
        logger.debug(f"[DEBUG] All context attributes: {dir(context)}")
        if hasattr(context, '__dict__'):
            logger.debug(f"[DEBUG] Context __dict__: {context.__dict__}")
            
        # If project not in params, try to get it from context
        if not project_name:
            project_name = getattr(context, 'current_project', None)
            logger.debug(f"[DEBUG] Project from context.current_project: {project_name}")
            
            # Try to get from bot_data if not found in current_project
            if not project_name and hasattr(context, 'bot_data'):
                bot_data = context.bot_data
                logger.debug(f"[DEBUG] bot_data content: {bot_data}")
                if 'active_projects' in bot_data:
                    active_projects = bot_data['active_projects']
                    logger.debug(f"[DEBUG] Active projects: {active_projects}")
                    if hasattr(context, 'chat_id'):
                        project_name = active_projects.get(str(context.chat_id))
                        logger.debug(f"[DEBUG] Project from active_projects: {project_name}")
            
        # If still no project, try to get from project manager
        if not project_name and hasattr(context, 'project_manager'):
            project_name = context.project_manager.current_project
            logger.debug(f"[DEBUG] Got project from project_manager: {project_name}")
        
        # If still no project, try to get from bot_data
        if not project_name and hasattr(context, 'bot_data'):
            logger.debug(f"[DEBUG] bot_data exists, looking for active_projects")
            if 'active_projects' in context.bot_data:
                logger.debug(f"[DEBUG] Found active_projects: {context.bot_data['active_projects']}")
                if hasattr(context, 'chat_id'):
                    chat_id = str(context.chat_id)
                    logger.debug(f"[DEBUG] Looking for chat_id '{chat_id}' in active_projects")
                    project_name = context.bot_data['active_projects'].get(chat_id)
                    logger.debug(f"[DEBUG] Project from bot_data: {project_name}")
        
        logger.debug(f"[DEBUG] Final project_name: {project_name}")
        logger.debug(f"[DEBUG] Context chat_id: {getattr(context, 'chat_id', 'NOT SET')}")
        logger.debug(f"[DEBUG] Context attributes: {dir(context)}")
        
        if not project_name:
            error_msg = (
                "❌ No active project. Please specify a project or switch to one.\n"
                "Example: `create_file path/to/file.txt --content 'Hello' --project myproject`"
            )
            logger.error(error_msg)
            return False, error_msg
        
        try:
            # Check if project exists by checking the projects directory
            project_path = context.project_manager.projects_dir / project_name
            if not project_path.exists():
                return False, f"❌ Project '{project_name}' not found"
            
            # Create the file directly in the project directory
            file_path = project_path / path
            
            # Ensure the directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True, (
                f"✅ File created successfully!\n"
                f"📄 Path: {file_path}\n"
                f"📁 Path: {file_path}\n"
                f"💾 Size: {len(content)} bytes"
            )
            
        except Exception as e:
            logger.error(f"Failed to create file: {str(e)}", exc_info=True)
            return False, f"❌ Failed to create file: {str(e)}"
    
    async def _handle_list_files(
        self, 
        command_data: Dict[str, Any], 
        context: 'CommandContext'
    ) -> Tuple[bool, str]:
        """List files in a directory."""
        self._validate_command_type(command_data, 'list_files')
        params = command_data.get('params', {})
        
        # Get parameters
        path = params.get('path', '.')
        project_name = params.get('project', context.current_project)
        
        if not project_name:
            return False, (
                "❌ No active project. Please specify a project or switch to one.\n"
                "Example: `list_files src/ --project myproject`"
            )
        
        try:
            # Get the project
            project = await context.project_manager.get_project(project_name)
            if not project:
                return False, f"❌ Project '{project_name}' not found"
            
            # List files
            files = await project.list_files(path)
            
            if not files:
                return True, f"No files found in {path}"
            
            # Format the file list
            file_list = []
            for file_info in files:
                file_type = "📁" if file_info['is_dir'] else "📄"
                size = f" ({file_info['size']} bytes)" if not file_info['is_dir'] else ""
                file_list.append(f"{file_type} {file_info['name']}{size}")
            
            return True, (
                f"📁 Contents of {path}:\n" +
                "\n".join(file_list)
            )
            
        except Exception as e:
            logger.error(f"Failed to list files: {str(e)}", exc_info=True)
            return False, f"❌ Failed to list files: {str(e)}"
    
    async def _handle_view_file(
        self, 
        command_data: Dict[str, Any], 
        context: 'CommandContext'
    ) -> Tuple[bool, str]:
        """View file contents."""
        self._validate_command_type(command_data, 'view_file')
        params = command_data.get('params', {})
        
        # Get required parameters
        path = self._get_param(params, 'path')
        project_name = params.get('project', context.current_project)
        
        if not project_name:
            return False, (
                "❌ No active project. Please specify a project or switch to one.\n"
                "Example: `view_file src/main.py --project myproject`"
            )
        
        try:
            # Get the project
            project = await context.project_manager.get_project(project_name)
            if not project:
                return False, f"❌ Project '{project_name}' not found"
            
            # Read the file
            content = await project.read_file(path)
            
            # Truncate large files for display
            max_length = 1000
            truncated = len(content) > max_length
            display_content = content[:max_length] + ("..." if truncated else "")
            
            return True, (
                f"📄 {path}\n"
                f"📏 Size: {len(content)} bytes\n"
                f"🔤 Encoding: utf-8\n"
                "\n```\n"
                f"{display_content}"
                "\n```"
            )
            
        except FileNotFoundError:
            return False, f"❌ File not found: {path}"
        except Exception as e:
            logger.error(f"Failed to view file: {str(e)}", exc_info=True)
            return False, f"❌ Failed to view file: {str(e)}"
