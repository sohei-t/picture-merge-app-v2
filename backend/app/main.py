"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.merge import router as merge_router
from app.api.segment import router as segment_router
from app.services.segmentation import preload_rembg

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup: preload rembg model
    logger.info("Starting up: preloading rembg model...")
    preload_rembg()
    logger.info("Startup complete")
    yield
    # Shutdown
    logger.info("Shutting down")


app = FastAPI(
    title="Picture Merge App v2 API",
    description="API for person segmentation and image merging",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(segment_router)
app.include_router(merge_router)
