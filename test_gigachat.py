import logging
from core.llm.client import llm_client
from config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_gigachat():
    try:
        # Initialize the client
        llm_client.initialize(use_gigachat=True)
        logger.info("LLM client initialized successfully with Gigachat")
        
        # Test a simple prompt
        test_prompt = "Привет! Как дела?"
        logger.info(f"Sending test prompt: {test_prompt}")
        
        response = llm_client.call(test_prompt)
        logger.info(f"Response from Gigachat: {response}")
        
        return True
    except Exception as e:
        logger.error(f"Error testing Gigachat: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    if test_gigachat():
        print("✅ Gigachat test completed successfully!")
    else:
        print("❌ Gigachat test failed. Check the logs for details.")
