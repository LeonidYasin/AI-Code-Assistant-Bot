"""
Base command handler for natural language processing.

This module defines the base class for all command handlers.
"""
from typing import Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod

class CommandHandler(ABC):
    """Base class for command handlers."""
    
    @abstractmethod
    async def handle(
        self, 
        command_data: Dict[str, Any], 
        context: 'CommandContext'
    ) -> Tuple[bool, str]:
        """Handle a command.
        
        Args:
            command_data: The parsed command data
            context: The command context
            
        Returns:
            Tuple of (success, message)
        """
        pass
    
    def _get_param(
        self, 
        params: Dict[str, Any], 
        name: str, 
        required: bool = True,
        default: Any = None
    ) -> Any:
        """Safely get a parameter value.
        
        Args:
            params: The parameters dictionary
            name: The parameter name
            required: Whether the parameter is required
            default: Default value if parameter is not found
            
        Returns:
            The parameter value
            
        Raises:
            ValueError: If a required parameter is missing
        """
        value = params.get(name, default)
        if required and value is None:
            raise ValueError(f"Missing required parameter: {name}")
        return value
    
    def _validate_command_type(
        self, 
        command_data: Dict[str, Any], 
        expected_type: str
    ) -> None:
        """Validate that the command is of the expected type.
        
        Args:
            command_data: The command data
            expected_type: The expected command type
            
        Raises:
            ValueError: If the command type doesn't match
        """
        command_type = command_data.get('type')
        if command_type != expected_type:
            raise ValueError(
                f"Expected command type '{expected_type}', got '{command_type}'"
            )
