"""
Core command processing for natural language commands.

This module handles the main processing pipeline for converting
natural language commands into structured actions.
"""
import logging
from typing import Dict, Any, Optional, Tuple, List, Type, Callable, Union
from dataclasses import dataclass
from pathlib import Path

from core.llm.client import llm_client
from core.project.manager import ProjectManager
from .prompt_builder import PromptBuilder
from .response_parser import ResponseParser
from .handlers.base import CommandHandler
from .handlers import (
    ProjectCommandHandler,
    FileCommandHandler,
    CodeCommandHandler
)

logger = logging.getLogger(__name__)

@dataclass
class CommandContext:
    """Context for command execution."""
    chat_id: str
    user_id: str
    bot_data: Dict[str, Any]
    project_manager: ProjectManager
    current_project: Optional[str] = None

class NLPCommandProcessor:
    """Processes natural language commands and converts them to actions."""
    
    def __init__(self):
        self.prompt_builder = PromptBuilder()
        self.response_parser = ResponseParser()
        self.handlers = self._initialize_handlers()
    
    def _initialize_handlers(self) -> Dict[str, Type[CommandHandler]]:
        """Initialize and return command handlers."""
        return {
            'create_project': ProjectCommandHandler(),
            'list_projects': ProjectCommandHandler(),
            'switch_project': ProjectCommandHandler(),
            'create_file': FileCommandHandler(),
            'list_files': FileCommandHandler(),
            'view_file': FileCommandHandler(),
            'run_code': CodeCommandHandler(),
            'analyze_code': CodeCommandHandler(),
            'analyze_project': CodeCommandHandler(),
        }
    
    async def process_command(
        self,
        text: str,
        context: Dict[str, Any],
        chat_id: str,
        user_id: str
    ) -> Tuple[bool, str]:
        """Process a natural language command.
        
        Args:
            text: The user's natural language input
            context: Bot context data
            chat_id: ID of the chat
            user_id: ID of the user
            
        Returns:
            Tuple of (success, response_message)
        """
        try:
            # Initialize context
            cmd_context = self._create_context(context, chat_id, user_id)
            
            # Build prompt for LLM
            prompt = self.prompt_builder.build(text, cmd_context.current_project)
            
            # Get response from LLM
            try:
                # Enhanced debug logging for LLM client inspection
                logger.debug("===== LLM Client Debug Info =====")
                logger.debug(f"LLM client: {llm_client}")
                logger.debug(f"LLM client type: {type(llm_client).__name__}")
                logger.debug(f"LLM client dir: {[m for m in dir(llm_client) if not m.startswith('_')]}")
                
                # Check for _client attribute and log its details
                if hasattr(llm_client, '_client'):
                    logger.debug(f"Found _client attribute: {llm_client._client}")
                    logger.debug(f"_client type: {type(llm_client._client).__name__}")
                    logger.debug(f"_client dir: {[m for m in dir(llm_client._client) if not m.startswith('_')]}")
                
                # Get the client to use (either llm_client or its _client attribute)
                client_to_use = llm_client._client if hasattr(llm_client, '_client') else llm_client
                logger.debug(f"Using client: {client_to_use}")
                logger.debug(f"Client type: {type(client_to_use).__name__}")
                
                # Log available methods on the client we're about to use
                available_methods = [m for m in dir(client_to_use) 
                                   if not m.startswith('_') and callable(getattr(client_to_use, m))]
                logger.debug(f"Available methods on client_to_use: {available_methods}")
                
                # Log the prompt we're about to send
                logger.debug(f"Sending prompt to LLM: {prompt[:200]}...")
                
                # Try using ainvoke first (for LangChain)
                if hasattr(client_to_use, 'ainvoke'):
                    logger.debug("Trying ainvoke method")
                    try:
                        logger.debug(f"Calling ainvoke with prompt: {prompt[:200]}...")
                        llm_response = await client_to_use.ainvoke(prompt)
                        logger.debug(f"ainvoke response type: {type(llm_response).__name__}")
                        logger.debug(f"ainvoke response: {str(llm_response)[:200]}...")
                        # Convert response to string if it's an object
                        if hasattr(llm_response, 'content'):
                            llm_response = llm_response.content
                            logger.debug("Extracted content from response object")
                        logger.debug("Successfully used ainvoke method")
                        logger.debug(f"Final llm_response type: {type(llm_response).__name__}")
                        logger.debug(f"Final llm_response: {str(llm_response)[:200]}...")
                    except Exception as e:
                        logger.error(f"Error in ainvoke: {str(e)}", exc_info=True)
                        llm_response = None
                
                # Try using invoke if available or if ainvoke failed
                if 'llm_response' not in locals() and hasattr(client_to_use, 'invoke'):
                    logger.debug("Trying invoke method")
                    try:
                        # Use run_in_executor to run synchronous code in a thread
                        import asyncio
                        from functools import partial
                        loop = asyncio.get_event_loop()
                        llm_response = await loop.run_in_executor(
                            None, 
                            partial(client_to_use.invoke, prompt)
                        )
                        logger.debug(f"invoke response type: {type(llm_response).__name__}")
                        if hasattr(llm_response, 'content'):
                            llm_response = llm_response.content
                        logger.debug("Successfully used invoke method")
                    except Exception as e:
                        logger.error(f"Error in invoke: {str(e)}", exc_info=True)
                        llm_response = None
                
                # Fall back to call_async for backward compatibility
                if 'llm_response' not in locals() and hasattr(client_to_use, 'call_async'):
                    logger.debug("Trying call_async method")
                    try:
                        llm_response = await client_to_use.call_async(prompt, is_json=True)
                        logger.debug(f"call_async response type: {type(llm_response).__name__}")
                        logger.debug("Successfully used call_async method")
                    except Exception as e:
                        logger.error(f"Error in call_async: {str(e)}", exc_info=True)
                        llm_response = None
                
                # Fall back to call if nothing else works
                if 'llm_response' not in locals() and hasattr(client_to_use, 'call'):
                    logger.debug("Trying call method")
                    try:
                        # Use run_in_executor for synchronous call method
                        import asyncio
                        loop = asyncio.get_event_loop()
                        llm_response = await loop.run_in_executor(
                            None, 
                            client_to_use.call,
                            prompt
                        )
                        logger.debug(f"call response type: {type(llm_response).__name__}")
                        logger.debug("Successfully used call method")
                    except Exception as e:
                        logger.error(f"Error in call: {str(e)}", exc_info=True)
                        llm_response = None
                
                # If we still don't have a response, log detailed error
                if 'llm_response' not in locals():
                    logger.error(f"No compatible LLM client method found. Available methods: {available_methods}")
                    logger.error(f"Client: {client_to_use}")
                    logger.error(f"Client type: {type(client_to_use).__name__}")
                    logger.error(f"Client dir: {[m for m in dir(client_to_use) if not m.startswith('_')]}")
                    logger.error(f"Client has __dict__: {hasattr(client_to_use, '__dict__')}")
                    if hasattr(client_to_use, '__dict__'):
                        logger.error(f"Client __dict__: {client_to_use.__dict__}")
                    return False, "❌ No compatible LLM client method found"
                
                # Log the raw response for debugging
                if hasattr(llm_response, 'generations') and llm_response.generations:
                    logger.debug(f"LLM response has {len(llm_response.generations)} generations")
                    for i, gen in enumerate(llm_response.generations):
                        logger.debug(f"Generation {i} type: {type(gen).__name__}")
                        if hasattr(gen[0], 'text'):
                            logger.debug(f"Generation {i} text: {gen[0].text[:200]}...")
                
                # Extract response text safely
                response_text = None
                try:
                    if hasattr(llm_response, 'generations') and llm_response.generations:
                        # Handle LangChain LLMResult format
                        response_text = llm_response.generations[0][0].text
                    elif hasattr(llm_response, 'content'):
                        # Handle direct content attribute
                        response_text = llm_response.content
                    elif isinstance(llm_response, str):
                        # Already a string
                        response_text = llm_response
                    elif hasattr(llm_response, '__str__'):
                        # Fallback to string representation
                        response_text = str(llm_response)
                    
                    logger.debug(f"Extracted response text: {response_text[:500]}...")
                    
                    # Parse response
                    command_data = self.response_parser.parse(response_text)
                    logger.debug(f"Parsed command data: {command_data}")
                    
                except Exception as parse_error:
                    logger.error(f"Error parsing LLM response: {str(parse_error)}")
                    logger.error(f"Response type: {type(llm_response).__name__}")
                    if hasattr(llm_response, '__dict__'):
                        logger.error(f"Response attributes: {llm_response.__dict__.keys()}")
                    raise ValueError(f"Failed to parse LLM response: {str(parse_error)}") from parse_error
                
            except Exception as e:
                error_msg = f"Error processing LLM response: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return False, f"❌ {error_msg}"
            
            # Execute command
            return await self._execute_command(command_data, cmd_context)
            
        except Exception as e:
            logger.error(f"Error processing command: {str(e)}", exc_info=True)
            return False, f"❌ Error processing command: {str(e)}"
    
    def _create_context(
        self,
        bot_data: Dict[str, Any],
        chat_id: str,
        user_id: str
    ) -> CommandContext:
        """Create and initialize command context."""
        # Initialize bot_data if needed
        if not isinstance(bot_data, dict):
            bot_data = {}
        
        # Ensure active_projects exists
        if 'active_projects' not in bot_data:
            bot_data['active_projects'] = {}
        
        # Get or initialize project manager
        if 'project_manager' not in bot_data:
            base_dir = Path(__file__).parent.parent.parent.absolute()
            bot_data['project_manager'] = ProjectManager(base_dir)
        
        # Get current project
        current_project = bot_data['active_projects'].get(chat_id)
        
        return CommandContext(
            chat_id=chat_id,
            user_id=user_id,
            bot_data=bot_data,
            project_manager=bot_data['project_manager'],
            current_project=current_project
        )
    
    async def _execute_command(
        self,
        command_data: Dict[str, Any],
        context: CommandContext
    ) -> Tuple[bool, str]:
        """Execute a command using the appropriate handler."""
        command_type = command_data.get('type')
        if not command_type:
            return False, "❌ No command type specified"
        
        handler = self.handlers.get(command_type)
        if not handler:
            return False, f"❌ Unknown command type: {command_type}"
        
        try:
            return await handler.handle(command_data, context)
        except Exception as e:
            logger.error(f"Error executing command {command_type}: {str(e)}", exc_info=True)
            return False, f"❌ Error executing command: {str(e)}"
