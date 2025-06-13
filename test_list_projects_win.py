#!/usr/bin/env python3
"""
Windows-compatible test script to test project commands without requiring BOT_TOKEN.
"""
import sys
import os
import json
from pathlib import Path
from core.project.manager import ProjectManager

def main():
    # Initialize project manager with LLM disabled
    project_manager = ProjectManager(llm_enabled=False)
    
    # Process command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command.startswith('/switch_project'):
            # Parse project name
            name = None
            for param in sys.argv[2:]:
                if param.startswith('name='):
                    name = param.split('=')[1]
            if not name:
                print("❌ Error: /switch_project requires name parameter")
                return 1
            
            print(f"[STATUS] Switching to project: {name}")
            success = project_manager.switch_project(name)
            if success:
                print(f"[SUCCESS] Successfully switched to project: {name}")
            else:
                print("[ERROR] Failed to switch project")
                return 1
        elif command == '/analyze_project':
            print("[STATUS] Getting project info...")
            result = project_manager.get_project_info()
            if result:
                print("[SUCCESS] Project info:")
                print("-" * 50)
                print(json.dumps(result, indent=2, ensure_ascii=False))
                print("-" * 50)
            else:
                print("[ERROR] Failed to get project info")
                return 1
        else:
            print("[ERROR] Unknown command. Available commands:")
            print("  /switch_project name=имя - Переключиться на проект")
            print("  /analyze_project - Проанализировать текущий проект")
            return 1
    else:
        # List projects if no command specified
        print("[STATUS] Listing projects...")
        success, result = project_manager.list_projects()
        
        if success:
            print("=== PROJECTS ===")
            for project in result:
                status = "[OK]" if project.get('has_config', False) else "[!]"
                config_status = "" if project.get('has_config', False) else " (no config)"
                print(f"{status} {project['name']}{config_status}")
                print(f"    Path: {project['path']}")
        else:
            print(f"ERROR: {result}")
        
        return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
