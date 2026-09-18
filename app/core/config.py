# Starlette 0.28.0+ / FastAPI Compatibility Patch
# Addresses signature changes in Starlette's Router.__init__ where lifespan handlers 
# (on_startup/on_shutdown) were deprecated or modified, preventing FastAPI initialization errors.
import starlette.routing
import fastapi.applications

if hasattr(starlette.routing, "Router"):
    # Store the original __init__ method reference
    _orig_router_init = starlette.routing.Router.__init__
    
    # Define a custom wrapper to gracefully handle legacy on_startup and on_shutdown arguments
    def _patched_router_init(self, *args, on_startup=None, on_shutdown=None, **kwargs):
        self.on_startup = on_startup or []
        self.on_shutdown = on_shutdown or []
        _orig_router_init(self, *args, **kwargs)
        
    # Monkey-patch the Starlette Router with the updated signature wrapper
    starlette.routing.Router.__init__ = _patched_router_init

# Fallback for missing FastAPI application attributes in varying versions
if not hasattr(fastapi.applications.FastAPI, "max_body_size"):
    # Set a default max_body_size attribute if the installed version lacks it
    setattr(fastapi.applications.FastAPI, "max_body_size", None)

# Core Imports
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
