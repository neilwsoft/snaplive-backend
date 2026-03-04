"""FastAPI application entry point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection
from app.api.v1.api import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events (startup and shutdown)"""
    # Startup
    logger.info("Starting SnapLive Backend...")
    await connect_to_mongo()
    logger.info("Application startup complete")
    yield
    # Shutdown
    logger.info("Shutting down SnapLive Backend...")
    await close_mongo_connection()
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS middleware - Global configuration for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all response headers
)

# Include API router
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to SnapLive API",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "disabled",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "snaplive-backend",
        "version": settings.app_version
    }


if __name__ == "__main__":
    import uvicorn
    import os

    # Use PORT from environment (Render) or default to 8000
    port = int(os.getenv("PORT", settings.port))

    uvicorn.run(
        "app.main:app",
        host=settings.host,  # 0.0.0.0
        port=port,
        reload=settings.debug,
        log_level="info"
    )
