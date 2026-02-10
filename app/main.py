"""
Maritime Intelligence Platform - Main Application
"""
import asyncio
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db, check_db_connection
from app.api.vessels import router as vessels_router
from app.websocket.endpoints import router as websocket_router
from app.services.ais_stream import start_ais_stream, stop_ais_stream, ais_stream_client

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Maritime Intelligence Platform...")
    init_db()
    if check_db_connection():
        logger.info("Database connected")
    else:
        logger.warning("Database connection failed")
    asyncio.create_task(start_ais_stream())
    yield
    await stop_ais_stream()
    logger.info("Shutting down...")

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, docs_url="/docs", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Include routers
app.include_router(vessels_router, prefix="/api/v1/vessels", tags=["vessels"])
app.include_router(websocket_router, prefix="/ws")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION, "timestamp": time.time()}

@app.get("/ais/status")
async def ais_status():
    stats = ais_stream_client.get_stats()
    return {
        "enabled": settings.AISSTREAM_API_KEY is not None,
        "connected": stats["connected"],
        "running": stats["running"],
        "messages_received": stats["messages_received"],
        "positions_processed": stats["positions_processed"],
    }
        "messages_received": stats["messages_received"],
        "positions_processed": stats["positions_processed"],
    }
