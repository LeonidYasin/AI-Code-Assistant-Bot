"""
Script to list all available GigaChat models.

This script demonstrates how to authenticate with the GigaChat API and list all available models.
"""
import os
import sys
import json
import logging
import urllib3
from dotenv import load_dotenv
from gigachat import GigaChat

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Get credentials from environment
    credentials = os.getenv("GIGACHAT_CREDENTIALS")
    if not credentials:
        logger.error("GIGACHAT_CREDENTIALS environment variable is not set")
        logger.info("Please set the GIGACHAT_CREDENTIALS environment variable with your API key")
        return 1
    
    logger.info("GIGACHAT_CREDENTIALS found in environment")
    
    try:
        # Initialize GigaChat client
        logger.info("Initializing GigaChat client...")
        try:
            giga = GigaChat(
                credentials=credentials,
                verify_ssl_certs=False,
                timeout=30
            )
            logger.info("GigaChat client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GigaChat client: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response headers: {dict(e.response.headers)}")
                try:
                    logger.error(f"Response body: {e.response.text}")
                except:
                    pass
            raise
        
        # Get available models
        logger.info("Fetching available models...")
        try:
            response = giga.get_models()
            
            # Log raw response
            logger.info("\n=== Raw Response ===")
            logger.info(f"Response type: {type(response)}")
            logger.info(f"Response attributes: {dir(response)}")
            
            # Try to get the raw data
            if hasattr(response, 'data'):
                logger.info(f"Response data type: {type(response.data)}")
                logger.info(f"Response data length: {len(response.data) if hasattr(response.data, '__len__') else 'N/A'}")
            
            # Try to get the first model to inspect its structure
            if hasattr(response, 'data') and response.data and len(response.data) > 0:
                first_model = response.data[0]
                logger.info(f"\nFirst model type: {type(first_model)}")
                logger.info(f"First model attributes: {dir(first_model)}")
                
                # Try common attribute names
                for attr in ['id', 'id_', 'model_id', 'name', 'model_name']:
                    if hasattr(first_model, attr):
                        logger.info(f"First model {attr}: {getattr(first_model, attr, 'N/A')}")
            
            # Pretty print the response
            logger.info("\n=== Available Models ===")
            if hasattr(response, 'data') and response.data:
                for i, model in enumerate(response.data, 1):
                    logger.info(f"\nModel #{i}")
                    # Try different possible attribute names
                    for attr_name in ['id', 'id_', 'model_id']:
                        if hasattr(model, attr_name):
                            logger.info(f"  ID: {getattr(model, attr_name, 'N/A')}")
                            break
                    else:
                        logger.info("  ID: N/A (no ID attribute found)")
                    
                    # Log other attributes
                    for attr_name in ['name', 'model_name']:
                        if hasattr(model, attr_name):
                            logger.info(f"  Name: {getattr(model, attr_name, 'N/A')}")
                    
                    logger.info(f"  Object Type: {type(model).__name__}")
                    
                    # Try to get any other interesting attributes
                    for attr in dir(model):
                        if not attr.startswith('_') and attr not in ['id', 'id_', 'model_id', 'name', 'model_name']:
                            try:
                                value = getattr(model, attr)
                                if not callable(value) and value is not None:
                                    logger.info(f"  {attr}: {value}")
                            except Exception as e:
                                logger.debug(f"Could not get attribute {attr}: {e}")
            else:
                logger.warning("No models found in the response")
                logger.info(f"Response type: {type(response)}")
                logger.info(f"Response attributes: {dir(response)}")
                
                # Try to get any available attributes
                for attr in dir(response):
                    if not attr.startswith('_') and attr != 'data':
                        try:
                            value = getattr(response, attr)
                            logger.info(f"{attr}: {value}")
                        except Exception as e:
                            logger.debug(f"Could not get attribute {attr}: {e}")
                            
        except Exception as e:
            logger.error(f"Failed to get models: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response headers: {dict(e.response.headers)}")
                try:
                    logger.error(f"Response body: {e.response.text}")
                except:
                    pass
            raise
        
        return 0
    
    except Exception as e:
        print(f"\nError: {str(e)}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
