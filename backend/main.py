import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.core.logging_config import setup_logging, log_error
from app.middleware.logging_middleware import LoggingMiddleware
from app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize logging system
    logging_info = setup_logging()
    logger = logging.getLogger("ovra.main")
    
    logger.info("🚀 Starting OVRA AI Backend Service")
    logger.info(f"📊 Project: {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"📝 Logs directory: {logging_info['logs_dir']}")
    
    try:
        # Startup - Create database tables
        logger.info("🗄️ Initializing database connection...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created/verified successfully")
        
        logger.info("🎯 OVRA AI Backend started successfully!")
        yield
        
    except Exception as e:
        log_error(e, "Application startup", service="main")
        raise
    finally:
        # Shutdown
        logger.info("🛑 Shutting down OVRA AI Backend...")
        try:
            await engine.dispose()
            logger.info("✅ Database connections closed")
        except Exception as e:
            log_error(e, "Application shutdown", service="main")
        logger.info("👋 OVRA AI Backend shutdown complete")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Add logging middleware (should be first)
app.add_middleware(LoggingMiddleware)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    logger = logging.getLogger("ovra.main")
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to OVRA AI API", "version": settings.VERSION}


@app.get("/health")
async def health_check():
    logger = logging.getLogger("ovra.main")
    logger.info("Health check endpoint accessed")
    return {"status": "healthy"}