#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wrapper script to run the project with proper encoding settings.
"""
import sys
import os
import io
import asyncio
from pathlib import Path

def setup_console_encoding():
    """Setup console encoding to handle UTF-8 properly."""
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    os.environ["PYTHONIOENCODING"] = "utf-8"

async def run_main():
    """Run the main function from the project."""
    # Add project directory to path
    project_dir = Path(__file__).parent / "projects" / "deployed_assistant_20250611_141300"
    sys.path.insert(0, str(project_dir))
    
    # Import the main module
    from main import main as project_main
    
    # Run the main function
    if asyncio.iscoroutinefunction(project_main):
        await project_main()
    else:
        project_main()

def main():
    """Main entry point."""
    setup_console_encoding()
    
    try:
        asyncio.run(run_main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error running project: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
