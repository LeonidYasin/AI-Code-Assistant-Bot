# PowerShell script to set up development environment

# Check if Python is installed
$pythonVersion = python --version
if ($LASTEXITCODE -ne 0) {
    Write-Error "Python is not installed or not in PATH. Please install Python 3.9 or higher."
    exit 1
}

# Check Python version
$pythonVersion = [System.Version]($pythonVersion -replace '^Python ([0-9]+\.[0-9]+\.[0-9]+).*$', '$1')
$minVersion = [System.Version]"3.9.0"

if ($pythonVersion -lt $minVersion) {
    Write-Error "Python 3.9 or higher is required. Current version: $pythonVersion"
    exit 1
}

# Create and activate virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Green
python -m venv venv
.\venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Green
python -m pip install --upgrade pip

# Install development dependencies
Write-Host "Installing development dependencies..." -ForegroundColor Green
pip install -r requirements-dev.txt

# Install pre-commit hooks
Write-Host "Installing pre-commit hooks..." -ForegroundColor Green
pre-commit install

Write-Host "`nDevelopment environment setup complete!" -ForegroundColor Green
Write-Host "To activate the virtual environment, run:" -ForegroundColor Yellow
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host "`nTo run tests, use:" -ForegroundColor Yellow
Write-Host "  pytest" -ForegroundColor Cyan
