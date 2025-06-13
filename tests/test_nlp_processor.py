"""
Tests for the NLP processor module.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from core.nlp.command_processor import NLPCommandProcessor, CommandContext
from core.project.manager import ProjectManager

# Test data
TEST_PROJECT_NAME = "test_project"
TEST_FILE_CONTENT = "print('Hello, World!')"

# Fixtures
@pytest.fixture
def project_manager(tmp_path):
    """Create a ProjectManager instance with a temporary directory."""
    return ProjectManager(tmp_path)

@pytest.fixture
def command_context(project_manager):
    """Create a command context for testing."""
    return CommandContext(
        chat_id="12345",
        user_id="test_user",
        bot_data={"active_projects": {}},
        project_manager=project_manager,
        current_project=None
    )

@pytest.fixture
def processor():
    """Create an NLPCommandProcessor instance."""
    return NLPCommandProcessor()

# Tests
@pytest.mark.asyncio
async def test_create_project(processor, command_context, tmp_path):
    """Test project creation."""
    # Mock the project manager's create_project method
    with patch.object(command_context.project_manager, 'create_project', new_callable=AsyncMock) as mock_create:
        mock_project = MagicMock()
        mock_project.name = TEST_PROJECT_NAME
        mock_project.path = tmp_path / TEST_PROJECT_NAME
        mock_create.return_value = mock_project
        
        # Test creating a project
        success, response = await processor.process_command(
            f"Создай новый проект с именем {TEST_PROJECT_NAME}",
            command_context
        )
        
        # Assertions
        assert success is True
        assert TEST_PROJECT_NAME in response
        mock_create.assert_called_once_with(name=TEST_PROJECT_NAME, template=None)

@pytest.mark.asyncio
async def test_list_projects(processor, command_context, project_manager):
    """Test listing projects."""
    # Mock the project manager's list_projects method
    with patch.object(project_manager, 'list_projects', new_callable=AsyncMock) as mock_list:
        mock_list.return_value = ["project1", "project2"]
        
        # Test listing projects
        success, response = await processor.process_command(
            "Покажи список проектов",
            command_context
        )
        
        # Assertions
        assert success is True
        assert "project1" in response
        assert "project2" in response
        mock_list.assert_called_once()

@pytest.mark.asyncio
async def test_create_file(processor, command_context, project_manager, tmp_path):
    """Test file creation."""
    # Set up test data
    test_project = tmp_path / TEST_PROJECT_NAME
    test_project.mkdir()
    test_file = test_project / "test.py"
    
    # Mock the project manager
    with patch.object(project_manager, 'get_project', new_callable=AsyncMock) as mock_get_project:
        mock_project = MagicMock()
        mock_project.path = test_project
        mock_project.create_file = AsyncMock(return_value=test_file)
        mock_get_project.return_value = mock_project
        
        # Set current project
        command_context.current_project = TEST_PROJECT_NAME
        
        # Test creating a file
        success, response = await processor.process_command(
            f"Создай файл test.py с кодом {TEST_FILE_CONTENT}",
            command_context
        )
        
        # Assertions
        assert success is True
        assert "test.py" in response
        mock_project.create_file.assert_called_once_with("test.py", TEST_FILE_CONTENT)

@pytest.mark.asyncio
async def test_analyze_code(processor, command_context):
    """Test code analysis."""
    # Test analyzing code
    success, response = await processor.process_command(
        f"Проанализируй код: {TEST_FILE_CONTENT}",
        command_context
    )
    
    # Basic assertions
    assert success is True
    assert isinstance(response, str)

@pytest.mark.asyncio
async def test_error_handling(processor, command_context):
    """Test error handling."""
    # Test with invalid command
    success, response = await processor.process_command(
        "несуществующая команда",
        command_context
    )
    
    # Should fail gracefully
    assert success is False
    assert "error" in response.lower() or "unknown" in response.lower()

# Run the tests
if __name__ == "__main__":
    pytest.main(["-v", "test_nlp_processor.py"])
