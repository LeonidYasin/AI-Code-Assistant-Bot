#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wrapper script to run the project with proper encoding settings.
"""
import sys
import os
import io
import locale

def main():
    # Set console encoding to UTF-8
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    # Set environment variables for encoding
    os.environ["PYTHONIOENCODING"] = "utf-8"
    
    # Import and run the main module
    from main import main as run_main
    run_main()

if __name__ == "__main__":
    main()
