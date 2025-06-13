"""Test script for HTTP request logging."""
import requests
from core.bot.config import http_logger

def test_http_requests():
    """Test making HTTP requests and verify logging."""
    http_logger.info("Starting HTTP request test")
    
    # Test GET request
    response = requests.get('https://httpbin.org/get', params={'test': 'value'})
    http_logger.info(f"GET request status: {response.status_code}")
    
    # Test POST request with JSON
    response = requests.post(
        'https://httpbin.org/post',
        json={'key': 'value'},
        headers={'X-Test-Header': 'test-value'}
    )
    http_logger.info(f"POST request status: {response.status_code}")
    
    http_logger.info("HTTP request test completed")

if __name__ == "__main__":
    test_http_requests()
    print("Test completed. Check logs/http_requests.log for details.")
