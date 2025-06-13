"""
LLM Operations Module

This module handles all LLM-related operations for the project manager.
It provides a clean interface for the ProjectManager to interact with LLM
functionality without directly initializing the LLM client.
"""
import logging
from typing import Any, Dict, Optional, Tuple, List

logger = logging.getLogger(__name__)

class LLMOperations:
    """Handles all LLM-related operations with lazy initialization."""
    
    def __init__(self, enabled: bool = True):
        """
        Initialize the LLM operations handler.
        
        Args:
            enabled: If False, all LLM operations will be disabled.
        """
        self._enabled = enabled
        self._llm_client = None
        
    def _ensure_initialized(self) -> bool:
        """Ensure the LLM client is initialized if enabled."""
        if not self._enabled:
            return False
            
        if self._llm_client is None:
            try:
                from core.llm.client import llm_client
                self._llm_client = llm_client
                # Initialize with default settings
                self._llm_client.initialize()
                return True
            except Exception as e:
                logger.error(f"Failed to initialize LLM client: {e}")
                return False
        return True
    
    def analyze_code(self, code: str, context: Dict[str, Any] = None) -> Tuple[bool, str]:
        """
        Analyze code using the LLM.
        
        Args:
            code: The code to analyze
            context: Additional context for the analysis
            
        Returns:
            Tuple of (success, result)
        """
        if not self._ensure_initialized():
            return False, "LLM is disabled or failed to initialize"
            
        try:
            # Example implementation - adjust based on your actual LLM client API
            prompt = self._create_analysis_prompt(code, context or {})
            result = self._llm_client.generate(prompt)
            return True, result
        except Exception as e:
            logger.error(f"Error analyzing code: {e}")
            return False, f"Error analyzing code: {str(e)}"
    
    def _create_analysis_prompt(self, code: str, context: Dict[str, Any]) -> str:
        """Create a prompt for code analysis."""
        # Customize this method based on your needs
        return f"""
        Analyze the following code and provide feedback:
        
        ```python
        {code}
        ```
        
        Context: {context}
        """
    
    def is_enabled(self) -> bool:
        """Check if LLM operations are enabled."""
        return self._enabled and self._llm_client is not None
