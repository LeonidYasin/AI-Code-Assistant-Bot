"""
Project-related command handlers.

This module contains handlers for project-related commands such as
creating, listing, and switching between projects.
"""
import logging
from typing import Dict, Any, Tuple, Optional

from ..response_parser import ResponseParser
from .base import CommandHandler

logger = logging.getLogger(__name__)

class ProjectCommandHandler(CommandHandler):
    """Handler for project-related commands."""
    
    async def handle(
        self, 
        command_data: Dict[str, Any], 
        context: 'CommandContext'
    ) -> Tuple[bool, str]:
        """Handle a project-related command."""
        command_type = command_data.get('type')
        
        try:
            if command_type == 'create_project':
                return await self._handle_create_project(command_data, context)
            elif command_type == 'list_projects':
                return await self._handle_list_projects(command_data, context)
            elif command_type == 'switch_project':
                return await self._handle_switch_project(command_data, context)
            else:
                return False, f"❌ Unknown project command: {command_type}"
        except Exception as e:
            logger.error(f"Error handling project command: {str(e)}", exc_info=True)
            return False, f"❌ Error: {str(e)}"
    
    async def _handle_create_project(
        self, 
        command_data: Dict[str, Any], 
        context: 'CommandContext'
    ) -> Tuple[bool, str]:
        """Handle project creation."""
        self._validate_command_type(command_data, 'create_project')
        params = command_data.get('params', {})
        
        # Get required parameter
        project_name = self._get_param(params, 'name')
        
        # Create the project
        try:
            project_path = context.project_manager.create_project(project_name)
            
            # Update active project
            context.bot_data['active_projects'][context.chat_id] = project_name
            
            return True, (
                f"✅ Project '{project_name}' created successfully!\n"
                f"Path: {project_path}\n"
                f"Type `switch {project_name}` to activate this project."
            )
        except Exception as e:
            logger.error(f"Failed to create project: {str(e)}", exc_info=True)
            return False, f"❌ Failed to create project: {str(e)}"
    
    async def _handle_list_projects(
        self, 
        command_data: Dict[str, Any], 
        context: 'CommandContext'
    ) -> Tuple[bool, str]:
        """List all available projects."""
        self._validate_command_type(command_data, 'list_projects')
        
        try:
            success, result = context.project_manager.list_projects()
            
            if not success:
                return False, f"❌ {result}"
                
            projects = result
            if not projects:
                return True, "No projects found. Create one with `/create_project`"
            
            # Format the project list
            project_list = []
            for i, project in enumerate(projects, 1):
                project_name = project.get('name', 'Unknown')
                active = " (active)" if project_name == context.current_project else ""
                project_list.append(f"{i}. {project_name}{active}")
            
            return True, "📋 Projects:\n" + "\n".join(project_list)
            
        except Exception as e:
            logger.error(f"Failed to list projects: {str(e)}", exc_info=True)
            return False, f"❌ Failed to list projects: {str(e)}"
    
    async def _handle_switch_project(
        self, 
        command_data: Dict[str, Any], 
        context: 'CommandContext'
    ) -> Tuple[bool, str]:
        """Switch to a different project."""
        self._validate_command_type(command_data, 'switch_project')
        params = command_data.get('params', {})
        
        # Get project name
        project_name = self._get_param(params, 'name')
        
        try:
            # Verify project exists
            success, projects_result = context.project_manager.list_projects()
            if not success:
                return False, f"❌ {projects_result}"
                
            # Check if project exists in the list
            project_exists = any(p.get('name') == project_name for p in projects_result)
            if not project_exists:
                return False, f"❌ Project '{project_name}' not found"
            
            # Ensure bot_data has active_projects dict
            if 'active_projects' not in context.bot_data:
                context.bot_data['active_projects'] = {}
                
            # Update active project in both places for redundancy
            context.bot_data['active_projects'][context.chat_id] = project_name
            context.current_project = project_name
            
            # Debug output
            logger.debug(f"[DEBUG] Updated active project to: {project_name}")
            logger.debug(f"[DEBUG] Updated bot_data: {context.bot_data}")
            
            # Get project path from the projects directory
            project_path = context.project_manager.projects_dir / project_name
            
            return True, (
                f"✅ Switched to project '{project_name}'\n"
                f"📁 Path: {project_path}\n"
                f"📝 Type `list_files` to view project files."
            )
            
        except Exception as e:
            logger.error(f"Failed to switch project: {str(e)}", exc_info=True)
            return False, f"❌ Failed to switch project: {str(e)}"
