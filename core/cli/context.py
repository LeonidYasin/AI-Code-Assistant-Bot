"""
CLI context and related utilities.
"""

class CLIContext:
    """Simple context class for CLI mode."""
    def __init__(self, llm_enabled=False):
        self.bot_data = {}
        self._chat_id = 0
        self.args = []
        # Initialize project manager with LLM disabled for CLI by default
        from core.project.manager import ProjectManager
        self.project_manager = ProjectManager(llm_enabled=llm_enabled)
    
    async def reply_text(self, text: str, parse_mode: str = None, **kwargs) -> None:
        """Print text to console for CLI mode."""
        print(text)
