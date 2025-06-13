"""
Response parsing for natural language processing.

This module handles parsing and validating responses from the LLM
into structured command data.
"""
import json
import logging
import re
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class ResponseParser:
    """Parses and validates LLM responses into command data."""
    
    def __init__(self):
        self.required_fields = ['type', 'params', 'confidence', 'explanation']
        self.valid_commands = {
            'create_project', 'list_projects', 'switch_project',
            'create_file', 'list_files', 'view_file',
            'run_code', 'analyze_code', 'analyze_project'
        }
    
    def parse(self, llm_response: str) -> Dict[str, Any]:
        """Parse LLM response into structured command data.
        
        Args:
            llm_response: Raw response from the LLM
            
        Returns:
            Parsed command data
            
        Raises:
            ValueError: If the response cannot be parsed or is invalid
        """
        if not llm_response:
            raise ValueError("Empty response from LLM")
            
        logger.debug(f"Parsing LLM response: {llm_response[:200]}...")
        
        try:
            # Try to extract JSON from the response
            json_data = self._extract_json(llm_response)
            if not json_data:
                logger.error(f"No valid JSON found in response: {llm_response[:500]}...")
                raise ValueError("No valid JSON found in response")
            
            logger.debug(f"Extracted JSON data: {json_data}")
            
            # Validate the command structure
            self._validate_command(json_data)
            
            return json_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}\nResponse: {llm_response[:500]}...")
            raise ValueError(f"Invalid JSON in response: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing response: {str(e)}\nResponse: {llm_response[:500]}...")
            raise
    
    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from text, handling common formatting issues."""
        logger.debug(f"Extracting JSON from: {text[:200]}...")
        
        # Try to find JSON in code blocks first
        json_match = re.search(r'```(?:json)?\n(.*?)\n```', text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
        
        # Try to parse as JSON directly first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.debug("Direct JSON parse failed, trying to clean and extract...")
        
        # Try to clean up the text and extract JSON
        try:
            # Handle case where the response is a string containing escaped JSON
            if text.startswith('content=') and "'" in text:
                # Extract the content part after the first single quote
                content_start = text.find("'") + 1
                content_end = text.rfind("'")
                if content_end > content_start:
                    text = text[content_start:content_end]
                    # Unescape the string
                    text = text.encode().decode('unicode_escape')
                    logger.debug(f"Unescaped text: {text[:200]}...")
            
            # Try to find a JSON object in the text
            json_match = re.search(r'\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}', text)
            if json_match:
                json_str = json_match.group(0)
                logger.debug(f"Found potential JSON: {json_str[:200]}...")
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse JSON: {str(e)}")
                    # Try to fix common issues in the JSON
                    json_str = self._fix_json(json_str)
                    return json.loads(json_str)
            
            # If no JSON object found, try to find the first { and last }
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = text[start:end]
                logger.debug(f"Extracted JSON string: {json_str[:200]}...")
                # Try to clean up any remaining escape sequences
                json_str = json_str.replace('\\\\', '\\')  # Fix double backslashes
                json_str = json_str.replace('\\"', '"')
                json_str = json_str.replace("\\'", "'")
                
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse extracted JSON: {str(e)}")
                    # Try to fix common issues in the JSON
                    json_str = self._fix_json(json_str)
                    return json.loads(json_str)
                
        except Exception as e:
            logger.debug(f"Error extracting JSON: {str(e)}")
            pass
            
        return None
        
    def _fix_json(self, json_str: str) -> str:
        """Attempt to fix common JSON formatting issues."""
        # Fix truncated strings
        if '"' in json_str and not json_str.endswith('"'):
            json_str = json_str.rsplit('"', 1)[0] + '"'
            
        # Fix unclosed objects/arrays
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        
        while open_braces > close_braces:
            json_str += '}'
            close_braces += 1
            
        # Fix unclosed strings
        lines = json_str.split('\n')
        for i, line in enumerate(lines):
            if ':' in line and '"' in line:
                key, value = line.split(':', 1)
                if value.count('"') % 2 != 0:  # Unclosed string
                    lines[i] = line + '"'
                    
        return '\n'.join(lines)
    
    def _validate_command(self, command_data: Dict[str, Any]) -> None:
        """Validate the structure and content of a command.
        
        Args:
            command_data: The parsed command data
            
        Raises:
            ValueError: If the command is invalid
        """
        # Check for required fields
        missing_fields = [
            field for field in self.required_fields 
            if field not in command_data
        ]
        
        if missing_fields:
            raise ValueError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        # Check command type
        command_type = command_data.get('type')
        if command_type not in self.valid_commands:
            raise ValueError(
                f"Invalid command type: {command_type}. "
                f"Must be one of: {', '.join(self.valid_commands)}"
            )
        
        # Check confidence level
        confidence = command_data.get('confidence', 0)
        if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
            raise ValueError("Confidence must be a number between 0 and 1")
        
        # Check params is a dictionary
        params = command_data.get('params', {})
        if not isinstance(params, dict):
            raise ValueError("Params must be a dictionary")
    
    def format_error(self, error: Exception) -> str:
        """Format an error message for display to the user."""
        if isinstance(error, json.JSONDecodeError):
            return "❌ Failed to parse response from AI. Please try again."
        elif isinstance(error, ValueError):
            return f"❌ {str(error)}"
        else:
            return "❌ An unexpected error occurred. Please try again later."
