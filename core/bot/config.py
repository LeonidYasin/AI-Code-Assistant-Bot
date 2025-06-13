"""Bot configuration module with logging setup."""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union

# Import dotenv only when needed
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    
# Import other heavy dependencies only when needed
REQUESTS_IMPORTED = False
if not any('pytest' in arg for arg in sys.argv):
    try:
        import requests
        import http.client
        import urllib3
        REQUESTS_IMPORTED = True
    except ImportError:
        pass

# Set up logging directory
LOG_DIR = Path('logs')
LOG_DIR.mkdir(exist_ok=True)

# Configure root logger with detailed format including file and line number
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / 'bot.log', encoding='utf-8')
    ]
)

# Create a logger for this module
logger = logging.getLogger(__name__)
logger.info("Logging configuration complete")

# Load environment variables if dotenv is available
if DOTENV_AVAILABLE:
    load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logger.warning("BOT_TOKEN environment variable is not set - running in CLI mode")
    BOT_TOKEN = "cli_mode_token"  # Use a placeholder token for CLI mode
    
# LLM configuration
LLM_ENABLED = os.getenv('LLM_ENABLED', 'false').lower() == 'true'

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'detailed',
            'stream': 'ext://sys.stdout',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': str(LOG_DIR / 'bot.log'),
            'mode': 'a',
            'encoding': 'utf-8',
            'level': 'DEBUG',
            'formatter': 'detailed',
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'http.client': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'urllib3': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / 'http_requests.log', encoding='utf-8')
    ]
)

logger = logging.getLogger('http_tracker')

# Store original request methods
_original_request = requests.Session.request
_original_http_connect = http.client.HTTPConnection.connect

# Patch http.client to log connections
class LoggingHTTPConnection(http.client.HTTPConnection):
    def connect(self):
        logger.debug(f"Connecting to {self.host}:{self.port}")
        _original_http_connect(self)

# Patch requests.Session.request
def patched_request(self, method, url, **kwargs):
    # Log the request
    logger.debug(f"Request: {method} {url}")
    
    # Log headers if present
    if 'headers' in kwargs and kwargs['headers']:
        logger.debug(f"Headers: {json.dumps(dict(kwargs['headers']), indent=2)}")
    
    # Log body if present
    if 'data' in kwargs and kwargs['data']:
        logger.debug(f"Request body: {kwargs['data']}")
    
    # Make the request
    response = _original_request(self, method, url, **kwargs)
    
    # Log the response
    logger.debug(f"Response: {response.status_code} {response.reason}")
    logger.debug(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")
    
    # Log response body if it's not too large
    try:
        if 'application/json' in response.headers.get('Content-Type', ''):
            logger.debug(f"Response JSON: {response.json()}")
        else:
            logger.debug(f"Response text: {response.text[:1000]}")
    except Exception as e:
        logger.debug(f"Could not log response body: {e}")
    
    return response

# Apply the patches
http.client.HTTPConnection = LoggingHTTPConnection
requests.Session.request = patched_request

# Also patch the main requests functions
for method in ('get', 'post', 'put', 'delete', 'head', 'options'):
    setattr(requests, method, lambda *args, **kwargs: requests.request(method.upper(), *args, **kwargs))

logger.info("HTTP request logging has been enabled")

class HTTPRequestLogger:
    """Logs HTTP requests and responses with detailed information."""
    
    @staticmethod
    def get_caller_info() -> Dict[str, Any]:
        """Get information about the caller that made the HTTP request."""
        frame = inspect.currentframe()
        try:
            # Walk up the call stack to find the first frame not in this module
            while frame:
                frame = frame.f_back
                if not frame:
                    break
                    
                module = inspect.getmodule(frame)
                if not module or not module.__name__.startswith('urllib3'):
                    # Found a frame outside of urllib3, this is likely our caller
                    return {
                        'filename': frame.f_code.co_filename,
                        'lineno': frame.f_lineno,
                        'function': frame.f_code.co_name,
                        'module': module.__name__ if module else 'unknown'
                    }
            return {}
        finally:
            del frame  # Avoid reference cycles

    @classmethod
    def log_request(cls, method: str, url: str, headers: Optional[Dict] = None, body: Optional[bytes] = None) -> None:
        """Log an HTTP request."""
        caller = cls.get_caller_info()
        logger = logging.getLogger('http.client')
        
        log_data = {
            'event': 'http_request',
            'method': method,
            'url': url,
            'headers': dict(headers) if headers else {},
            'body': body.decode('utf-8', errors='replace') if body else None,
            'caller': caller
        }
        
        logger.debug(json.dumps(log_data, indent=2, ensure_ascii=False))

    @classmethod
    def log_response(cls, response: 'requests.Response') -> None:
        """Log an HTTP response."""
        logger = logging.getLogger('http.client')
        
        try:
            content_type = response.headers.get('Content-Type', '')
            is_json = 'application/json' in content_type
            
            log_data = {
                'event': 'http_response',
                'status_code': response.status_code,
                'url': response.url,
                'headers': dict(response.headers),
                'elapsed': response.elapsed.total_seconds(),
                'content_type': content_type
            }
            
            # Log response body if it's not too large
            if is_json:
                try:
                    log_data['json'] = response.json()
                except:
                    log_data['text'] = response.text[:1000] + '...' if len(response.text) > 1000 else response.text
            else:
                log_data['text'] = response.text[:1000] + '...' if len(response.text) > 1000 else response.text
            
            logger.debug(json.dumps(log_data, indent=2, ensure_ascii=False))
            
        except Exception as e:
            logger.error(f"Error logging response: {e}", exc_info=True)

class LoggingHTTPAdapter(requests.adapters.HTTPAdapter):
    """Custom HTTP adapter that logs all requests and responses."""
    
    def send(self, request, **kwargs):
        # Log the request
        HTTPRequestLogger.log_request(
            method=request.method,
            url=request.url,
            headers=request.headers,
            body=request.body
        )
        
        # Send the request
        response = super().send(request, **kwargs)
        
        # Log the response
        HTTPRequestLogger.log_response(response)
        
        return response

# Ensure logs directory exists
LOG_DIR = Path('logs')
LOG_DIR.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / 'http_requests.log', encoding='utf-8')
    ]
)

