"""
Команды для анализа кода в проектах.

Этот модуль содержит команды для статического анализа кода,
поиска уязвимостей и других проверок качества кода.
"""
import logging
import ast
import astor
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from ..base import Command, CommandResponse, Context
from .base import ProjectCommand, ProjectCommandParams

logger = logging.getLogger(__name__)

@dataclass
class AnalyzeCodeParams(ProjectCommandParams):
    """Параметры команды анализа кода."""
    file_path: Optional[str] = None
    code: Optional[str] = None
    language: str = "python"
    checks: List[str] = field(default_factory=list)
    max_issues: int = 100

class AnalyzeCodeCommand(ProjectCommand[AnalyzeCodeParams]):
    """
    Команда для статического анализа кода.
    
    Выполняет статический анализ кода на наличие потенциальных проблем,
    уязвимостей и нарушений стиля.
    """
    
    name = "analyze_code"
    description = "Выполняет статический анализ кода"
    
    async def execute(self, params: AnalyzeCodeParams) -> CommandResponse:
        """
        Выполняет анализ кода.
        
        Args:
            params: Параметры команды
            
        Returns:
            CommandResponse: Результат анализа кода
        """
        try:
            if params.code:
                # Анализируем переданный код
                return await self._analyze_code_content(
                    code=params.code,
                    language=params.language,
                    checks=params.checks,
                    max_issues=params.max_issues
                )
            elif params.file_path:
                # Анализируем файл
                return await self._analyze_code_file(
                    file_path=params.file_path,
                    language=params.language,
                    checks=params.checks,
                    max_issues=params.max_issues
                )
            else:
                return CommandResponse(
                    success=False,
                    message="Either 'code' or 'file_path' must be provided",
                    data={'error': 'missing_parameter'}
                )
                
        except Exception as e:
            logger.error(f"Failed to analyze code: {str(e)}", exc_info=True)
            return CommandResponse(
                success=False,
                message=f"Failed to analyze code: {str(e)}",
                data={
                    'error': 'analysis_failed',
                    'details': str(e)
                }
            )
    
    async def _analyze_code_content(
        self,
        code: str,
        language: str = "python",
        checks: Optional[List[str]] = None,
        max_issues: int = 100
    ) -> CommandResponse:
        """
        Анализирует переданный код.
        
        Args:
            code: Исходный код для анализа
            language: Язык программирования
            checks: Список проверок для выполнения
            max_issues: Максимальное количество проблем для возврата
            
        Returns:
            CommandResponse: Результат анализа
        """
        try:
            if language.lower() == "python":
                return await self._analyze_python_code(
                    code=code,
                    checks=checks,
                    max_issues=max_issues
                )
            else:
                return CommandResponse(
                    success=False,
                    message=f"Unsupported language: {language}",
                    data={'error': 'unsupported_language'}
                )
                
        except Exception as e:
            logger.error(f"Failed to analyze code content: {str(e)}", exc_info=True)
            raise
    
    async def _analyze_code_file(
        self,
        file_path: str,
        language: str = "python",
        checks: Optional[List[str]] = None,
        max_issues: int = 100
    ) -> CommandResponse:
        """
        Анализирует код из файла.
        
        Args:
            file_path: Путь к файлу для анализа
            language: Язык программирования
            checks: Список проверок для выполнения
            max_issues: Максимальное количество проблем для возврата
            
        Returns:
            CommandResponse: Результат анализа
        """
        try:
            # Получаем полный путь к файлу
            path = Path(file_path)
            if not path.is_absolute():
                project_id = self.get_project_id({})
                if project_id:
                    project = await self.project_manager.get_project(project_id)
                    path = project.path / path
            
            # Проверяем существование файла
            if not path.exists() or not path.is_file():
                return CommandResponse(
                    success=False,
                    message=f"File not found: {path}",
                    data={'error': 'file_not_found'}
                )
            
            # Читаем содержимое файла
            with open(path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Определяем язык по расширению, если не указан
            if language == "auto":
                language = self._detect_language(path)
            
            # Анализируем код
            result = await self._analyze_code_content(
                code=code,
                language=language,
                checks=checks,
                max_issues=max_issues
            )
            
            # Добавляем информацию о файле в результат
            if result.data and isinstance(result.data, dict):
                result.data['file_path'] = str(path)
                result.data['language'] = language
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze file {file_path}: {str(e)}", exc_info=True)
            raise
    
    def _detect_language(self, file_path: Path) -> str:
        """
        Определяет язык программирования по расширению файла.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            str: Идентификатор языка программирования
        """
        extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.h': 'cpp',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.m': 'objectivec',
            '.sh': 'bash',
            '.sql': 'sql',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.md': 'markdown',
            '.xml': 'xml'
        }
        
        suffix = file_path.suffix.lower()
        return extensions.get(suffix, 'text')
    
    async def _analyze_python_code(
        self,
        code: str,
        checks: Optional[List[str]] = None,
        max_issues: int = 100
    ) -> CommandResponse:
        """
        Анализирует Python-код.
        
        Args:
            code: Исходный код на Python
            checks: Список проверок для выполнения
            max_issues: Максимальное количество проблем для возврата
            
        Returns:
            CommandResponse: Результат анализа
        """
        issues = []
        
        try:
            # Парсим код в AST
            tree = ast.parse(code)
            
            # Выполняем доступные проверки
            if not checks or 'syntax' in checks:
                issues.extend(self._check_python_syntax(code))
            
            if not checks or 'unused_imports' in checks:
                issues.extend(self._check_unused_imports(tree))
            
            if not checks or 'undefined_vars' in checks:
                issues.extend(self._check_undefined_variables(tree))
            
            # Ограничиваем количество возвращаемых проблем
            issues = issues[:max_issues]
            
            return CommandResponse(
                success=True,
                message=f"Found {len(issues)} issues",
                data={
                    'language': 'python',
                    'issues': issues,
                    'issue_count': len(issues)
                }
            )
            
        except SyntaxError as e:
            return CommandResponse(
                success=False,
                message=f"Syntax error: {str(e)}",
                data={
                    'error': 'syntax_error',
                    'details': {
                        'line': e.lineno,
                        'offset': e.offset,
                        'message': e.msg
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error analyzing Python code: {str(e)}", exc_info=True)
            raise
    
    def _check_python_syntax(self, code: str) -> List[Dict[str, Any]]:
        """
        Проверяет синтаксис Python-кода.
        
        Args:
            code: Исходный код
            
        Returns:
            List[Dict[str, Any]]: Список найденных проблем
        """
        try:
            ast.parse(code)
            return []
        except SyntaxError as e:
            return [{
                'type': 'syntax_error',
                'message': e.msg,
                'line': e.lineno,
                'col': e.offset,
                'severity': 'error'
            }]
    
    def _check_unused_imports(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """
        Ищет неиспользуемые импорты в Python-коде.
        
        Args:
            tree: AST-дерево кода
            
        Returns:
            List[Dict[str, Any]]: Список неиспользуемых импортов
        """
        issues = []
        
        # Собираем все имена, которые определены в коде
        defined_names = set()
        used_names = set()
        
        class NameCollector(ast.NodeVisitor):
            def visit_Name(self, node):
                used_names.add(node.id)
                self.generic_visit(node)
        
        # Собираем использованные имена
        NameCollector().visit(tree)
        
        # Проверяем импорты
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    if name.asname:
                        defined_names.add(name.asname)
                    else:
                        defined_names.add(name.name.split('.')[0])
            
            elif isinstance(node, ast.ImportFrom):
                for name in node.names:
                    if name.asname:
                        defined_names.add(name.asname)
                    else:
                        defined_names.add(name.name)
        
        # Ищем неиспользуемые импорты
        unused_imports = defined_names - used_names
        
        for name in unused_imports:
            issues.append({
                'type': 'unused_import',
                'message': f"Unused import: {name}",
                'severity': 'warning',
                'fix': f"Remove unused import: {name}"
            })
        
        return issues
    
    def _check_undefined_variables(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """
        Ищет неопределенные переменные в Python-коде.
        
        Args:
            tree: AST-дерево кода
            
        Returns:
            List[Dict[str, Any]]: Список неопределенных переменных
        """
        issues = []
        defined = set()
        
        class UndefinedVars(ast.NodeVisitor):
            def __init__(self):
                self.scope = [set()]  # Текущая область видимости
                self.issues = []
            
            def visit_FunctionDef(self, node):
                # Входим в новую область видимости функции
                self.scope.append(set())
                
                # Аргументы функции считаются определенными
                for arg in node.args.args:
                    self.scope[-1].add(arg.arg)
                
                # Обрабатываем тело функции
                self.generic_visit(node)
                
                # Выходим из области видимости
                self.scope.pop()
            
            def visit_Assign(self, node):
                # Обрабатываем левую часть присваивания (цели)
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.scope[-1].add(target.id)
                    elif isinstance(target, (ast.Tuple, ast.List)):
                        for elt in target.elts:
                            if isinstance(elt, ast.Name):
                                self.scope[-1].add(elt.id)
                
                # Обрабатываем правую часть
                self.generic_visit(node)
            
            def visit_Name(self, node):
                # Проверяем, является ли имя переменной загружаемым (а не сохраняемым)
                if isinstance(node.ctx, ast.Load):
                    # Проверяем все области видимости от текущей до глобальной
                    name_defined = False
                    for scope in reversed(self.scope):
                        if node.id in scope:
                            name_defined = True
                            break
                    
                    if not name_defined and not node.id.startswith('_') and node.id not in dir(__builtins__):
                        self.issues.append({
                            'type': 'undefined_variable',
                            'message': f"Undefined variable: {node.id}",
                            'line': node.lineno,
                            'col': node.col_offset,
                            'severity': 'error'
                        })
                
                self.generic_visit(node)
        
        # Запускаем анализатор
        analyzer = UndefinedVars()
        analyzer.visit(tree)
        
        return analyzer.issues

@dataclass
class AnalyzeProjectParams(ProjectCommandParams):
    """Параметры команды анализа проекта."""
    paths: List[str] = field(default_factory=list)
    exclude: List[str] = field(default_factory=list)
    recursive: bool = True
    checks: List[str] = field(default_factory=list)
    max_issues_per_file: int = 50

class AnalyzeProjectCommand(ProjectCommand[AnalyzeProjectParams]):
    """
    Команда для анализа всего проекта.
    
    Рекурсивно анализирует файлы проекта на наличие проблем,
    уязвимостей и нарушений стиля.
    """
    
    name = "analyze_project"
    description = "Анализирует весь проект на наличие проблем"
    
    async def execute(self, params: AnalyzeProjectParams) -> CommandResponse:
        """
        Выполняет анализ проекта.
        
        Args:
            params: Параметры команды
            
        Returns:
            CommandResponse: Результат анализа проекта
        """
        try:
            project_id = self.get_project_id(params)
            project = await self.project_manager.get_project(project_id) if project_id else None
            
            if not project and not params.paths:
                return CommandResponse(
                    success=False,
                    message="No project or paths specified for analysis",
                    data={'error': 'no_project_or_paths'}
                )
            
            # Определяем пути для анализа
            paths_to_analyze = []
            
            if params.paths:
                # Используем указанные пути
                for path_str in params.paths:
                    path = Path(path_str)
                    if not path.is_absolute() and project:
                        path = project.path / path
                    paths_to_analyze.append(path)
            elif project:
                # Используем корень проекта
                paths_to_analyze.append(project.path)
            
            # Анализируем каждый путь
            results = {
                'files_analyzed': 0,
                'issues_found': 0,
                'files_with_issues': 0,
                'issues_by_severity': {
                    'error': 0,
                    'warning': 0,
                    'info': 0
                },
                'files': {}
            }
            
            # Получаем список файлов для анализа
            files_to_analyze = []
            for path in paths_to_analyze:
                if path.is_file():
                    files_to_analyze.append(path)
                elif path.is_dir():
                    if params.recursive:
                        files_to_analyze.extend(self._find_files_recursive(path, params.exclude))
                    else:
                        files_to_analyze.extend([f for f in path.iterdir() if f.is_file()])
            
            # Анализируем каждый файл
            for file_path in files_to_analyze:
                try:
                    # Пропускаем файлы из списка исключений
                    if self._should_exclude(file_path, params.exclude):
                        continue
                    
                    # Определяем язык по расширению
                    language = self._detect_language(file_path)
                    
                    # Пропускаем неподдерживаемые языки
                    if language not in ['python']:  # Пока поддерживаем только Python
                        continue
                    
                    # Анализируем файл
                    result = await self._analyze_code_file(
                        file_path=str(file_path),
                        language=language,
                        checks=params.checks,
                        max_issues=params.max_issues_per_file
                    )
                    
                    # Обрабатываем результаты
                    if result.success and 'issues' in result.data:
                        issues = result.data['issues']
                        if issues:
                            rel_path = str(file_path.relative_to(project.path)) if project else str(file_path)
                            results['files'][rel_path] = {
                                'path': rel_path,
                                'language': language,
                                'issues': issues,
                                'issue_count': len(issues)
                            }
                            
                            # Обновляем статистику
                            results['files_analyzed'] += 1
                            results['files_with_issues'] += 1
                            results['issues_found'] += len(issues)
                            
                            for issue in issues:
                                severity = issue.get('severity', 'info')
                                if severity in results['issues_by_severity']:
                                    results['issues_by_severity'][severity] += 1
                    else:
                        results['files_analyzed'] += 1
                        
                except Exception as e:
                    logger.error(f"Error analyzing file {file_path}: {str(e)}", exc_info=True)
            
            # Формируем итоговый ответ
            return CommandResponse(
                success=True,
                message=f"Analyzed {results['files_analyzed']} files, found {results['issues_found']} issues in {results['files_with_issues']} files",
                data=results
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze project: {str(e)}", exc_info=True)
            return CommandResponse(
                success=False,
                message=f"Failed to analyze project: {str(e)}",
                data={
                    'error': 'project_analysis_failed',
                    'details': str(e)
                }
            )
    
    def _find_files_recursive(self, directory: Path, exclude: List[str]) -> List[Path]:
        """
        Рекурсивно ищет все файлы в директории.
        
        Args:
            directory: Корневая директория для поиска
            exclude: Список шаблонов для исключения
            
        Returns:
            List[Path]: Список найденных файлов
        """
        files = []
        
        for item in directory.iterdir():
            # Пропускаем скрытые директории и файлы
            if item.name.startswith('.'):
                continue
                
            # Пропускаем исключенные пути
            if self._should_exclude(item, exclude):
                continue
                
            if item.is_file():
                files.append(item)
            elif item.is_dir():
                files.extend(self._find_files_recursive(item, exclude))
        
        return files
    
    def _should_exclude(self, path: Path, exclude_patterns: List[str]) -> bool:
        """
        Проверяет, должен ли путь быть исключен из анализа.
        
        Args:
            path: Путь для проверки
            exclude_patterns: Список шаблонов для исключения
            
        Returns:
            bool: True, если путь должен быть исключен
        """
        path_str = str(path)
        
        for pattern in exclude_patterns:
            if pattern.startswith('*') and path_str.endswith(pattern[1:]):
                return True
            elif pattern in path_str:
                return True
                
        return False
    
    def _detect_language(self, file_path: Path) -> str:
        """
        Определяет язык программирования по расширению файла.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            str: Идентификатор языка программирования
        """
        # Используем ту же логику, что и в AnalyzeCodeCommand
        return AnalyzeCodeCommand._detect_language(self, file_path)
