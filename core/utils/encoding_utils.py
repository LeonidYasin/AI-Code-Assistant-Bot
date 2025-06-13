"""Utility functions for handling text encoding in the console."""
import sys
import os
import logging
from typing import Optional, TextIO

def setup_console_encoding():
    """Set up console encoding to properly handle Unicode output."""
    if sys.platform == 'win32':
        # Try to set console output to UTF-8 on Windows
        try:
            # Set console code page to UTF-8
            os.system('chcp 65001 > nul')
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except Exception as e:
            # If we can't change the console, we'll use the SafeConsoleWriter
            pass

class SafeConsoleWriter:
    """A file-like object that safely writes to the console, replacing unsupported characters."""
    
    def __init__(self, stream: TextIO):
        self.stream = stream
        self.encoding = 'utf-8'
        
    def write(self, text: str) -> int:
        try:
            return self.stream.write(text)
        except UnicodeEncodeError:
            # Replace unsupported characters with '?'
            cleaned = text.encode('utf-8', errors='replace').decode('utf-8')
            return self.stream.write(cleaned)
    
    def flush(self) -> None:
        self.stream.flush()

def safe_print(*args, **kwargs):
    """A safe print function that handles Unicode characters."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # If we can't print with the default settings, use our safe writer
        import sys
        safe_stdout = SafeConsoleWriter(sys.stdout)
        print(*args, **{**kwargs, 'file': safe_stdout})

def configure_logging():
    """Configure logging to handle Unicode characters."""
    class SafeLoggingHandler(logging.StreamHandler):
        def emit(self, record):
            try:
                super().emit(record)
            except UnicodeEncodeError:
                # Create a cleaned message
                record.msg = str(record.msg).encode('utf-8', errors='replace').decode('utf-8')
                if record.args:
                    record.args = tuple(
                        arg.encode('utf-8', errors='replace').decode('utf-8') 
                        if isinstance(arg, str) else arg 
                        for arg in record.args
                    )
                super().emit(record)

    # Replace the default handler with our safe handler
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        if isinstance(handler, logging.StreamHandler):
            root_logger.removeHandler(handler)
    
    handler = SafeLoggingHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
