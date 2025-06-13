"""Test script for HTTP request logging."""
import requests
import json
import logging
from pathlib import Path

# Configure logging for the test script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_http_requests.log', mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger('http_test')

def test_http_requests():
    """Test making HTTP requests and verify logging."""
    logger.info("Starting HTTP request test")
    
    try:
        # Test GET request with query parameters
        logger.info("Sending GET request to httpbin.org/get")
        response = requests.get(
            'https://httpbin.org/get',
            params={'test_param': 'test_value', 'foo': 'bar'},
            headers={'User-Agent': 'TestScript/1.0'}
        )
        logger.info(f"GET request completed with status: {response.status_code}")
        
        # Test POST request with JSON body
        logger.info("Sending POST request to httpbin.org/post")
        response = requests.post(
            'https://httpbin.org/post',
            json={'key': 'value', 'nested': {'a': 1, 'b': 2}},
            headers={
                'Content-Type': 'application/json',
                'X-Test-Header': 'test-value'
            }
        )
        logger.info(f"POST request completed with status: {response.status_code}")
        
        # Test error case
        logger.info("Sending request to non-existent endpoint")
        try:
            response = requests.get('https://httpbin.org/status/404')
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.warning(f"Expected error received: {e}")
        
        logger.info("HTTP request test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    # Import the config to apply HTTP request logging
    from core.bot import config
    
    print("Starting HTTP request logging test...")
    success = test_http_requests()
    
    if success:
        print("\nTest completed successfully!")
        print(f"Check the following log files for details:")
        print(f"- {Path('test_http_requests.log').resolve()}")
        print(f"- {Path('logs/http_requests.log').resolve()}")
    else:
        print("\nTest failed. Check the logs for details.")
    
