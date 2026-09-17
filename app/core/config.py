# Starlette 1.6+ compatibility patch for FastAPI
import starlette.routing
import fastapi.applications

if hasattr(starlette.routing, "Router"):
    _orig_router_init = starlette.routing.Router.__init__
    def _patched_router_init(self, *args, on_startup=None, on_shutdown=None, **kwargs):
        self.on_startup = on_startup or []
        self.on_shutdown = on_shutdown or []
        _orig_router_init(self, *args, **kwargs)
    starlette.routing.Router.__init__ = _patched_router_init

if not hasattr(fastapi.applications.FastAPI, "max_body_size"):
    setattr(fastapi.applications.FastAPI, "max_body_size", None)

import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Developer Control Tower AI Assistant"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./towerbot.db"
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    USE_IN_MEMORY_REDIS_FALLBACK: bool = True
    
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
    DEFAULT_MODEL_NAME: str = "gemini-1.5-flash"
    FALLBACK_MODEL_NAME: str = "gemini-1.5-pro"
    MAX_OUTPUT_TOKENS: int = 2048
    TEMPERATURE: float = 0.2
    
    WORKING_MEMORY_MAX_TURNS: int = 12
    WORKING_MEMORY_TOKEN_BUDGET: int = 3000
    EPISODIC_RECALL_TOP_K: int = 5
    EPISODIC_DECAY_RATE: float = 0.05
    SEMANTIC_RAG_TOP_K: int = 4
    
    IDLE_SESSION_MINUTES_TRIGGER: int = 15
    AUTO_CONSOLIDATION_ENABLED: bool = True

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
