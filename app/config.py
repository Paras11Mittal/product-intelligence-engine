import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

class Settings(BaseModel):
    PROJECT_NAME: str = "AI Product Intelligence Orchestration Engine"
    API_V1_STR: str = "/api/v1"
    
    # Source Reliability Scores
    MANUFACTURER_RELIABILITY: float = 0.95
    AUTHORIZED_DISTRIBUTOR_RELIABILITY: float = 0.80
    THIRD_PARTY_RELIABILITY: float = 0.60
    UNVERIFIED_RELIABILITY: float = 0.30
    
    # Conflict thresholds
    CONFLICT_NUMERIC_TOLERANCE_PCT: float = 2.0  # 2% variance allowed before conflict flagged
    
    # Search & LLM API Keys (Optional)
    SERPER_API_KEY: str = os.getenv("SERPER_API_KEY", "")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Supabase (the anon key is safe to expose to the browser; never expose a service-role key)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "").rstrip("/")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")

    # Comma-separated browser origins allowed to call this API. Keep these exact
    # origins (scheme + host + optional port), with no trailing slash.
    CORS_ALLOWED_ORIGINS: str = os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000,http://127.0.0.1:8000",
    )
    # Optional regex for preview deployments; prefer explicit origins in production.
    CORS_ALLOWED_ORIGIN_REGEX: str = os.getenv("CORS_ALLOWED_ORIGIN_REGEX", "")

settings = Settings()
