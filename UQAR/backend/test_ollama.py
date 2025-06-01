#!/usr/bin/env python3
import asyncio
import logging
from app.services.ollama_service import OllamaService
from app.core.config import get_ollama_config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ollama():
    """Test Ollama connectivity directly"""
    logger.info("Testing Ollama service directly...")
    
    # Print Ollama config
    config = get_ollama_config()
    logger.info(f"Ollama config: {config}")
    
    # Test Ollama
    ollama = OllamaService()
    logger.info(f"Ollama service initialized with model: {ollama.model}")
    
    # Check health
    is_healthy = await ollama.health_check()
    logger.info(f"Ollama health check: {'PASSED' if is_healthy else 'FAILED'}")
    
    # Test response
    if is_healthy:
        response = await ollama.generate_response("Bonjour, qu'est-ce que l'intelligence artificielle?")
        logger.info(f"Ollama response: {response[:200]}...")
    else:
        logger.error("Skipping response test because Ollama is not healthy")

async def main():
    """Run all tests"""
    logger.info("Starting tests...")
    
    await test_ollama()
    
    logger.info("Tests completed")

if __name__ == "__main__":
    asyncio.run(main()) 