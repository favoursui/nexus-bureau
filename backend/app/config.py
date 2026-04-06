import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Supabase
    SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY", "")

    # Stellar
    STELLAR_SECRET_KEY: str = os.environ.get("STELLAR_SECRET_KEY", "")
    STELLAR_NETWORK: str = os.environ.get("STELLAR_NETWORK", "testnet")

    # OpenAI
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.environ.get("OPENAI_MODEL", "gpt-4o")

    # Groq
    GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

    # App
    APP_ENV: str = os.environ.get("APP_ENV", "development")
    APP_PORT: int = int(os.environ.get("APP_PORT", "8000"))

def get_settings() -> Settings:
    return Settings()