"""
Code execution and analysis command handlers.

This module contains handlers for code execution and analysis commands.
"""
from pathlib import Path
import logging
import asyncio
from typing import Dict, Any, Tuple, Optional, List

from ..response_parser import ResponseParser
from .base import CommandHandler

logger = logging.getLogger(__name__)

class CodeCommandHandler(CommandHandler):
    """Handler for code execution and analysis commands."""
    
    def __init__(self):
        self.max_output_length = 2000  # Maximum length of command output to show
    
    async def handle(
        self, 
        command_data: Dict[str, Any], 
        context: 'CommandContext'
    ) -> Tuple[bool, str]:
        """Handle a code-related command."""
        command_type = command_data.get('type')
        
        try:
            if command_type == 'run_code':
                return await self._handle_run_code(command_data, context)
            elif command_type == 'analyze_code':
                return await self._handle_analyze_code(command_data, context)
            elif command_type == 'analyze_project':
                return await self._handle_analyze_project(command_data, context)
            else:
                return False, f"❌ Unknown code command: {command_type}"
        except Exception as e:
            logger.error(f"Error handling code command: {str(e)}", exc_info=True)
            return False, f"❌ Error: {str(e)}"
    
    async def _handle_run_code(
        self, 
        command_data: Dict[str, Any], 
        context: 'CommandContext'
    ) -> Tuple[bool, str]:
        """Handle code execution."""
        self._validate_command_type(command_data, 'run_code')
        params = command_data.get('params', {})
        
        # Get required parameters
        code = self._get_param(params, 'code')
        language = params.get('language', 'python')
        project_name = params.get('project', context.current_project)
        
        if not project_name:
            return False, (
                "❌ No active project. Please specify a project or switch to one.\n"
                "Example: `run_code --code 'print(\"Hello\")' --language python --project myproject`"
            )
        
        try:
            # Get the project path
            project_path = context.project_manager.get_project_path(project_name)
            if not project_path or not project_path.exists():
                return False, f"❌ Project '{project_name}' not found or invalid path: {project_path}"
            
            # Create a temporary file with the code
            import tempfile
            import os
            
            file_ext = {
                'python': '.py',
                'javascript': '.js',
                'bash': '.sh',
                'shell': '.sh'
            }.get(language.lower(), '.txt')
            
            # Create a temporary file in the project directory
            with tempfile.NamedTemporaryFile(
                suffix=file_ext, 
                prefix='temp_code_', 
                dir=str(project_path),
                delete=False
            ) as temp_file:
                temp_file.write(code.encode('utf-8'))
                file_path = Path(temp_file.name)
            
            # Execute the code
            if language.lower() in ['python', 'py']:
                cmd = ["python", str(file_path)]
            elif language.lower() in ['javascript', 'js']:
                cmd = ["node", str(file_path)]
            elif language.lower() in ['bash', 'shell', 'sh']:
                cmd = ["bash", str(file_path)]
            else:
                return False, f"❌ Unsupported language: {language}"
            
            # Run the command and wait for it to complete
            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(project_path)
                )
                
                # Wait for the process to complete
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=30  # 30 second timeout for execution
                    )
                except asyncio.TimeoutError:
                    # If the process times out, terminate it
                    process.terminate()
                    await process.wait()
                    return False, f"❌ Command timed out after 30 seconds"
            except Exception as e:
                return False, f"❌ Failed to execute command: {str(e)}"
            
            # Clean up the temporary file
            try:
                file_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete temporary file: {str(e)}")
            
            # Prepare the output
            output = ""
            if stdout:
                output += f"\n💻 Output:\n{stdout.decode('utf-8', errors='replace')}"
            if stderr:
                output += f"\n❌ Errors:\n{stderr.decode('utf-8', errors='replace')}"
            
            # Truncate long output
            if len(output) > self.max_output_length:
                output = output[:self.max_output_length] + "\n... (output truncated)"
            
            return True, f"✅ Code executed successfully!{output}"
            
        except Exception as e:
            logger.error(f"Failed to execute code: {str(e)}", exc_info=True)
            return False, f"❌ Failed to execute code: {str(e)}"
    
    async def _handle_analyze_code(
        self, 
        command_data: Dict[str, Any], 
        context: 'CommandContext'
    ) -> Tuple[bool, str]:
        """Analyze code for issues."""
        self._validate_command_type(command_data, 'analyze_code')
        params = command_data.get('params', {})
        
        # Get required parameters
        code = self._get_param(params, 'code')
        language = params.get('language', 'python')
        
        try:
            # For now, we'll do a simple analysis
            # In a real implementation, you might want to use tools like:
            # - pylint, flake8 for Python
            # - eslint for JavaScript
            # - shellcheck for shell scripts
            
            issues = []
            
            # Basic code analysis
            if language.lower() in ['python', 'py']:
                # Check for common Python issues
                if 'import *' in code:
                    issues.append({
                        'line': code.find('import *'),
                        'type': 'warning',
                        'message': 'Avoid using "import *" as it pollutes the namespace',
                        'code': 'W001'
                    })
                
                # Check for print statements (in a real app, use AST parsing)
                if 'print(' in code and 'def ' not in code and 'class ' not in code:
                    issues.append({
                        'line': code.find('print(') + 1,
                        'type': 'info',
                        'message': 'Consider using logging instead of print for production code',
                        'code': 'I001'
                    })
            
            # Format the issues
            if not issues:
                return True, "✅ No issues found in the code!"
            
            issue_list = []
            for i, issue in enumerate(issues, 1):
                issue_list.append(
                    f"{i}. [{issue['type'].upper()}] {issue['code']}: {issue['message']}\n"
                    f"   Line: {issue.get('line', 'N/A')}"
                )
            
            return True, (
                f"🔍 Found {len(issues)} potential issue(s) in the code:\n\n" +
                "\n\n".join(issue_list)
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze code: {str(e)}", exc_info=True)
            return False, f"❌ Failed to analyze code: {str(e)}"
    
    async def _handle_analyze_project(
        self, 
        command_data: Dict[str, Any], 
        context: 'CommandContext'
    ) -> Tuple[bool, str]:
        """Analyze an entire project."""
        self._validate_command_type(command_data, 'analyze_project')
        params = command_data.get('params', {})
        
        # Get project name
        project_name = self._get_param(params, 'project', context.current_project)
        
        if not project_name:
            return False, (
                "❌ No active project. Please specify a project or switch to one.\n"
                "Example: `analyze_project --project myproject`"
            )
        
        try:
            # Get the project
            project = await context.project_manager.get_project(project_name)
            if not project:
                return False, f"❌ Project '{project_name}' not found"
            
            # List all files in the project
            files = await project.list_files(recursive=True)
            
            if not files:
                return True, "ℹ️ No files found in the project"
            
            # Basic project analysis
            file_count = len(files)
            total_size = sum(f.get('size', 0) for f in files)
            
            # Count files by extension
            ext_counts = {}
            for file_info in files:
                if not file_info['is_dir']:
                    ext = file_info['name'].split('.')[-1] if '.' in file_info['name'] else 'other'
                    ext_counts[ext] = ext_counts.get(ext, 0) + 1
            
            # Format the analysis
            ext_summary = "\n".join(
                f"  - {ext}: {count} file{'s' if count != 1 else ''}"
                for ext, count in sorted(ext_counts.items(), key=lambda x: -x[1])
            )
            
            return True, (
                f"📊 Project Analysis: {project_name}\n"
                f"📁 Total files: {file_count}\n"
                f"📦 Total size: {self._format_size(total_size)}\n"
                f"\n📂 File types:\n{ext_summary}"
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze project: {str(e)}", exc_info=True)
            return False, f"❌ Failed to analyze project: {str(e)}"
    
    def _format_size(self, size_bytes: int) -> str:
        """Format size in bytes to a human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
