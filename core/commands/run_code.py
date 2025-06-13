"""
Command for running Python code and analyzing its output with LLM.
"""
import asyncio
import datetime
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from telegram import Update
from telegram.ext import CallbackContext, ContextTypes

from core.llm.client import LLMClient
from core.project.manager import ProjectManager
from core.utils.formatting import code_block

logger = logging.getLogger(__name__)

class CodeRunner:
    """Handles running Python code and analyzing its output."""
    
    def __init__(self, project_manager: ProjectManager, llm_client: LLMClient):
        """Initialize the code runner."""
        self.project_manager = project_manager
        self.llm_client = llm_client
    
    async def run_code(
        self, 
        code: str, 
        project_name: Optional[str] = None,
        analyze: bool = True
    ) -> Tuple[bool, str]:
        """
        Run Python code and optionally analyze its output.
        
        Args:
            code: Python code to execute
            project_name: Optional project name to run the code in
            analyze: Whether to analyze the output with LLM
            
        Returns:
            Tuple of (success, result_message)
        """
        # Get the project path
        try:
            project_path = self.project_manager.get_project_path(project_name)
            if not project_path or not project_path.exists():
                return False, f"❌ Project '{project_name}' not found or invalid path: {project_path}"
            
            # Ensure the project directory exists and is writable
            project_path.mkdir(parents=True, exist_ok=True)
            
            # Create a temporary file with a more descriptive name for debugging
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_file_path = project_path / f"temp_code_{timestamp}.py"
            
            # Write the code to the file with error handling
            try:
                temp_file_path.write_text(code, encoding='utf-8')
                logger.info(f"Code written to temporary file: {temp_file_path}")
            except Exception as e:
                return False, f"❌ Failed to write code to temporary file: {str(e)}"
            
            try:
                # Run the code with a timeout
                process = await asyncio.create_subprocess_exec(
                    sys.executable,  # Use the current Python interpreter
                    str(temp_file_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(project_path),
                    env=dict(os.environ, PYTHONPATH=str(project_path))
                )
                
                # Get the output with a timeout
                try:
                    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
                    stdout = stdout.decode('utf-8', errors='replace').strip()
                    stderr = stderr.decode('utf-8', errors='replace').strip()
                    return_code = process.returncode
                    
                except asyncio.TimeoutError:
                    process.terminate()
                    await asyncio.sleep(1)  # Give it a moment to terminate
                    if process.returncode is None:  # Still running
                        process.kill()
                    return False, "❌ Code execution timed out after 30 seconds"
                
                # Prepare the result
                result_parts = []
                
                if return_code != 0:
                    result_parts.append(f"❌ Process exited with code {return_code}")
                
                if stdout:
                    result_parts.append(f"💻 Output:\n{code_block(stdout, 'python')}")
                
                if stderr:
                    result_parts.append(f"❌ Errors:\n{code_block(stderr, 'python')}")
                
                if not (stdout or stderr):
                    result_parts.append("ℹ️ No output was produced.")
                
                # Analyze the output if requested and we have an LLM client
                if analyze and self.llm_client:
                    try:
                        analysis = await self.analyze_output(code, stdout, stderr)
                        result_parts.append(f"\n🔍 Analysis:\n{analysis}")
                    except Exception as e:
                        logger.error(f"Error during LLM analysis: {e}", exc_info=True)
                        result_parts.append("\n⚠️ Failed to analyze output with LLM.")
                
                return return_code == 0, "\n".join(result_parts)
                
            except Exception as e:
                logger.error(f"Error executing code: {e}", exc_info=True)
                return False, f"❌ Error executing code: {str(e)}"
            
            finally:
                # Always clean up the temporary file
                try:
                    temp_file_path.unlink(missing_ok=True)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {temp_file_path}: {e}")
                    
        except Exception as e:
            logger.error(f"Unexpected error in run_code: {e}", exc_info=True)
            return False, f"❌ Unexpected error: {str(e)}"
    
    async def analyze_output(self, code: str, stdout: str, stderr: str) -> str:
        """Analyze the code execution output using LLM."""
        # Prepare the prompt with proper escaping
        try:
            # Create a clean version of the code and output for the prompt
            clean_code = code.strip()
            clean_stdout = stdout.strip()
            clean_stderr = stderr.strip()
            
            # Build the prompt with f-strings to avoid .format() issues
            prompt = f"""
Analyze the following Python code and its execution output.

Code:
```python
{clean_code}
```

Output:
```
{clean_stdout}
"""
            
            # Only include Errors section if there are any errors
            if clean_stderr:
                prompt += f"""
Errors:
```
{clean_stderr}
```
"""
            
            # Add analysis instructions
            prompt += """
Please analyze:
1. Any errors or exceptions that occurred
2. Potential issues with the code
3. Suggestions for improvement
4. Any security or performance concerns
"""
            
            logger.debug("Sending prompt to LLM for analysis...")
            
            # Check if the client's call method is async
            import inspect
            is_async = inspect.iscoroutinefunction(self.llm_client.call)
            
            # Call the appropriate method based on whether it's async or not
            if is_async:
                response = await self.llm_client.call(
                    prompt=prompt,
                    max_tokens=1000,
                    temperature=0.3
                )
            else:
                # Handle synchronous call
                import asyncio
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.llm_client.call(
                        prompt=prompt,
                        max_tokens=1000,
                        temperature=0.3
                    )
                )
            
            # Clean up the response
            if response:
                if hasattr(response, 'strip'):
                    response = response.strip()
                else:
                    # Handle case where response is not a string
                    response = str(response).strip()
                
                # Remove any markdown code blocks from the response
                response_str = str(response)
                if response_str.startswith('```') and response_str.endswith('```'):
                    response_str = response_str[3:-3].strip()
                    if '\n' in response_str:
                        response_str = response_str[response_str.find('\n')+1:].strip()
                return response_str
            
            return "No analysis available."
            
        except Exception as e:
            logger.error(f"Error in analyze_output: {str(e)}", exc_info=True)
            return f"⚠️ Could not analyze the output: {str(e)}"

async def execute_run_code(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE,
    args: List[str],
    project_manager: ProjectManager,
    llm_client: LLMClient
) -> None:
    """Execute the run_code command."""
    if not args:
        await update.message.reply_text(
            "Please provide Python code to execute.\n"
            "Example: /run_code 'print(\"Hello, World!\")'"
        )
        return
    
    # Join all arguments as the code
    code = ' '.join(args)
    
    # If the code is in a code block, extract it
    if '```' in code:
        # Extract code from markdown code block
        code_parts = code.split('```')
        if len(code_parts) >= 2:
            code = '\n'.join(code_parts[1].split('\n')[1:])  # Remove the first line (usually 'python')
    
    # Get the project name from context if available
    project_name = None
    if hasattr(context.bot_data, 'current_project'):
        project_name = context.bot_data.current_project
    
    # Create the code runner
    runner = CodeRunner(project_manager, llm_client)
    
    # Send a typing action to show the bot is working
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action='typing'
    )
    
    # Run the code
    success, result = await runner.run_code(
        code=code,
        project_name=project_name,
        analyze=True
    )
    
    # Send the result
    await update.message.reply_text(result, parse_mode='Markdown')
