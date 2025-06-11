@echo off
setlocal enabledelayedexpansion

echo [INFO] Creating deployment directory...

set DEPLOY_DIR=deployment\ai_code_assistant

REM Create directory structure
mkdir "%DEPLOY_DIR%" 2>nul
mkdir "%DEPLOY_DIR%\config" 2>nul
mkdir "%DEPLOY_DIR%\core" 2>nul
mkdir "%DEPLOY_DIR%\core\ai" 2>nul
mkdir "%DEPLOY_DIR%\core\bot" 2>nul
mkdir "%DEPLOY_DIR%\core\code_generator" 2>nul
mkdir "%DEPLOY_DIR%\core\llm" 2>nul
mkdir "%DEPLOY_DIR%\core\project" 2>nul
mkdir "%DEPLOY_DIR%\handlers" 2>nul

echo [INFO] Copying Python files...

REM Copy Python files
xcopy /s /y "config\*.py" "%DEPLOY_DIR%\config\"
xcopy /s /y "core\*.py" "%DEPLOY_DIR%\core\"
xcopy /s /y "core\ai\*.py" "%DEPLOY_DIR%\core\ai\"
xcopy /s /y "core\bot\*.py" "%DEPLOY_DIR%\core\bot\"
xcopy /s /y "core\code_generator\*.py" "%DEPLOY_DIR%\core\code_generator\"
xcopy /s /y "core\llm\*.py" "%DEPLOY_DIR%\core\llm\"
xcopy /s /y "core\project\*.py" "%DEPLOY_DIR%\core\project\"
xcopy /s /y "handlers\*.py" "%DEPLOY_DIR%\handlers\"

REM Copy root Python files
copy "main.py" "%DEPLOY_DIR%\" >nul

REM Copy requirements
pip freeze > "%DEPLOY_DIR%\requirements.txt"

echo [INFO] Creating README.md...
echo # AI Code Assistant - Deployment Package> "%DEPLOY_DIR%\README.md"
echo.>> "%DEPLOY_DIR%\README.md"
echo ## Quick Start>> "%DEPLOY_DIR%\README.md"
echo.>> "%DEPLOY_DIR%\README.md"
echo 1. Install dependencies:>> "%DEPLOY_DIR%\README.md"
echo    ```>> "%DEPLOY_DIR%\README.md"
echo    pip install -r requirements.txt>> "%DEPLOY_DIR%\README.md"
echo    ```>> "%DEPLOY_DIR%\README.md"

echo [INFO] Creating archive...

set TIMESTAMP=%DATE:~-4%%DATE:~3,2%%DATE:~0,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%
set TIMESTAMP=!TIMESTAMP: =0!

powershell Compress-Archive -Path "%DEPLOY_DIR%\*" -DestinationPath "deployment\ai_code_assistant_%TIMESTAMP%.zip" -Force

echo [SUCCESS] Deployment package created: deployment\ai_code_assistant_%TIMESTAMP%.zip
echo Deployment directory: %CD%\%DEPLOY_DIR%
