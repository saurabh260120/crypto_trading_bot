"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_client import make_asgi_app

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import api_router
from app.core.logging import setup_logging
from app.core.middleware import LoggingMiddleware, ErrorHandlingMiddleware

# Setup logging
setup_logging()

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Delta Exchange Trading Platform",
    description="Multi-user algorithmic trading platform for Delta Exchange",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Custom middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Delta Exchange Trading Platform API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

