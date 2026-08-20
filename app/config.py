import os
from pydantic import BaseModel

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

settings = Settings()
