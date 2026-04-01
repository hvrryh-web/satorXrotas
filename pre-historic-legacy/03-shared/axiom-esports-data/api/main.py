"""
SATOR API - FastAPI Application Entry Point
Production-ready FastAPI application with health checks, CORS, and graceful startup/shutdown.
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

import asyncpg
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

# Import route modules
from api.src.routes import players, matches, analytics

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "text")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    if LOG_FORMAT == "text"
    else "%(message)s",
)

logger = logging.getLogger(__name__)

# Application metadata
APP_NAME = os.getenv("APP_NAME", "SATOR-API")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
APP_ENVIRONMENT = os.getenv("APP_ENVIRONMENT", "development")

# Database configuration
DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")

# Global database pool (initialized during startup)
db_pool: Optional[asyncpg.Pool] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager - handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {APP_NAME} v{APP_VERSION} in {APP_ENVIRONMENT} mode")
    
    global db_pool
    if DATABASE_URL:
        try:
            db_pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=1,
                max_size=5,  # Conservative for free tier
                command_timeout=30,
                server_settings={
                    'jit': 'off',  # Disable JIT for faster simple queries
                }
            )
            logger.info("Database connection pool established")
            
            # Test connection
            async with db_pool.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                logger.info(f"Connected to PostgreSQL: {version[:50]}...")
                
                # Check TimescaleDB
                try:
                    ts_version = await conn.fetchval(
                        "SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'"
                    )
                    logger.info(f"TimescaleDB version: {ts_version}")
                except Exception:
                    logger.warning("TimescaleDB extension not found")
                    
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            db_pool = None
    else:
        logger.warning("DATABASE_URL not set - running in stub mode")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {APP_NAME}")
    if db_pool:
        await db_pool.close()
        logger.info("Database connection pool closed")


# Create FastAPI application
app = FastAPI(
    title="SATOR Esports API",
    description="""
    SATOR Esports Platform API - Player analytics, match data, and investment grading.
    
    ## Features
    
    * **Players**: Query player stats, SimRating, RAR scores
    * **Matches**: Access match data and SATOR spatial events
    * **Analytics**: Investment grades, performance analytics
    
    ## Free Tier Notice
    
    This API runs on Render's free tier and may experience cold starts
    (10-30s response time on first request after 15 minutes of inactivity).
    """,
    version=APP_VERSION,
    docs_url="/docs" if APP_ENVIRONMENT != "production" else None,
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Add CORS middleware
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,  # 10 minutes
)

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# ---------------------------------------------------------------------------
# Health Check Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint for monitoring and keepalive pings.
    
    Returns:
        Health status with database connectivity information.
    """
    health_status = {
        "status": "healthy",
        "service": APP_NAME.lower(),
        "version": APP_VERSION,
        "environment": APP_ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    
    # Check database connectivity
    if db_pool:
        try:
            async with db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                health_status["database"] = "connected"
        except Exception as e:
            health_status["database"] = "error"
            health_status["database_error"] = str(e)
            logger.error(f"Health check database error: {e}")
    else:
        health_status["database"] = "not_configured"
    
    return health_status


@app.get("/ready", tags=["health"])
async def readiness_check():
    """
    Readiness check for load balancers and orchestrators.
    
    Returns 503 if the service is not ready to accept traffic.
    """
    if not DATABASE_URL:
        return {"ready": True, "mode": "stub"}  # OK for stub mode
    
    if db_pool is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"ready": True}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")


@app.get("/live", tags=["health"])
async def liveness_check():
    """
    Liveness check for Kubernetes-style health monitoring.
    
    Always returns 200 if the process is running.
    """
    return {"alive": True}


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------

# Include route modules
app.include_router(players.router)
app.include_router(matches.router)
app.include_router(analytics.router)


# ---------------------------------------------------------------------------
# Root Endpoint
# ---------------------------------------------------------------------------

@app.get("/", tags=["root"])
async def root():
    """
    API root - returns service information and available endpoints.
    """
    return {
        "service": APP_NAME,
        "version": APP_VERSION,
        "environment": APP_ENVIRONMENT,
        "documentation": "/redoc",
        "health": "/health",
        "endpoints": {
            "players": "/api/players",
            "matches": "/api/matches",
            "analytics": "/api/analytics",
        }
    }


# ---------------------------------------------------------------------------
# Error Handlers
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for uncaught errors.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if APP_ENVIRONMENT == "development" else "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    )


@app.exception_handler(asyncpg.PostgresError)
async def database_exception_handler(request: Request, exc: asyncpg.PostgresError):
    """
    Handle PostgreSQL-specific errors.
    """
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Database error",
            "message": "A database error occurred" if APP_ENVIRONMENT == "production" else str(exc),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    )


# ---------------------------------------------------------------------------
# Middleware: Request Logging
# ---------------------------------------------------------------------------

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all incoming requests for monitoring and debugging.
    """
    start_time = datetime.utcnow()
    
    response = await call_next(request)
    
    duration = (datetime.utcnow() - start_time).total_seconds()
    
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {duration:.3f}s"
    )
    
    # Add response headers for debugging
    response.headers["X-Request-ID"] = str(start_time.timestamp())
    response.headers["X-API-Version"] = APP_VERSION
    
    return response


# ---------------------------------------------------------------------------
# Development Server Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("API_PORT", "8000"))
    host = os.getenv("API_HOST", "0.0.0.0")
    workers = int(os.getenv("API_WORKERS", "1"))
    
    logger.info(f"Starting development server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        workers=workers,
        reload=True if APP_ENVIRONMENT == "development" else False,
        log_level=LOG_LEVEL.lower(),
    )
