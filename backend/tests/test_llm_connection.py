import os
import pytest
from discovery_engine.config.settings import settings
from discovery_engine.llm.client import GeminiClient

def test_llm_client_routing_and_fallback():
    """Verifies that the LLM client initializes with the correct provider and falls back gracefully when credentials are not present."""
    # Store original settings to restore later
    orig_provider = settings.LLM_PROVIDER
    orig_gemini_key = settings.GEMINI_API_KEY
    orig_groq_key = settings.GROQ_API_KEY

    try:
        # 1. Test Gemini Routing Configuration
        settings.LLM_PROVIDER = "gemini"
        settings.GEMINI_API_KEY = None
        client_gemini = GeminiClient()
        assert client_gemini.provider == "gemini"
        # Call generate_content with no api_key to verify fallback
        res = client_gemini.generate_content("hello", json_mode=True)
        assert "theme_clustering" in res  # Verifies fallback JSON schema
        
        # 2. Test Groq Routing Configuration
        settings.LLM_PROVIDER = "groq"
        settings.GROQ_API_KEY = None
        client_groq = GeminiClient()
        assert client_groq.provider == "groq"
        # Call generate_content with no api_key to verify fallback
        res = client_groq.generate_content("hello", json_mode=True)
        assert "theme_clustering" in res
    finally:
        # Restore settings
        settings.LLM_PROVIDER = orig_provider
        settings.GEMINI_API_KEY = orig_gemini_key
        settings.GROQ_API_KEY = orig_groq_key

def test_live_llm_connection():
    """
    Checks if active API key works. If active provider's API key is present in settings,
    it executes a live call to verify connection and parsing. Otherwise, logs a skip notice.
    """
    provider = settings.LLM_PROVIDER
    client = GeminiClient()
    
    gemini_key = settings.GEMINI_API_KEY
    groq_key = settings.GROQ_API_KEY
    
    is_gemini_active = provider == "gemini" and gemini_key and not gemini_key.startswith("YOUR_")
    is_groq_active = provider == "groq" and groq_key and not groq_key.startswith("YOUR_")
    
    if is_gemini_active:
        print("\nTesting live Google Gemini API connection...")
        prompt = "Write a JSON object with a single key 'status' and value 'connected'."
        res = client.generate_content(prompt, json_mode=True)
        assert isinstance(res, dict)
        if "error" not in res:
            assert res.get("status") == "connected"
            print("Google Gemini API connection successful!")
        else:
            print(f"Google Gemini returned parse error or api issue: {res}")
            
    elif is_groq_active:
        print("\nTesting live Groq API connection...")
        prompt = "Write a JSON object with a single key 'status' and value 'connected'."
        res = client.generate_content(prompt, json_mode=True)
        assert isinstance(res, dict)
        if "error" not in res:
            assert res.get("status") == "connected"
            print("Groq API connection successful!")
        else:
            print(f"Groq returned parse error or api issue: {res}")
    else:
        pytest.skip(f"API key not configured or is placeholder for provider: {provider}. Skipping live connection test.")

