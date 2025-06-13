#!/usr/bin/env python3
"""
Project Analysis Tool

This script analyzes a Python project and provides a detailed report.
"""

import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def safe_print(text: str) -> None:
    """Safely print text, handling encoding issues."""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback for terminals that don't support unicode
        print(text.encode('ascii', 'replace').decode('ascii'))

def print_analysis_results(results: Dict[str, Any]) -> None:
    """Print the analysis results in a user-friendly format."""
    safe_print("\n" + "="*50)
    safe_print(f"Project: {results.get('project_root', 'Unknown')}")
    
    # Print basic statistics
    stats = results.get('stats', {})
    safe_print("\n[STATISTICS]")
    safe_print(f"- Total files: {stats.get('total_files', 0)}")
    safe_print(f"- Total size: {stats.get('total_size', 0) / 1024:.2f} KB")
    safe_print(f"- Total lines: {stats.get('total_lines', 0)}")
    
    # Print file types
    if 'file_types' in stats:
        safe_print("\n[FILE TYPES]")
        for ftype, count in sorted(stats['file_types'].items()):
            safe_print(f"- {ftype}: {count} files")
    
    # Print project health
    summary = results.get('summary', {})
    health = summary.get('health', {})
    if health:
        safe_print("\n[PROJECT HEALTH]")
        safe_print(f"- Has README: {'Yes' if health.get('has_readme') else 'No'}")
        safe_print(f"- Has tests: {'Yes' if health.get('has_tests') else 'No'}")
        safe_print(f"- Has requirements: {'Yes' if health.get('has_requirements') else 'No'}")
    
    # Print recommendations
    recommendations = summary.get('recommendations', [])
    if recommendations:
        safe_print("\n[RECOMMENDATIONS]")
        for i, rec in enumerate(recommendations, 1):
            safe_print(f"{i}. {rec}")
    
    safe_print("\n" + "="*50 + "\nAnalysis complete!")

def analyze_project(project_path: Path) -> Dict[str, Any]:
    """Analyze the project at the given path."""
    from core.project.analyzer import ProjectAnalyzer
    
    if not project_path.exists():
        raise FileNotFoundError(f"Project path does not exist: {project_path}")
    
    analyzer = ProjectAnalyzer(project_path)
    return analyzer.analyze_project()

def main() -> None:
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python analyze_project.py <project_path>")
        print("\nExample:")
        print("  python analyze_project.py path/to/your/project")
        sys.exit(1)
    
    try:
        project_path = Path(sys.argv[1]).resolve()
        logger.info(f"Analyzing project at: {project_path}")
        
        # Run the analysis
        results = analyze_project(project_path)
        
        # Print the results
        print_analysis_results(results)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
