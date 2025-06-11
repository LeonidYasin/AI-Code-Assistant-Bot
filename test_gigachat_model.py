"""Test script to check GigaChat model configuration."""
import os
import sys
import json
from dotenv import load_dotenv
from gigachat import GigaChat

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f" {title}".ljust(80, "="))
    print("=" * 80)

def test_gigachat_connection():
    """Test GigaChat connection and model information."""
    try:
        # Get credentials from environment
        credentials = os.getenv("GIGACHAT_CREDENTIALS")
        if not credentials:
            print("[ERROR] GIGACHAT_CREDENTIALS not found in environment variables")
            return
            
        print_section("TESTING GIGACHAT CONNECTION")
        print("Using credentials from GIGACHAT_CREDENTIALS environment variable")
        
        # Initialize with different model names to test
        model_names = ["GigaChat-Lite", "GigaChat-2-Max", "GigaChat", "GigaChat-Pro"]
        
        for model_name in model_names:
            try:
                print(f"\n[TEST] Trying model: {model_name}")
                
                # Initialize client with current model
                client = GigaChat(
                    credentials=credentials,
                    model=model_name,
                    verify_ssl_certs=False,
                    timeout=10,
                    profanity_check=False,
                    streaming=False
                )
                
                # Test connection
                print("  [OK] Client initialized successfully")
                print(f"  Model in client: {getattr(client, 'model', 'unknown')}")
                
                # Get model info if possible
                try:
                    models = client.get_models()
                    print("  [INFO] Available models:")
                    for model in models.data:
                        print(f"    - {model.id} (owned_by: {getattr(model, 'owned_by', 'N/A')})")
                except Exception as e:
                    print(f"  [WARN] Could not get available models: {e}")
                
                # Try a simple completion
                try:
                    print("  [TEST] Sending test message...")
                    response = client.chat([{"role": "user", "content": "Привет! Какая у тебя модель?"}])
                    
                    print("  [SUCCESS] Response received!")
                    print(f"  Model used: {getattr(response, 'model', 'unknown')}")
                    if hasattr(response, 'choices') and response.choices:
                        print(f"  Response: {response.choices[0].message.content[:200]}...")
                    
                    # Print full response if needed
                    print("\n  [DEBUG] Full response structure:")
                    print(f"  {json.dumps(vars(response), indent=2, default=str)}")
                    
                    return  # Stop after first successful test
                    
                except Exception as e:
                    print(f"  [ERROR] During chat completion: {e}")
                    import traceback
                    print(traceback.format_exc())
                
            except Exception as e:
                print(f"  [ERROR] Initializing with model '{model_name}': {e}")
    
    except Exception as e:
        print(f"[CRITICAL] Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gigachat_connection()
