"""
Utility functions for LLM providers.
"""

import logging
from typing import Any, Dict, Optional
from models import ModelProvider, OllamaProvider, GeminiProvider, GroqProvider
from prompt import MODEL_PROVIDER_MAPPING, GEMINI_API_KEY, GROQ_API_KEY

logger = logging.getLogger(__name__)


import re

def extract_json_from_response(response_text: str) -> str:
    """
    Extract JSON content from markdown code blocks or the raw response.
    """
    response_text = response_text.strip()
    
    # Handle <think> blocks (DeepSeek/Thinking models)
    if "<think>" in response_text:
        response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL).strip()

    # Try to find JSON in markdown code blocks
    json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
    if json_match:
        return json_match.group(1).strip()
    
    # Try generic code block if json block not found
    code_match = re.search(r'```\s*(.*?)\s*```', response_text, re.DOTALL)
    if code_match:
        return code_match.group(1).strip()

    # If no code blocks, look for first { and last }
    bracket_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
    if bracket_match:
        return bracket_match.group(1).strip()

    return response_text


def initialize_llm_provider(model_name: str, api_key: Optional[str] = None) -> Any:
    """
    Initialize the appropriate LLM provider based on the model name.

    Args:
        model_name: The name of the model to use
        api_key: Optional API key to use (overrides environment variable)

    Returns:
        An initialized LLM provider (either OllamaProvider, GeminiProvider, or GroqProvider)
    """
    # Default to Groq provider
    model_provider = MODEL_PROVIDER_MAPPING.get(model_name, ModelProvider.GROQ)

    if model_provider == ModelProvider.GEMINI:
        key = api_key or GEMINI_API_KEY
        if not key:
            logger.warning("⚠️ Gemini API key not found.")
            provider = GeminiProvider(api_key="")
        else:
            logger.info(f"🔄 Using Google Gemini API provider with model {model_name}")
            provider = GeminiProvider(api_key=key)
    elif model_provider == ModelProvider.GROQ:
        key = api_key or GROQ_API_KEY
        if not key:
            logger.warning("⚠️ Groq API key not found.")
            provider = GroqProvider(api_key="")
        else:
            logger.info(f"🔄 Using Groq API provider with model {model_name}")
            provider = GroqProvider(api_key=key)
    else:
        logger.info(f"🔄 Using Ollama provider with model {model_name}")
        provider = OllamaProvider()
    return provider

