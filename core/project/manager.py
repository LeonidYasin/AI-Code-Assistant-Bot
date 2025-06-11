import os
import subprocess
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Union
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Project configuration file name
PROJECT_CONFIG = ".project.json"

class FileType(Enum):
    FILE = "file"
    DIRECTORY = "directory"
    ANY = "any"

@dataclass
class FileOperation:
    action: str  # 'create', 'read', 'update', 'delete'
    path: str
    content: Optional[str] = None
    file_type: FileType = FileType.FILE

class CommandType(Enum):
    CREATE_FILE = "create_file"
    READ_FILE = "read_file"
    UPDATE_FILE = "update_file"
    DELETE_FILE = "delete_file"
    LIST_FILES = "list_files"
    ANALYZE_CODE = "analyze_code"
    RUN_CODE = "run_code"
    UNKNOWN = "unknown"

class ProjectManager:
    def __init__(self, base_path: str = None):
        """
        Initialize project manager with base directory.
        If no base_path is provided, uses current working directory.
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self._current_project = None  # Always store as string (project name)
        self.projects_dir = self.base_path / "projects"
        self.projects_dir.mkdir(exist_ok=True)
        self._load_config()
        
        # Load current project state if exists
        self._load_current_project()
        
        # Initialize AI client for natural language processing
        try:
            from core.llm.client import llm_client
            self.llm = llm_client
        except ImportError:
            logger.warning("LLM client not available, some features may be limited")
            self.llm = None
            
    @property
    def current_project(self) -> Optional[str]:
        """Get the current project name"""
        return self._current_project
        
    @current_project.setter
    def current_project(self, value: Optional[str]):
        """Set the current project name (string only)"""
        if value is not None and not isinstance(value, str):
            if hasattr(value, 'name'):  # If it's a Path object with name attribute
                value = value.name
            else:
                value = str(value)
        self._current_project = value
        
    def _load_config(self) -> None:
        """Load project configuration"""
        self.config_path = self.base_path / "config.json"
        self.config = {}
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                self.config = {}
    
    def _save_config(self) -> bool:
        """Save project configuration"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
            
    def _get_state_file_path(self) -> Path:
        """Get path to the state file"""
        return self.base_path / ".current_project"
        
    def _save_current_project(self) -> bool:
        """Save current project to state file"""
        try:
            state_file = self._get_state_file_path()
            state = {
                'current_project': self.current_project,
                'timestamp': datetime.now().isoformat()
            }
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving current project: {e}")
            return False
            
    def _load_current_project(self) -> bool:
        """Load current project from state file"""
        try:
            state_file = self._get_state_file_path()
            if not state_file.exists():
                return False
                
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                
            if 'current_project' in state:
                self.current_project = state['current_project']
                logger.info(f"Loaded current project from state: {self.current_project}")
                return True
                
        except Exception as e:
            logger.error(f"Error loading current project: {e}")
            
        return False
            
    def get_project_path(self, project_name: str = None) -> Optional[Path]:
        """
        Get path to project directory
        
        Args:
            project_name: Optional project name. If None, uses current_project
            
        Returns:
            Path object to the project directory or None if no project is selected
        """
        if not project_name and not self.current_project:
            return None
            
        project_name = project_name or self.current_project
        
        # Ensure project_name is a string
        if hasattr(project_name, 'name'):  # If it's a Path object
            project_name = project_name.name
        project_name = str(project_name)
            
        return self.projects_dir / project_name
        
    def validate_path(self, path: Union[str, Path], project_name: str = None) -> Tuple[bool, str]:
        """Validate that path is within project directory"""
        try:
            project_path = self.get_project_path(project_name)
            if not project_path:
                return False, "No project selected"
                
            full_path = (project_path / path).resolve()
            project_path = project_path.resolve()
            
            # Check if path is within project directory
            if project_path not in full_path.parents and full_path != project_path:
                return False, f"Path {path} is outside project directory"
                
            return True, str(full_path)
        except Exception as e:
            return False, f"Invalid path: {str(e)}"
            
    def create_file(self, path: str, content: str = "", project_name: str = None) -> Tuple[bool, str]:
        """Create a new file in the project"""
        try:
            valid, result = self.validate_path(path, project_name)
            if not valid:
                return False, result
                
            file_path = Path(result)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            return True, f"File {path} created successfully"
            
        except Exception as e:
            return False, f"Error creating file: {str(e)}"
            
    def read_file(self, path: str, project_name: str = None) -> Tuple[bool, Union[str, bytes]]:
        """Read file content from project"""
        try:
            valid, result = self.validate_path(path, project_name)
            if not valid:
                return False, result
                
            file_path = Path(result)
            if not file_path.exists():
                return False, f"File {path} does not exist"
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            return True, content
            
        except UnicodeDecodeError:
            # Try reading as binary if text decoding fails
            try:
                with open(file_path, 'rb') as f:
                    return True, f.read()
            except Exception as e:
                return False, f"Error reading binary file: {str(e)}"
        except Exception as e:
            return False, f"Error reading file: {str(e)}"
            
    def list_files(self, path: str = ".", project_name: str = None) -> Tuple[bool, Union[str, List[Dict]]]:
        """List files in project directory"""
        try:
            valid, result = self.validate_path(path, project_name)
            if not valid:
                return False, result
                
            dir_path = Path(result)
            if not dir_path.exists():
                return False, f"Directory {path} does not exist"
                
            files = []
            for item in dir_path.iterdir():
                try:
                    files.append({
                        'name': item.name,
                        'path': str(item.relative_to(dir_path)),
                        'type': 'directory' if item.is_dir() else 'file',
                        'size': item.stat().st_size if item.is_file() else 0,
                        'modified': datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                    })
                except Exception as e:
                    logger.warning(f"Error reading file info for {item}: {e}")
                    
            return True, files
            
        except Exception as e:
            return False, f"Error listing files: {str(e)}"
            
    def analyze_code(self, path: str, project_name: str = None) -> Tuple[bool, str]:
        """Analyze code using AI"""
        if not self.llm:
            return False, "AI analysis is not available"
            
        try:
            # First check if the file exists
            success, content = self.read_file(path, project_name)
            if not success:
                return False, content
                
            # Prepare prompt for code analysis
            prompt = (
                f"Please analyze the following Python code. Provide a detailed report including:\n"
                f"1. Code quality assessment\n"
                f"2. Potential bugs or issues\n"
                f"3. Security vulnerabilities\n"
                f"4. Performance considerations\n"
                f"5. Suggestions for improvement\n\n"
                f"Code to analyze:\n```python\n{content}\n```"
            )
            
            # Get analysis from LLM
            response = self.llm.generate(prompt)
            return True, response
            
        except Exception as e:
            return False, f"Error during code analysis: {str(e)}"
            
    def process_natural_language(self, command: str, project_name: str = None) -> Dict:
        """Process natural language command and return structured operation"""
        if not self.llm:
            return {
                'success': False,
                'error': 'AI processing is not available',
                'type': CommandType.UNKNOWN
            }
            
        try:
            # Prepare prompt for command interpretation
            prompt = (
                f"You are a helpful assistant that understands file operations in a project. "
                f"Analyze the following user command and respond with a JSON object containing:\n"
                f"- 'type': One of {[t.value for t in CommandType]}\n"
                f"- 'path': File or directory path (if applicable)\n"
                f"- 'content': Content for create/update operations (if any)\n"
                f"- 'error': Error message if command is invalid\n\n"
                f"Command: {command}\n\n"
                f"Example responses:\n"
                f'{{"type": "create_file", "path": "src/main.py", "content": "print(\'Hello, World!\')"}}'
                f'{{"type": "list_files", "path": "src"}}'
                f'{{"type": "analyze_code", "path": "src/main.py"}}'
                f'{{"type": "unknown", "error": "Command not understood"}}'
            )
            
            # Get structured command from LLM
            response = self.llm.generate(prompt)
            try:
                result = json.loads(response)
                if 'type' not in result:
                    raise ValueError("Missing 'type' in response")
                return {'success': True, **result}
            except (json.JSONDecodeError, ValueError) as e:
                return {
                    'success': False,
                    'error': f'Invalid response from AI: {str(e)}',
                    'type': CommandType.UNKNOWN
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error processing command: {str(e)}',
                'type': CommandType.UNKNOWN
            }
        
    def create_project(self, project_name: str) -> str:
        """Create a new project directory"""
        try:
            # Sanitize project name
            project_name = "".join(c for c in project_name if c.isalnum() or c in ' _-').strip()
            if not project_name:
                raise ValueError("Invalid project name")
                
            project_path = self.projects_dir / project_name
            project_path.mkdir(parents=True, exist_ok=False)
            
            # Create project config
            project_config = {
                'name': project_name,
                'created_at': str(datetime.now().isoformat()),
                'files': []
            }
            
            with open(project_path / PROJECT_CONFIG, 'w', encoding='utf-8') as f:
                json.dump(project_config, f, ensure_ascii=False, indent=2)
            
            return str(project_path)
            
        except FileExistsError:
            raise ValueError(f"Project '{project_name}' already exists")
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            raise Exception(f"Failed to create project: {str(e)}")
    
    def switch_project(self, project_name: str) -> bool:
        """
        Switch to an existing project and save the state
        
        Args:
            project_name: Name of the project to switch to
            
        Returns:
            bool: True if switch was successful, False otherwise
        """
        project_path = self.projects_dir / project_name
        if not project_path.exists() or not (project_path / PROJECT_CONFIG).exists():
            logger.error(f"Project {project_name} does not exist or is not a valid project")
            return False
            
        try:
            self.current_project = project_name
            self.config['current_project'] = project_name
            
            # Save to config file
            if not self._save_config():
                logger.warning("Failed to save project config")
            
            # Save to state file
            if not self._save_current_project():
                logger.warning("Failed to save project state")
                
            logger.info(f"Switched to project: {project_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error switching to project {project_name}: {e}")
            return False
        
    def list_projects(self) -> Tuple[bool, Union[str, List[Dict[str, Any]]]]:
        """List all available projects with detailed information
        
        Returns:
            Tuple[bool, Union[str, List[Dict]]]: A tuple containing:
                - bool: Success status (True if successful, False if error)
                - Union[str, List[Dict]]: Error message if failed, or list of projects if successful
        """
        try:
            projects = []
            logger.debug(f"Looking for projects in: {self.projects_dir}")
            
            if not self.projects_dir.exists():
                logger.debug(f"Creating projects directory: {self.projects_dir}")
                self.projects_dir.mkdir(parents=True, exist_ok=True)
                return True, projects
                
            for item in self.projects_dir.iterdir():
                if item.is_dir() and (item / PROJECT_CONFIG).exists():
                    logger.debug(f"Found project directory with config: {item}")
                    try:
                        config_path = item / PROJECT_CONFIG
                        
                        # Get project config
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        
                        # Calculate directory size
                        total_size = sum(f.stat().st_size for f in item.glob('**/*') if f.is_file())
                        
                        # Count files
                        file_count = sum(1 for _ in item.glob('**/*') if _.is_file() and _.name != PROJECT_CONFIG)
                        
                        project_data = {
                            'name': item.name,
                            'path': str(item.absolute()),
                            'created_at': config.get('created_at', 'Unknown'),
                            'size': self._format_size(total_size),
                            'file_count': file_count,
                            'is_current': self.current_project and str(self.current_project.absolute()) == str(item.absolute())
                        }
                        projects.append(project_data)
                        
                    except Exception as e:
                        error_msg = f"Error reading project {item.name}: {str(e)}"
                        logger.error(error_msg, exc_info=True)
                        projects.append({
                            'name': item.name,
                            'path': str(item.absolute()),
                            'error': str(e)
                        })
            
            # Sort projects by name
            return True, sorted(projects, key=lambda x: x['name'])
            
        except Exception as e:
            error_msg = f"Error listing projects: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
        
    def _format_size(self, size_bytes: int) -> str:
        """Convert size in bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0 or unit == 'GB':
                break
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} {unit}"
        
    def get_project_info(self) -> Dict[str, Any]:
        """Get information about the current project"""
        if not self.current_project or not self.current_project.exists():
            return {}
            
        try:
            with open(self.current_project / PROJECT_CONFIG, 'r', encoding='utf-8') as f:
                project_config = json.load(f)
                
            # Count files in project
            file_count = sum(1 for _ in self.current_project.rglob('*') if _.is_file() and _.name != PROJECT_CONFIG)
            
            return {
                'name': project_config.get('name', 'Unnamed Project'),
                'path': str(self.current_project),
                'created_at': project_config.get('created_at', 'Unknown'),
                'file_count': file_count,
                'current_project': self.current_project.name
            }
            
        except Exception as e:
            logger.error(f"Error getting project info: {e}")
            return {'error': str(e)}
    
    def list_files(self, path: str = '.') -> List[Dict]:
        """List all files in the current project or specified path"""
        if not self.current_project:
            return []
            
        try:
            target_path = (self.current_project / path).resolve()
            
            # Security check: prevent directory traversal
            if not target_path.is_relative_to(self.current_project):
                raise ValueError("Access denied: path outside project directory")
                
            files = []
            for item in target_path.iterdir():
                try:
                    rel_path = item.relative_to(self.current_project)
                    files.append({
                        'name': item.name,
                        'path': str(rel_path),
                        'size': item.stat().st_size,
                        'modified': item.stat().st_mtime,
                        'is_dir': item.is_dir(),
                        'is_file': item.is_file()
                    })
                except Exception as e:
                    logger.warning(f"Error processing {item}: {e}")
                    
            return sorted(files, key=lambda x: (not x['is_dir'], x['name']))
            
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            raise
    
    def read_file(self, file_path: str) -> Tuple[bool, str]:
        """Read file content"""
        try:
            full_path = self._get_absolute_path(file_path)
            if not full_path.exists():
                return False, f"File not found: {file_path}"
                
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return True, content
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return False, f"Failed to read file: {str(e)}"
    
    def write_file(self, file_path: str, content: str, overwrite: bool = False) -> Tuple[bool, str]:
        """Create or update a file"""
        try:
            full_path = self._get_absolute_path(file_path)
            
            if full_path.exists() and not overwrite:
                return False, f"File already exists: {file_path}. Use overwrite=True to replace it."
                
            # Create parent directories if they don't exist
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            return True, f"File saved: {file_path}"
            
        except Exception as e:
            logger.error(f"Error writing to {file_path}: {e}")
            return False, f"Failed to write file: {str(e)}"
    
    def execute_script(self, file_path: str) -> Tuple[bool, str, str]:
        """Execute a Python script and return output"""
        try:
            full_path = self._get_absolute_path(file_path)
            if not full_path.exists():
                return False, "", f"File not found: {file_path}"
                
            result = subprocess.run(
                ['python', str(full_path)],
                capture_output=True,
                text=True,
                cwd=str(full_path.parent)
            )
            
            if result.returncode == 0:
                return True, result.stdout, result.stderr
            else:
                return False, result.stdout, result.stderr
                
        except Exception as e:
            error_msg = f"Failed to execute script: {str(e)}"
            logger.error(error_msg)
            return False, "", error_msg
    
    def _get_absolute_path(self, relative_path: str) -> Path:
        """Convert relative path to absolute path within project"""
        if not self.current_project:
            raise ValueError("No project selected")
            
        # Prevent directory traversal attacks
        abs_path = (self.current_project / relative_path).resolve()
        if not abs_path.is_relative_to(self.current_project):
            raise ValueError("Invalid path: outside project directory")
            
        return abs_path
