"""
Configuration settings for the application.
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # File upload settings
    MAX_FILE_SIZE_MB: int = 100
    MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024
    ALLOWED_EXTENSIONS: list[str] = [".csv", ".xlsx", ".xls", ".html"]
    
    # Storage paths
    UPLOAD_DIR: Path = Path("data/uploads")
    REPORTS_DIR: Path = Path("data/reports")
    TEMP_DIR: Path = Path("data/temp")
    
    # LLM settings (for future use)
    USE_LLM: bool = False
    LLM_PROVIDER: str = "openai"  # or "anthropic", "local", etc.
    LLM_MODEL: str = "gpt-4o"
    LLM_TEMPERATURE: float = 0.0  # Deterministic reasoning
    LLM_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    LLM_BASE_URL: Optional[str] = None
    
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_TITLE: str = "Agentic Data Intelligence Studio API"
    API_VERSION: str = "1.0.0"
    
    # Streamlit settings
    STREAMLIT_PORT: int = 8501
    
    class Config:
        env_file = str(Path(__file__).resolve().parent.parent / ".env")
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        self.TEMP_DIR.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
