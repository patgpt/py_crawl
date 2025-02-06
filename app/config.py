from pydantic_settings import BaseSettings
import logging
import sys
from pathlib import Path

# Configure logging
def setup_logging():
    """
    Configure logging for the application
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        handlers=[
            # Console handler
            logging.StreamHandler(sys.stdout),
            # File handler
            logging.FileHandler("logs/app.log")
        ]
    )

# Initialize logging
setup_logging()

"""
Application configuration using Pydantic BaseSettings
"""

class Settings(BaseSettings):
    """
    Application settings

    Attributes:
        APP_NAME (str): Name of the application
        DEBUG (bool): Debug mode flag
        API_V1_STR (str): API version prefix
        DEFAULT_USER_AGENT (str): Default user agent for web scraping
        DEFAULT_TIMEOUT (int): Default timeout for requests
    """
    APP_NAME: str = "FastAPI Application"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # Scraping settings
    DEFAULT_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    DEFAULT_TIMEOUT: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
