"""Simple test script to verify basic logging functionality."""
import logging
import sys
from pathlib import Path

# Set up basic logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test.log', mode='w', encoding='utf-8')
    ]
)

# Get logger for this module
logger = logging.getLogger(__name__)

def test_logging():
    """Test logging at different levels."""
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    try:
        # Generate a division by zero error
        result = 1 / 0
    except Exception as e:
        logger.exception("An error occurred:")
    
    return True

if __name__ == "__main__":
    print("Starting logging test...")
    success = test_logging()
    
    if success:
        print("\nTest completed successfully!")
        print(f"Check {Path('test.log').resolve()} for detailed logs.")
    else:
        print("\nTest failed. Check the logs for details.")
