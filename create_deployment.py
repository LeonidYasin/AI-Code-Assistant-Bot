import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

# Configuration
PROJECT_ROOT = Path(__file__).parent
DEPLOY_DIR = PROJECT_ROOT / 'deployment' / 'ai_code_assistant'
EXCLUDED_DIRS = {
    '__pycache__',
    '.git',
    '.github',
    '.vscode',
    'venv',
    'env',
    '.pytest_cache',
    '.mypy_cache',
    'deployment',
    'sessions',
    'logs',
    'projects',
    'temp',
    'tmp',
    'test',
    'tests',
    'screenshots',
    'docs',
    'examples',
}

INCLUDED_EXTENSIONS = {
    '.py', '.txt', '.md', '.json', '.yaml', '.yml', '.env', '.sh', '.bat',
    '.html', '.css', '.js', '.gitignore', 'Dockerfile', 'requirements.txt',
    'README.md', 'LICENSE'
}

# Create deployment directory
DEPLOY_DIR.mkdir(parents=True, exist_ok=True)

def should_include(path: Path) -> bool:
    """Check if a file should be included in the deployment."""
    # Skip hidden files and directories
    if any(part.startswith('.') and part not in {'.gitignore', '.env'} for part in path.parts):
        return False
    
    # Skip excluded directories
    if any(excluded in path.parts for excluded in EXCLUDED_DIRS):
        return False
    
    # Include files with specific extensions
    if path.suffix.lower() in INCLUDED_EXTENSIONS:
        return True
    
    # Include all files in the config directory
    if 'config' in path.parts and path.is_file():
        return True
    
    return False

def copy_project_files():
    """Copy all project files to the deployment directory."""
    print("📦 Copying project files...")
    
    # Copy all files
    for item in PROJECT_ROOT.glob('**/*'):
        if not should_include(item):
            continue
            
        rel_path = item.relative_to(PROJECT_ROOT)
        target_path = DEPLOY_DIR / rel_path
        
        # Create target directory if it doesn't exist
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        if item.is_file():
            shutil.copy2(item, target_path)
            print(f"  [FILE] {rel_path}")

def create_requirements():
    """Create requirements.txt from pip freeze."""
    print("\n[INFO] Generating requirements.txt...")
    requirements_path = DEPLOY_DIR / 'requirements.txt'
    os.system(f'pip freeze > "{requirements_path}"')
    print(f"  [OK] Created {requirements_path.relative_to(PROJECT_ROOT)}")

def create_archive():
    """Create a zip archive of the deployment."""
    print("\n[INFO] Creating deployment archive...")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    archive_name = f"ai_code_assistant_deploy_{timestamp}"
    archive_path = PROJECT_ROOT / 'deployment' / archive_name
    
    # Create zip file
    shutil.make_archive(str(archive_path), 'zip', DEPLOY_DIR)
    
    # Also create a tar.gz for Linux systems
    shutil.make_archive(str(archive_path), 'gztar', DEPLOY_DIR)
    
    print(f"\n[SUCCESS] Deployment packages created in {archive_path}.{{zip,tar.gz}}")

def create_readme():
    """Create a README.md file for the deployment."""
    readme_content = """# AI Code Assistant - Deployment Package

## 🚀 Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables**:
   Copy `.env.example` to `.env` and update the values:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```

## 📁 Project Structure

- `core/` - Core application code
- `handlers/` - Message and command handlers
- `config/` - Configuration files
- `logs/` - Application logs (created at runtime)

## ⚙️ Configuration

Update the following environment variables in `.env`:

- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token
- `GIGACHAT_CREDENTIALS` - GigaChat API credentials
- `LOG_LEVEL` - Logging level (INFO, DEBUG, etc.)

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
"""
    readme_path = DEPLOY_DIR / 'README.md'
    readme_path.write_text(readme_content, encoding='utf-8')
    print(f"  ✅ Created {readme_path.relative_to(PROJECT_ROOT)}")

def main():
    print("[START] Starting deployment package creation...")
    
    # Clean deployment directory
    if DEPLOY_DIR.exists():
        shutil.rmtree(DEPLOY_DIR)
    
    # Create deployment structure
    copy_project_files()
    create_requirements()
    create_readme()
    
    # Create archives
    create_archive()
    
    print("\n[SUCCESS] Deployment package created successfully!")

if __name__ == "__main__":
    main()
