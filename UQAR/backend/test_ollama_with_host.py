import sys
sys.path.append('.')
from app.services.ollama_service import OllamaService
import asyncio
import httpx
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

async def test_ollama_connection():
    # Try different hostnames to see which one works
    hosts_to_try = ["127.0.0.1", "localhost", "ollama", "10.0.30.51"]
    port = 11434
    
    for host in hosts_to_try:
        base_url = f"http://{host}:{port}"
        logger.info(f"Testing connection to Ollama at {base_url}")
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                try:
                    response = await client.get(f"{base_url}/api/version")
                    if response.status_code == 200:
                        logger.info(f"✓ Successfully connected to {base_url}/api/version")
                        version_info = response.json()
                        logger.info(f"   Version: {version_info.get('version', 'unknown')}")
                        
                        # Now check for available models
                        try:
                            models_response = await client.get(f"{base_url}/api/tags")
                            if models_response.status_code == 200:
                                models_data = models_response.json()
                                models = [model.get("name") for model in models_data.get("models", [])]
                                if models:
                                    logger.info(f"✓ Available models at {host}: {', '.join(models)}")
                                    if "llama3.1:70b" in models:
                                        logger.info("✓ Required model 'llama3.1:70b' is available!")
                                    else:
                                        logger.warning("✗ Required model 'llama3.1:70b' is NOT available")
                                else:
                                    logger.warning(f"No models found at {host}")
                            else:
                                logger.error(f"Failed to get models list: {models_response.status_code}")
                        except Exception as e:
                            logger.error(f"Error checking models: {e}")
                            
                    else:
                        logger.error(f"✗ Failed to connect to {base_url}/api/version: {response.status_code}")
                except Exception as e:
                    logger.error(f"✗ Connection error for {base_url}: {e}")
        except Exception as e:
            logger.error(f"✗ Failed to test {base_url}: {e}")
    
    # Now test with OllamaService
    service = OllamaService()
    logger.info(f"\nTesting OllamaService with base_url={service.base_url}")
    
    # Override the base_url
    service.base_url = "http://ollama:11434"
    logger.info(f"Overriding base_url to {service.base_url}")
    
    try:
        health_result = await service.health_check()
        logger.info(f"Health check result: {health_result}")
        
        if not health_result:
            # Try generating a response anyway to see the error
            try:
                response = await service.generate_response("Qu'est-ce que l'intelligence artificielle?")
                logger.info(f"Got response even though health check failed: {response[:100]}...")
            except Exception as e:
                logger.error(f"Failed to generate response: {e}")
    except Exception as e:
        logger.error(f"Error in health check: {e}")

if __name__ == "__main__":
    asyncio.run(test_ollama_connection()) 