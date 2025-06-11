"""
Basic command line test script for the bot.
This script tests commands that don't require API access.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return (success, output)"""
    try:
        result = subprocess.run(
            [sys.executable, "main.py"] + cmd.split(),
            cwd=cwd or os.getcwd(),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        return result.returncode == 0, result.stdout
    except Exception as e:
        return False, str(e)

def test_help():
    print("\n=== Testing help command ===")
    success, output = run_command("help")
    if success:
        print("✅ Help command works")
        print("Available commands in help:")
        print("-", "\n- ".join(line.strip() for line in output.split('\n') if line.strip()))
    else:
        print("❌ Help command failed")
    return success

def test_project_commands():
    print("\n=== Testing project commands ===")
    
    # Create a test project
    test_project = "test_project_123"
    print(f"Creating test project: {test_project}")
    success, output = run_command(f"project create {test_project}")
    
    if success and "создан" in output.lower():
        print(f"✅ Project {test_project} created successfully")
        
        # Test project list
        print("\nTesting project list:")
        success, output = run_command("project list")
        if test_project in output:
            print("✅ Project list shows the created project")
        else:
            print("❌ Project list doesn't show the created project")
            return False
            
        # Test project info
        print("\nTesting project info:")
        success, output = run_command("project info")
        if "информация о проекте" in output.lower():
            print("✅ Project info works")
        else:
            print("❌ Project info failed")
            return False
            
        return True
    else:
        print("❌ Failed to create test project")
        print(f"Output: {output}")
        return False

def main():
    print("Starting basic command tests...")
    
    # Get current directory
    base_dir = Path(__file__).parent.absolute()
    print(f"Running tests in: {base_dir}")
    
    # Run tests
    tests = [
        ("Help Command", test_help),
        ("Project Commands", test_project_commands),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n{'='*40}")
        print(f"TEST: {name}")
        print("="*40)
        try:
            success = test_func()
            results.append((name, success))
            status = "PASSED" if success else "FAILED"
            print(f"\n{name}: {status}")
        except Exception as e:
            print(f"❌ Error during test: {e}")
            results.append((name, False))
    
    # Print summary
    print("\n" + "="*50)
    print("TEST SUMMARY:")
    print("="*50)
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {name}")
    
    # Return non-zero exit code if any test failed
    if not all(success for _, success in results):
        sys.exit(1)

if __name__ == "__main__":
    main()
