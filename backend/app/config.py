from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # Stellar
    STELLAR_SECRET_KEY: str
    STELLAR_NETWORK: str = "testnet"  # change to "mainnet" for production

    # OpenAI (LangChain)
    OPENAI_API_KEY: str

    # App
    APP_ENV: str = "development"
    APP_PORT: int = 8000

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()