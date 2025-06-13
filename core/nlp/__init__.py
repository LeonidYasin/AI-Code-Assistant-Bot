"""
Natural Language Processing Module

This module provides functionality for processing natural language commands
and converting them into structured actions that can be executed by the system.
"""
from .command_processor import NLPCommandProcessor
from .prompt_builder import PromptBuilder
from .response_parser import ResponseParser
from .handlers import (
    ProjectCommandHandler,
    FileCommandHandler,
    CodeCommandHandler
)

# Create a default instance for easy import
default_processor = NLPCommandProcessor()

__all__ = [
    'NLPCommandProcessor',
    'PromptBuilder',
    'ResponseParser',
    'ProjectCommandHandler',
    'FileCommandHandler',
    'CodeCommandHandler',
    'default_processor'
]
