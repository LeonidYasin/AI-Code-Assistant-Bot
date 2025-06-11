# Simple test script for basic commands

# 1. Test help command
Write-Host "Testing help command..."
python main.py help

# 2. Create a test project
$projectName = "test_project_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Write-Host "`nCreating test project: $projectName"
python main.py project create $projectName

# 3. Check if project was created
if (Test-Path $projectName) {
    Write-Host "Project created successfully!" -ForegroundColor Green
} else {
    Write-Host "Failed to create project!" -ForegroundColor Red
    exit 1
}

# 4. Switch to the project
Write-Host "`nSwitching to project..."
python main.py project switch $projectName

# 5. Create a test file
$testFile = "$projectName/test_script.py"
@'
def hello():
    return "Hello, World!"
'@ | Out-File -FilePath $testFile -Encoding utf8

# 6. Test file analysis
Write-Host "`nTesting file analysis..."
python main.py analyze $testFile

# 7. Test project analysis
Write-Host "`nTesting project analysis..."
python main.py analyze_project

# 8. Test project info
Write-Host "`nTesting project info..."
python main.py project info

# 9. Test error handling
Write-Host "`nTesting error handling (should show error):"
python main.py invalid_command

Write-Host "`nTest script completed!" -ForegroundColor Green
