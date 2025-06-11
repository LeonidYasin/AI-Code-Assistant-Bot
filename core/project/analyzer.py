from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
import json
from dataclasses import dataclass, asdict
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class FileAnalysis:
    """Represents analysis results for a single file."""
    path: str
    size: int
    lines: int
    language: str
    imports: List[str]
    functions: List[Dict]
    classes: List[Dict]
    issues: List[Dict]

class ProjectAnalyzer:
    """Analyzes project structure and code quality."""
    
    def __init__(self, project_root: Union[str, Path]):
        """Initialize with project root directory."""
        self.project_root = Path(project_root).resolve()
        self.allowed_extensions = {'.py', '.md', '.txt', '.json', '.yaml', '.yml'}
        self.ignore_dirs = {'__pycache__', 'venv', '.git', '.idea', 'node_modules'}
    
    def analyze_project(self) -> Dict:
        """Analyze the entire project structure and contents."""
        try:
            files_analysis = self._analyze_files()
            stats = self._calculate_stats()
            structure = self._get_project_structure()
            
            # Generate project summary and recommendations
            summary = self._generate_project_summary(stats, files_analysis, structure)
            
            return {
                'project_root': str(self.project_root),
                'files': files_analysis,
                'stats': stats,
                'structure': structure,
                'summary': summary
            }
        except Exception as e:
            logger.error(f"Project analysis failed: {e}", exc_info=True)
            return {'error': str(e)}
    
    def _analyze_files(self) -> List[Dict]:
        """Analyze all files in the project."""
        results = []
        for file_path in self._iter_project_files():
            try:
                analysis = self._analyze_file(file_path)
                if analysis:
                    results.append(asdict(analysis))
            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")
        return results
    
    def _analyze_file(self, file_path: Path) -> Optional[FileAnalysis]:
        """Analyze a single file."""
        if not file_path.is_file():
            return None
            
        try:
            content = file_path.read_text(encoding='utf-8')
            rel_path = str(file_path.relative_to(self.project_root))
            
            return FileAnalysis(
                path=rel_path,
                size=file_path.stat().st_size,
                lines=len(content.splitlines()),
                language=self._detect_language(file_path),
                imports=self._extract_imports(content, file_path.suffix),
                functions=[],  # TODO: Implement function extraction
                classes=[],    # TODO: Implement class extraction
                issues=[]      # TODO: Implement issue detection
            )
        except Exception as e:
            logger.warning(f"Error analyzing {file_path}: {e}")
            return None
    
    def _iter_project_files(self):
        """Iterate over all relevant files in the project."""
        for file_path in self.project_root.rglob('*'):
            # Skip ignored directories
            if file_path.is_dir() and file_path.name in self.ignore_dirs:
                continue
                
            if file_path.is_file() and file_path.suffix.lower() in self.allowed_extensions:
                yield file_path
    
    def _calculate_stats(self) -> Dict:
        """Calculate project statistics."""
        stats = {
            'total_files': 0,
            'total_size': 0,  # in bytes
            'total_lines': 0,
            'dir_count': 0,
            'by_extension': {},
            'file_types': {}
        }
        
        # First count all directories
        for item in self.project_root.rglob('*'):
            if item.is_dir() and item.name not in self.ignore_dirs:
                stats['dir_count'] += 1
        
        # Then process files
        for file_path in self._iter_project_files():
            try:
                # Get file size
                file_size = file_path.stat().st_size
                stats['total_size'] += file_size
                
                # Count by extension
                ext = file_path.suffix.lower()
                stats['by_extension'][ext] = stats['by_extension'].get(ext, 0) + 1
                
                # Count lines if it's a text file
                if file_path.suffix.lower() in {'.py', '.md', '.txt', '.json', '.yaml', '.yml', '.html', '.css', '.js'}:
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        stats['total_lines'] += len(content.splitlines())
                    except (UnicodeDecodeError, PermissionError) as e:
                        logger.debug(f"Could not read {file_path} for line counting: {e}")
                
                stats['total_files'] += 1
                
                # Categorize by file type
                file_type = self._detect_file_type(file_path)
                if file_type not in stats['file_types']:
                    stats['file_types'][file_type] = 0
                stats['file_types'][file_type] += 1
                
            except Exception as e:
                logger.warning(f"Error processing {file_path}: {e}", exc_info=True)
        
        return stats
    
    def _get_project_structure(self, max_depth: int = 3) -> Dict:
        """Generate a tree-like structure of the project."""
        def build_tree(path: Path, depth: int = 0) -> Dict:
            if depth > max_depth:
                return {'name': path.name, 'type': '...'}
                
            if path.is_file():
                return {'name': path.name, 'type': 'file'}
                
            return {
                'name': path.name,
                'type': 'directory',
                'children': [
                    build_tree(child, depth + 1)
                    for child in sorted(path.iterdir())
                    if child.name not in self.ignore_dirs
                ]
            }
        
        return build_tree(self.project_root)
    
    @staticmethod
    def _detect_language(file_path: Path) -> str:
        """Detect programming/markup language from file extension."""
        ext = file_path.suffix.lower()
        return {
            '.py': 'python',
            '.js': 'javascript',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.txt': 'text'
        }.get(ext, 'unknown')
    
    @staticmethod
    def _detect_file_type(file_path: Path) -> str:
        """Detect file type category."""
        ext = file_path.suffix.lower()
        if ext in ['.py']:
            return 'Python Source'
        elif ext in ['.json', '.yaml', '.yml']:
            return 'Configuration'
        elif ext in ['.md', '.txt', '.rst']:
            return 'Documentation'
        elif ext in ['.html', '.css', '.js', '.ts']:
            return 'Web'
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg']:
            return 'Image'
        elif ext in ['.ipynb']:
            return 'Jupyter Notebook'
        return 'Other'
    
    @staticmethod
    def _extract_imports(content: str, file_extension: str) -> List[str]:
        """Extract imports from file content based on file type."""
        imports = []
        if file_extension == '.py':
            # Match both import and from ... import statements
            patterns = [
                r'^\s*import\s+([a-zA-Z0-9_,\s]+)',
                r'^\s*from\s+([a-zA-Z0-9_.]+)\s+import',
                r'^\s*import\s+([a-zA-Z0-9_.]+)\s+as',
                r'^\s*from\s+([a-zA-Z0-9_.]+)\s+import\s+\*'
            ]
            for line in content.split('\n'):
                for pattern in patterns:
                    match = re.search(pattern, line)
                    if match:
                        imports.extend([i.strip() for i in match.group(1).split(',')])
        return imports
        
    def _analyze_project_health(self, stats: Dict, files_analysis: List[Dict]) -> Dict:
        """Analyze project health based on various metrics."""
        health = {
            'has_tests': False,
            'has_docs': False,
            'has_requirements': False,
            'has_license': False,
            'has_readme': False,
            'has_gitignore': False,
            'has_setup': False,
            'test_coverage': 'unknown',
            'complexity': 'low',
            'dependencies': set(),
            'main_tech_stack': set()
        }
        
        # Check for common project files
        for file_info in files_analysis:
            file_path = Path(file_info['path'])
            if file_path.name.lower() == 'requirements.txt':
                health['has_requirements'] = True
                # Extract dependencies
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        health['dependencies'].update(line.split('==')[0].strip() for line in f if line.strip() and not line.strip().startswith('#'))
                except Exception as e:
                    logger.debug(f"Could not read requirements: {e}")
            
            if file_path.name.lower() == 'readme.md':
                health['has_readme'] = True
            
            if file_path.name.lower() == 'license':
                health['has_license'] = True
                
            if file_path.name == '.gitignore':
                health['has_gitignore'] = True
                
            if file_path.name.lower() in ('setup.py', 'pyproject.toml'):
                health['has_setup'] = True
                
            if 'test' in file_path.parts or file_path.name.startswith('test_'):
                health['has_tests'] = True
                
            # Detect main technologies
            if file_path.suffix == '.py':
                health['main_tech_stack'].add('Python')
                if 'django' in str(file_path).lower():
                    health['main_tech_stack'].add('Django')
                elif 'flask' in str(file_path).lower():
                    health['main_tech_stack'].add('Flask')
            elif file_path.suffix == '.js':
                health['main_tech_stack'].add('JavaScript')
                if 'react' in str(file_path).lower():
                    health['main_tech_stack'].add('React')
                elif 'vue' in str(file_path).lower():
                    health['main_tech_stack'].add('Vue')
        
        # Convert sets to lists for JSON serialization
        health['dependencies'] = list(health['dependencies'])
        health['main_tech_stack'] = list(health['main_tech_stack'])
        
        return health
    
    def _generate_project_summary(self, stats: Dict, files_analysis: List[Dict], structure: Dict) -> Dict:
        """Generate a summary of the project with AI recommendations."""
        health = self._analyze_project_health(stats, files_analysis)
        
        # Basic project info
        project_name = self.project_root.name
        created_date = datetime.fromtimestamp(self.project_root.stat().st_ctime).strftime('%Y-%m-%d')
        modified_date = datetime.fromtimestamp(self.project_root.stat().st_mtime).strftime('%Y-%m-%d')
        
        # Analyze project type
        project_type = self._detect_project_type(health, stats, files_analysis)
        
        # Generate maturity assessment
        maturity = self._assess_project_maturity(health, stats)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(health, stats, project_type)
        
        return {
            'project_name': project_name,
            'project_type': project_type,
            'created_date': created_date,
            'modified_date': modified_date,
            'maturity': maturity,
            'health': health,
            'recommendations': recommendations
        }
    
    def _detect_project_type(self, health: Dict, stats: Dict, files_analysis: List[Dict]) -> str:
        """Detect the type of project based on its structure and files."""
        if not files_analysis:
            return 'Empty Project'
            
        # Get all file types, safely handling missing 'type' key
        file_types = set()
        python_file_count = 0
        
        for f in files_analysis:
            # Check for Python files
            if f.get('path', '').endswith('.py'):
                python_file_count += 1
                file_types.add('Python Source')
            # Check for other file types
            elif f.get('path', '').endswith(('.ipynb', 'notebooks/')):
                return 'Data Science / Jupyter Notebooks'
            elif 'templates/' in f.get('path', ''):
                return 'Web Application'
            elif f.get('path', '').endswith(('.js', '.ts')):
                return 'JavaScript/TypeScript Application'
        
        # Make determination based on file types and counts
        if python_file_count > 5:
            return 'Python Package/Application'
        elif python_file_count > 0:
            return 'Small Python Script'
            
        # Default fallback
        return 'General Project'
    
    def _assess_project_maturity(self, health: Dict, stats: Dict) -> Dict:
        """Assess the maturity level of the project."""
        score = 0
        max_score = 10
        
        # Basic project structure
        if health['has_readme']: score += 1
        if health['has_requirements']: score += 1
        if health['has_license']: score += 1
        if health['has_tests']: score += 2
        if health['has_setup']: score += 1
        if health['has_gitignore']: score += 1
        
        # Code metrics
        if stats.get('total_lines', 0) > 1000: score += 1
        if stats.get('total_files', 0) > 10: score += 1
        if stats.get('dir_count', 0) > 2: score += 1
        
        # Maturity level
        if score >= 8:
            level = 'High'
            description = 'Well-structured project with good documentation and testing'
        elif score >= 5:
            level = 'Medium'
            description = 'Basic project structure with some documentation'
        else:
            level = 'Low'
            description = 'Early stage or minimal project setup'
            
        return {
            'score': score,
            'max_score': max_score,
            'level': level,
            'description': description
        }
    
    def _generate_recommendations(self, health: Dict, stats: Dict, project_type: str) -> List[str]:
        """Generate AI-powered recommendations for project improvement."""
        recommendations = []
        
        # Basic recommendations
        if not health['has_readme']:
            recommendations.append("Создайте файл README.md с описанием проекта, установкой и использованием")
            
        if not health['has_requirements'] and project_type in ['Python Package/Application', 'Data Science / Jupyter Notebooks']:
            recommendations.append("Создайте файл requirements.txt с зависимостями проекта")
            
        if not health['has_license']:
            recommendations.append("Добавьте файл LICENSE с лицензией проекта")
            
        if not health['has_tests']:
            recommendations.append("Добавьте тесты для улучшения качества кода")
            
        if not health['has_gitignore']:
            recommendations.append("Добавьте .gitignore файл для игнорирования временных файлов")
        
        # Project type specific recommendations
        if project_type == 'Python Package/Application' and not health['has_setup']:
            recommendations.append("Добавьте setup.py или pyproject.toml для упрощения установки")
            
        if project_type == 'Web Application':
            if 'Dockerfile' not in [f['path'] for f in health.get('files', [])]:
                recommendations.append("Рассмотрите возможность добавления Dockerfile для контейнеризации приложения")
        
        # AI-specific recommendations
        if any(lib in health.get('dependencies', []) for lib in ['tensorflow', 'pytorch', 'transformers']):
            recommendations.extend([
                "Для ML-проекта рассмотрите добавление: документации по архитектуре модели, примеров инференса, метрик качества",
                "Добавьте скрипты для воспроизведения обучения моделей и оценки качества"
            ])
        
        # Performance recommendations for large projects
        if stats.get('total_lines', 0) > 5000:
            recommendations.append("Для большого проекта рассмотрите рефакторинг на модули/пакеты для лучшей поддерживаемости")
        
        return recommendations

def analyze_project(project_root: Union[str, Path]) -> Dict:
    analyzer = ProjectAnalyzer(project_root)
    return analyzer.analyze_project()

# Example usage:
if __name__ == "__main__":
    # Use current directory when run directly
    project_root = Path.cwd()
    result = analyze_project(project_root)
    print(json.dumps(result, indent=4, ensure_ascii=False))