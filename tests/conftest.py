"""Pytest configuration and fixtures."""
import os
import shutil
from pathlib import Path
import pytest

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory and change to it for the test."""
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(old_cwd)

@pytest.fixture
def test_project(tmp_path):
    """Create a test project directory structure."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    
    # Create some test files
    (project_dir / "main.py").write_text('def hello():\n    return "Hello, World!"')
    (project_dir / "requirements.txt").write_text("pytest\nblack\n")
    
    return project_dir
