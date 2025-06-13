"""Test script for HTTP request logging with file and line number info."""
import requests
import logging
from pathlib import Path

# Configure logging to show file and line numbers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_http_requests.log', mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger('http_test')

def make_get_request():
    """Make a GET request to httpbin."""
    logger.info("Making GET request to httpbin.org/get")
    response = requests.get(
        'https://httpbin.org/get',
        params={'test': 'value'},
        headers={'User-Agent': 'TestScript/1.0'}
    )
    logger.info(f"GET request completed with status: {response.status_code}")
    return response

def make_post_request():
    """Make a POST request to httpbin."""
    logger.info("Making POST request to httpbin.org/post")
    response = requests.post(
        'https://httpbin.org/post',
        json={'key': 'value'},
        headers={'Content-Type': 'application/json'}
    )
    logger.info(f"POST request completed with status: {response.status_code}")
    return response

def test_http_requests():
    """Test making HTTP requests and verify logging."""
    logger.info("Starting HTTP request test")
    
    try:
        # Make requests from different functions to test line numbers
        make_get_request()
        make_post_request()
        
        logger.info("HTTP request test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    # Import config to apply HTTP request logging
    from core.bot import config
    
    print("Starting HTTP request logging test...")
    print("Check the console output for file and line number information.")
    
    success = test_http_requests()
    
    if success:
        print("\nTest completed successfully!")
        print(f"Check {Path('test_http_requests.log').resolve()} for detailed logs.")
    else:
        print("\nTest failed. Check the logs for details.")