# Configure requests to use our logging adapter
session = requests.Session()
adapter = LoggingHTTPAdapter()
session.mount('http://', adapter)
session.mount('https://', adapter)

# Patch requests to use our session
def patch_requests():
    """Patch the requests module to use our custom session."""
    def patched_request(method, url, **kwargs):
        return session.request(method=method, url=url, **kwargs)
    
    # Patch the main request methods
    for method in ('get', 'post', 'put', 'delete', 'head', 'options', 'patch'):
        setattr(requests, method, lambda *args, **kwargs: patched_request(method.upper(), *args, **kwargs))
    
    # Also patch the session methods
    requests.Session = type('PatchedSession', (requests.Session,), {
        'request': lambda self, method, url, **kwargs: patched_request(method, url, **kwargs)
    })

# Apply the patch
patch_requests()

# Enable HTTP request logging
http.client.HTTPConnection.debuglevel = 1
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging for all HTTP-related loggers
http_loggers = [
    'requests',
    'urllib3',
    'http.client',
    'urllib3.connectionpool',
    'urllib3.connection',
    'urllib3.util.retry',
    'urllib3.util.connection',
    'urllib3.poolmanager',
    'urllib3.response',
    'urllib3.util.ssl_',
    'urllib3.util.timeout',
    'urllib3.util.url'
]

# Create and configure loggers
for logger_name in http_loggers:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    
    # Add handler if not already added
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('HTTP REQUEST: %(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)

# Enable HTTP request debugging
import http.client as http_client
http_client.HTTPConnection.debuglevel = 1

# Configure requests to use urllib3
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure session with retry strategy
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[408, 429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

# Override the default requests methods to use our session
original_get = requests.get
original_post = requests.post

def patched_request(method, *args, **kwargs):
    return session.request(method=method, *args, **kwargs)

# Patch the requests methods
requests.get = lambda *args, **kwargs: patched_request('GET', *args, **kwargs)
requests.post = lambda *args, **kwargs: patched_request('POST', *args, **kwargs)

# Load environment variables
load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DEFAULT_CHAT_ID = 12345  # Default chat ID for CLI commands

# File paths
BASE_DIR = Path(__file__).parent.parent.parent
LOG_DIR = BASE_DIR / 'logs'

# Ensure log directory exists
LOG_DIR.mkdir(exist_ok=True)

# Enhanced logging formatter that includes file and line number
class RequestFormatter(logging.Formatter):
    def format(self, record):
        # Add file and line number to the log record
        if not hasattr(record, 'pathname'):
            record.pathname = ''
        if not hasattr(record, 'lineno'):
            record.lineno = 0
        
        # Get the last frame that's not in the logging module
        frame = None
        f = logging.currentframe()
        while f:
            if f.f_globals.get('__name__', '').startswith('http'):
                frame = f
                break
            f = f.f_back
        
        if frame is not None:
            # Get the frame where the request was made
            while f and 'site-packages' in frame.f_code.co_filename:
                f = f.f_back
            
            if f:
                record.pathname = f.f_code.co_filename
                record.lineno = f.f_lineno
        
        return super().format(record)

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            '()': RequestFormatter,
            'format': '%(asctime)s - %(pathname)s:%(lineno)d - %(name)s - %(levelname)s - %(message)s'
        },
        'request': {
            '()': RequestFormatter,
            'format': 'REQUEST: %(asctime)s - %(pathname)s:%(lineno)d - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': 'INFO',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'bot.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'standard',
            'level': 'DEBUG',
        },
        'request_console': {
            'class': 'logging.StreamHandler',
            'formatter': 'request',
            'level': 'DEBUG',
            'stream': 'ext://sys.stdout'
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True
        },
        'http.client': {
            'handlers': ['request_console', 'file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'urllib3.connectionpool': {
            'handlers': ['request_console', 'file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'telegram': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False
        },
    }
}
