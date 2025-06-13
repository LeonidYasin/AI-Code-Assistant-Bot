import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.absolute())
sys.path.insert(0, project_root)

# Now import and run the analysis
from main import main

if __name__ == "__main__":
    # List available projects first
    print("Доступные проекты:")
    projects_dir = Path("projects")
    if projects_dir.exists():
        projects = [d.name for d in projects_dir.iterdir() if d.is_dir()]
        for i, project in enumerate(projects, 1):
            print(f"{i}. {project}")
    
    # Run the analysis
    print("\nЗапускаем анализ проекта...")
    sys.argv = ["main.py", "analyze_project"]
    main()
