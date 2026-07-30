import logging
import sys
from discovery_engine.config.settings import settings

def setup_logging(name: str = "discovery_engine") -> logging.Logger:
    """Configures structured, clean logging for the discovery engine."""
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if setup is run multiple times
    if logger.handlers:
        return logger
        
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    level_name = settings.LOG_LEVEL.upper()
    level = getattr(logging, level_name, logging.INFO)
    logger.setLevel(level)
    
    return logger

# Module-level logger
logger = setup_logging()
