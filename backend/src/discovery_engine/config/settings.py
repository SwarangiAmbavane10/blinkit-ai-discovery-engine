import os
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from discovery_engine.config.constants import BLINKIT_PLAY_STORE_ID, BLINKIT_APP_STORE_ID

# Load environment variables from .env if present
# Check for backend/.env first, then fall back to .env, or use ENV_FILE env variable if set.
env_file = os.getenv("ENV_FILE")
if env_file:
    load_dotenv(env_file)
elif os.path.exists("backend/.env"):
    load_dotenv("backend/.env")
else:
    load_dotenv(".env")

class Settings(BaseModel):
    """Configuration settings loaded from environment variables/dotenv."""
    LOG_LEVEL: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    # Gemini Config
    GEMINI_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))
    GEMINI_MODEL: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))

    # LLM Provider Config (gemini or groq)
    LLM_PROVIDER: str = Field(default_factory=lambda: os.getenv("LLM_PROVIDER", "gemini").lower())

    # Groq Config
    GROQ_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("GROQ_API_KEY"))
    GROQ_MODEL: str = Field(default_factory=lambda: os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"))

    # Play Store Config
    PLAY_STORE_APP_ID: str = Field(default_factory=lambda: os.getenv("PLAY_STORE_APP_ID", BLINKIT_PLAY_STORE_ID))
    PLAY_STORE_FETCH_LIMIT: int = Field(default_factory=lambda: int(os.getenv("PLAY_STORE_FETCH_LIMIT", "100")))

    # App Store Config
    APP_STORE_APP_ID: str = Field(default_factory=lambda: os.getenv("APP_STORE_APP_ID", BLINKIT_APP_STORE_ID))
    APP_STORE_FETCH_LIMIT: int = Field(default_factory=lambda: int(os.getenv("APP_STORE_FETCH_LIMIT", "100")))

    # Reddit Config
    REDDIT_CLIENT_ID: Optional[str] = Field(default_factory=lambda: os.getenv("REDDIT_CLIENT_ID"))
    REDDIT_CLIENT_SECRET: Optional[str] = Field(default_factory=lambda: os.getenv("REDDIT_CLIENT_SECRET"))
    REDDIT_USER_AGENT: str = Field(default_factory=lambda: os.getenv("REDDIT_USER_AGENT", "blinkit-discovery-engine:v0.1.0"))
    
    REDDIT_SUBREDDITS: List[str] = Field(
        default_factory=lambda: [
            s.strip() for s in os.getenv("REDDIT_SUBREDDITS", "india,bangalore,delhi,gurgaon,mumbai").split(",") if s.strip()
        ]
    )
    REDDIT_SEARCH_TERMS: List[str] = Field(
        default_factory=lambda: [
            s.strip() for s in os.getenv("REDDIT_SEARCH_TERMS", "blinkit,grofers").split(",") if s.strip()
        ]
    )
    REDDIT_FETCH_LIMIT: int = Field(default_factory=lambda: int(os.getenv("REDDIT_FETCH_LIMIT", "50")))

    # Storage Config
    RAW_STORE_DIR: str = Field(default_factory=lambda: os.getenv("RAW_STORE_DIR", "./data/raw"))
    DEAD_LETTER_QUEUE_DIR: str = Field(default_factory=lambda: os.getenv("DEAD_LETTER_QUEUE_DIR", "./data/dlq"))
    CLEANED_DATA_PATH: str = Field(default_factory=lambda: os.getenv("CLEANED_DATA_PATH", "clean_reviews.csv"))

# Instantiate global settings
settings = Settings()
