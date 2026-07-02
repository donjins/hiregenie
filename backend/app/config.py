import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file using absolute path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(backend_dir, ".env")
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    PROJECT_NAME: str = "HireGenie AI"
    API_V1_STR: str = "/api/v1"
    
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    MONGODB_URI: str = os.getenv("MONGODB_URI", "")
    DATABASE_NAME: str = "hiregenie"
    
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Directory to store uploaded resumes
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
    
    # Auto-detect if we should use Mock LLM or real OpenAI API
    @property
    def USE_MOCK_LLM(self) -> bool:
        return not bool(self.OPENAI_API_KEY.strip())

settings = Settings()

# Create upload directory if it doesn't exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
