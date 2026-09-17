import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.logger import logger
from app.models.database import init_db
from app.api.routes_chat import router as chat_router
from app.api.routes_memories import router as memories_router
from app.api.routes_features import router as features_router
from app.api.routes_telemetry import router as telemetry_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Developer Control Tower Assistant...")
    init_db()
    logger.info("Database schemas initialized.")
    yield
    logger.info("Shutting down Developer Control Tower Assistant...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(chat_router, prefix=settings.API_V1_PREFIX)
app.include_router(memories_router, prefix=settings.API_V1_PREFIX)
app.include_router(features_router, prefix=settings.API_V1_PREFIX)
app.include_router(telemetry_router, prefix=settings.API_V1_PREFIX)

# Mount static web UI
static_dir = os.path.join(os.path.dirname(__file__), "app", "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
