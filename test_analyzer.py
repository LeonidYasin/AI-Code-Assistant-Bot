from core.project.analyzer import ProjectAnalyzer
from pathlib import Path
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_analyzer.py <project_path>")
        return
    
    project_path = Path(sys.argv[1]).resolve()
    print(f"Analyzing project at: {project_path}")
    
    analyzer = ProjectAnalyzer(project_path)
    result = analyzer.analyze_project()
    
    # Print basic information
    print("\nProject Analysis Results:")
    print("=" * 50)
    print(f"Project Root: {result['project_root']}")
    print(f"Total Files: {result['stats']['total_files']}")
    print(f"Total Size: {result['stats']['total_size']} bytes")
    print(f"Number of Directories: {result['stats']['dir_count']}")
    
    # Print project structure
    print("\nProject Structure:")
    print("-" * 50)
    print_structure(result['structure'])
    
    # Print summary
    print("\nSummary:")
    print("-" * 50)
    print(f"Project Type: {result['summary'].get('project_type', 'Unknown')}")
    print(f"Has README: {result['summary'].get('has_readme', False)}")
    print(f"Has LICENSE: {result['summary'].get('has_license', False)}")
    print(f"Has .gitignore: {result['summary'].get('has_gitignore', False)}")

def print_structure(node, indent=0):
    """Recursively print the project structure."""
    if node.get('type') == 'directory':
        print('  ' * indent + f"📁 {node.get('name', '')}/")
        for child in node.get('children', [])[:5]:  # Show first 5 items
            print_structure(child, indent + 1)
        if len(node.get('children', [])) > 5:
            print('  ' * (indent + 1) + f"... and {len(node['children']) - 5} more items")
    elif node.get('type') == 'file':
        print('  ' * indent + f"📄 {node.get('name', '')}")

if __name__ == "__main__":
    main()
