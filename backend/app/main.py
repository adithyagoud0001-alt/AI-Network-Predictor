"""FastAPI Application Main Entrypoint

Initializes FastAPI, configures CORS, database schema initialization,
and mounts API and WebSocket routers.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database.connection import engine, Base
from app.api.routes import router as api_router
from app.api.websocket import ws_router
from app.collector.telemetry import telemetry_service
from app.ml.service import prediction_engine

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("network_predictor")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management for database and background collector tasks."""
    logger.info("Initializing database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    except Exception as exc:
        logger.error(f"Error creating database tables: {exc}")

    # Ensure model is ready
    if prediction_engine.pipeline is None:
        logger.warning("ML champion pipeline not loaded during startup; attempting reload...")
        prediction_engine.load_model()

    # Start telemetry monitoring service
    logger.info("Starting background network telemetry collector service...")
    telemetry_service.start()

    yield

    # Clean shutdown
    logger.info("Shutting down background services...")
    await telemetry_service.stop()
    logger.info("Application shutdown complete.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Full-Stack AI/ML-Powered Network Observability and Connection Predictor",
    lifespan=lifespan
)

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routes
app.include_router(api_router, prefix="/api/v1", tags=["Network Telemetry & Predictions"])
app.include_router(ws_router, tags=["Real-Time WebSockets"])


# Root info endpoint
@app.get("/", tags=["System"])
def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "api_prefix": "/api/v1",
        "websocket_endpoint": "/ws/telemetry",
        "status": "operational"
    }


# Production exception handler preventing raw stack trace exposure
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred while processing the network telemetry request.",
            "path": request.url.path
        }
    )
