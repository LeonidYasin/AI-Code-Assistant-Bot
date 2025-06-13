#!/usr/bin/env python3
"""
Test script to list projects without requiring BOT_TOKEN.
"""
import sys
import os
from pathlib import Path
from core.project.manager import ProjectManager

def main():
    # Initialize project manager
    project_manager = ProjectManager()
    
    # List projects
    success, result = project_manager.list_projects()
    
    if success:
        print("📋 Список проектов:")
        for project in result:
            status = "✅" if project.get('has_config', False) else "⚠️"
            config_status = "" if project.get('has_config', False) else " (без конфигурации)"
            print(f"• {status} {project['name']}{config_status}")
            print(f"  📁 {project['path']}")
    else:
        print(f"❌ Ошибка: {result}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
