import os
import sys
import unittest
import asyncio
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from core.project.manager import ProjectManager
from core.nlp.command_processor import NLPCommandProcessor
from core.nlp.handlers.file_handlers import FileCommandHandler
from core.nlp.handlers.project_handlers import ProjectCommandHandler
from core.commands.dispatcher import CommandDispatcher

class TestDirectCommands(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Create a temporary directory for tests
        self.test_dir = Path("test_projects")
        self.test_dir.mkdir(exist_ok=True)
        
        # Initialize project manager
        self.project_manager = ProjectManager(base_path=str(self.test_dir.absolute()))
        
        # Initialize command handlers
        self.file_handler = FileCommandHandler()
        self.project_handler = ProjectCommandHandler()
        
        # Create test context
        self.context = MagicMock()
        self.context.project_manager = self.project_manager
        self.context.chat_id = "test_chat"
        self.context.bot_data = {
            'active_projects': {},
            'project_manager': self.project_manager
        }
    
    async def test_create_project_direct(self):
        """Test direct project creation"""
        project_name = "test_direct_project"
        
        # Create project
        success, result = await self.project_handler._handle_create_project(
            {'type': 'create_project', 'params': {'name': project_name}}, 
            self.context
        )
        
        self.assertTrue(success)
        self.assertIn(project_name, result)
        
        # Verify project directory exists
        project_path = self.test_dir / "projects" / project_name
        self.assertTrue(project_path.exists() and project_path.is_dir())
    
    async def test_switch_project_direct(self):
        """Test direct project switching"""
        project_name = "test_switch_project"
        
        # First create a project
        await self.project_handler._handle_create_project(
            {'type': 'create_project', 'params': {'name': project_name}}, 
            self.context
        )
        
        # Switch to the project
        success, result = await self.project_handler._handle_switch_project(
            {'type': 'switch_project', 'params': {'name': project_name}}, 
            self.context
        )
        
        self.assertTrue(success)
        self.assertIn(project_name, result)
        self.assertEqual(self.project_manager.current_project, project_name)
    
    async def test_create_file_direct(self):
        """Test direct file creation"""
        project_name = "test_file_project"
        file_name = "test_file.txt"
        file_content = "Test content"
        
        # Create a project and switch to it
        await self.project_handler._handle_create_project(
            {'type': 'create_project', 'params': {'name': project_name}}, 
            self.context
        )
        await self.project_handler._handle_switch_project(
            {'type': 'switch_project', 'params': {'name': project_name}}, 
            self.context
        )
        
        # Create a file
        success, result = await self.file_handler._handle_create_file(
            {
                'type': 'create_file', 
                'params': {
                    'path': file_name,
                    'content': file_content
                }
            },
            self.context
        )
        
        self.assertTrue(success)
        
        # Verify file exists and has correct content
        file_path = self.test_dir / "projects" / project_name / file_name
        self.assertTrue(file_path.exists())
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, file_content)
    
    def tearDown(self):
        # Clean up test directory
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

if __name__ == "__main__":
    unittest.main()
