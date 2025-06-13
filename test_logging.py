"""Test script to verify logging configuration with file and line numbers."""
import logging
import requests
from pathlib import Path

# Get the logger for this module
logger = logging.getLogger(__name__)

def make_http_request():
    """Make an HTTP request to test logging."""
    logger.info("Making HTTP request to httpbin.org/get")
    try:
        response = requests.get('https://httpbin.org/get', params={'test': 'value'})
        logger.info(f"Received response with status code: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Error making HTTP request: {e}", exc_info=True)
        raise

def main():
    """Main test function."""
    logger.info("Starting logging test")
    
    # Test different log levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    
    # Make an HTTP request to test HTTP client logging
    try:
        response = make_http_request()
        logger.info(f"Test completed successfully. Response length: {len(response.text)} bytes")
    except Exception as e:
        logger.error("Test failed with error", exc_info=True)
        return False
    
    return True

if __name__ == "__main__":
    # Import the config to set up logging
    from core.bot import config
    
    print("Starting logging test...")
    success = main()
    
    if success:
        print("\nTest completed successfully!")
        print(f"Check {Path('logs/bot.log').resolve()} for detailed logs.")
    else:
        print("\nTest failed. Check the logs for details.")
