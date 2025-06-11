import asyncio
from main import process_command, process_command_full

async def test_commands():
    # Test help command
    print("\n=== Testing /help ===")
    help_result = await process_command("/help")
    print(help_result[:500] + "...\n[truncated]" if len(help_result) > 500 else help_result)
    
    # Test project commands
    print("\n=== Testing Project Commands ===")
    
    # List projects
    print("\n1. Listing projects:")
    print(await process_command("/project list"))
    
    # Create a test project
    print("\n2. Creating test project:")
    print(await process_command("/project create test_project"))
    
    # List projects again to see the new project
    print("\n3. Listing projects after creation:")
    print(await process_command("/project list"))
    
    # Test file operations
    print("\n=== Testing File Operations ===")
    
    # Create a test file
    print("\n4. Creating test file:")
    print(await process_command("/create test.py print('Hello, World!')"))
    
    # Read the created file
    print("\n5. Reading test file:")
    print(await process_command("/read test.py"))
    
    # List files
    print("\n6. Listing files:")
    print(await process_command("/list"))
    
    # Test code analysis
    print("\n=== Testing Code Analysis ===")
    
    # Analyze code directly
    print("\n7. Analyzing code snippet:")
    print(await process_command("/analyze def add(a, b):\n    return a + b"))
    
    # Analyze the test file
    print("\n8. Analyzing test file:")
    print(await process_command("/analyze_file test.py"))
    
    # Analyze project
    print("\n9. Analyzing project:")
    print(await process_command("/analyze_project"))
    
    # Test running scripts
    print("\n=== Testing Script Execution ===")
    
    # Run the test script
    print("\n10. Running test script:")
    print(await process_command("/run test.py"))
    
    # Test shell command
    print("\n11. Running shell command:")
    print(await process_command("/cmd echo Hello from shell"))
    
    # Test natural language commands
    print("\n=== Testing Natural Language Commands ===")
    
    # Natural language file creation
    print("\n12. Natural language file creation:")
    print(await process_command("создай файл hello.py с кодом 'print(\"Привет, мир!\")'"))
    
    # Natural language file reading
    print("\n13. Natural language file reading:")
    print(await process_command("покажи содержимое файла hello.py"))
    
    # Natural language file listing
    print("\n14. Natural language file listing:")
    print(await process_command("покажи список файлов"))
    
    # Cleanup
    print("\n=== Cleaning Up ===")
    print("\n15. Deleting test files:")
    print(await process_command("/delete test.py"))
    print(await process_command("/delete hello.py"))
    
    print("\n16. Deleting test project:")
    # Note: You might need to implement project deletion in ProjectManager
    print("Project deletion not implemented yet")

if __name__ == "__main__":
    asyncio.run(test_commands())
