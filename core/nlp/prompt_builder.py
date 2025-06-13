"""
Prompt construction for natural language processing.

This module handles the construction of prompts for the LLM
based on user input and current context.
"""
import json
from typing import Dict, Any, Optional, List
from dataclasses import asdict

class PromptBuilder:
    """Builds prompts for LLM-based command processing."""
    
    def __init__(self):
        self.system_prompt = self._create_system_prompt()
    
    def build(self, user_input: str, current_project: str = None) -> str:
        """Build a complete prompt for the LLM.
        
        Args:
            user_input: The user's natural language input
            current_project: The currently active project (if any)
            
        Returns:
            Formatted prompt string
        """
        # Prepare context information
        context = {
            'current_project': current_project,
            'available_commands': self._get_available_commands()
        }
        
        # Format the prompt
        prompt_parts = [
            self.system_prompt,
            "\n## Context",
            json.dumps(context, indent=2, ensure_ascii=False),
            "\n## User Input",
            user_input,
            "\n## Response (in JSON format):"
        ]
        
        return "\n".join(part for part in prompt_parts if part)
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt that defines the LLM's behavior."""
        return """You are an AI assistant that helps with software development tasks. 
Your role is to understand natural language requests and convert them into 
structured commands that can be executed by the system.

For each user request, you should respond with a JSON object containing:
1. 'type': The type of command to execute
2. 'params': A dictionary of parameters for the command
3. 'confidence': Your confidence in this interpretation (0.0 to 1.0)
4. 'explanation': A brief explanation of your interpretation

Example response:
{
  "type": "create_file",
  "params": {
    "project": "my_project",
    "path": "src/main.py",
    "content": "print('Hello, World!')\n"
  },
  "confidence": 0.95,
  "explanation": "The user wants to create a new Python file with a hello world program."
}"""
    
    def _get_available_commands(self) -> List[Dict[str, Any]]:
        """Get a list of available commands and their parameters."""
        return [
            {
                'name': 'create_project',
                'description': 'Create a new project',
                'params': ['name', 'template']
            },
            {
                'name': 'list_projects',
                'description': 'List all available projects',
                'params': []
            },
            {
                'name': 'switch_project',
                'description': 'Switch to a different project',
                'params': ['name']
            },
            {
                'name': 'create_file',
                'description': 'Create a new file',
                'params': ['path', 'content', 'project']
            },
            {
                'name': 'list_files',
                'description': 'List files in a directory',
                'params': ['path', 'project']
            },
            {
                'name': 'view_file',
                'description': 'View the contents of a file',
                'params': ['path', 'project']
            },
            {
                'name': 'run_code',
                'description': 'Execute code',
                'params': ['code', 'language', 'project']
            },
            {
                'name': 'analyze_code',
                'description': 'Analyze code for issues',
                'params': ['code', 'language']
            },
            {
                'name': 'analyze_project',
                'description': 'Analyze an entire project',
                'params': ['project']
            }
        ]
