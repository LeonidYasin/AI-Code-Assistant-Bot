# Create deployment directory
$deployDir = "deployment\ai_code_assistant"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$zipFile = "deployment\ai_code_assistant_${timestamp}.zip"

Write-Host "[INFO] Creating deployment directory..." -ForegroundColor Cyan

# Ensure directories exist
New-Item -ItemType Directory -Force -Path $deployDir | Out-Null
New-Item -ItemType Directory -Force -Path "$deployDir\config" | Out-Null
New-Item -ItemType Directory -Force -Path "$deployDir\core" | Out-Null
New-Item -ItemType Directory -Force -Path "$deployDir\core\ai" | Out-Null
New-Item -ItemType Directory -Force -Path "$deployDir\core\bot" | Out-Null
New-Item -ItemType Directory -Force -Path "$deployDir\core\code_generator" | Out-Null
New-Item -ItemType Directory -Force -Path "$deployDir\core\llm" | Out-Null
New-Item -ItemType Directory -Force -Path "$deployDir\core\project" | Out-Null
New-Item -ItemType Directory -Force -Path "$deployDir\handlers" | Out-Null

# Copy files
Write-Host "[INFO] Copying Python files..." -ForegroundColor Cyan

# Copy Python files from each directory
Copy-Item -Path "config\*.py" -Destination "$deployDir\config\" -Force
Copy-Item -Path "core\*.py" -Destination "$deployDir\core\" -Force
Copy-Item -Path "core\ai\*.py" -Destination "$deployDir\core\ai\" -Force
Copy-Item -Path "core\bot\*.py" -Destination "$deployDir\core\bot\" -Force
Copy-Item -Path "core\code_generator\*.py" -Destination "$deployDir\core\code_generator\" -Force
Copy-Item -Path "core\llm\*.py" -Destination "$deployDir\core\llm\" -Force
Copy-Item -Path "core\project\*.py" -Destination "$deployDir\core\project\" -Force
Copy-Item -Path "handlers\*.py" -Destination "$deployDir\handlers\" -Force

# Copy main files
Copy-Item -Path "main.py" -Destination $deployDir -Force

# Create requirements.txt
Write-Host "[INFO] Creating requirements.txt..." -ForegroundColor Cyan
pip freeze > "$deployDir\requirements.txt"

# Create README.md
Write-Host "[INFO] Creating README.md..." -ForegroundColor Cyan
@"
# AI Code Assistant - Deployment Package

## Quick Start

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Copy .env.example to .env and update with your configuration:
   ```
   copy .env.example .env
   # Edit .env with your configuration
   ```

3. Run the application:
   ```
   python main.py
   ```

## Project Structure

- `config/` - Configuration files
- `core/` - Core application code
- `handlers/` - Message and command handlers
- `main.py` - Application entry point

## Configuration

Update the following environment variables in `.env`:

- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token
- `GIGACHAT_CREDENTIALS` - GigaChat API credentials
- `LOG_LEVEL` - Logging level (INFO, DEBUG, etc.)

## License

This project is licensed under the MIT License.
"@ | Out-File -FilePath "$deployDir\README.md" -Encoding utf8

# Create zip archive
Write-Host "[INFO] Creating archive..." -ForegroundColor Cyan
Compress-Archive -Path "$deployDir\*" -DestinationPath $zipFile -Force

Write-Host "`n[SUCCESS] Deployment package created: $zipFile" -ForegroundColor Green
Write-Host "Deployment directory: $(Resolve-Path $deployDir)" -ForegroundColor Green
