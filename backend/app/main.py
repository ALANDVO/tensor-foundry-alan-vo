"""Main FastAPI application entrypoint for TensorFoundry."""

from contextlib import asynccontextmanager
import logging
from typing import Dict, Any
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api import advisor, audit, auth, compiler, coverage, profiler
from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.core.security import verify_security_environment
from app.services.coverage_service import CoverageService

logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("tensor_foundry")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    # 1. Enforce strict security guards on startup
    verify_security_environment()
    logger.info("Security environment validated: APP_ENV=%s, DEMO_MODE=%s", settings.app_env, settings.demo_mode)

    # 2. Initialize database tables
    init_db()
    logger.info("Database schema verified and tables initialized at %s", settings.database_url)

    # 3. Seed operator catalog from PyTorch reference tracking issues
    db = SessionLocal()
    try:
        cov_svc = CoverageService(db)
        seeded_count = cov_svc.seed_initial_catalog()
        logger.info("Operator coverage catalog initialized with %d entries", seeded_count)
    finally:
        db.close()

    yield

    logger.info("TensorFoundry application shutting down.")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    application = FastAPI(
        title="TensorFoundry API",
        description="Dynamic Tensor Engine, Graph Optimization & Multi-Device Kernel Compiler Simulator",
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Configure CORS for Vite frontend and local dev
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Liveness and readiness probe
    @application.get("/api/v1/health", tags=["Health"])
    def health_check() -> Dict[str, Any]:
        return {
            "status": "healthy",
            "app": settings.app_name,
            "version": settings.app_version,
            "environment": settings.app_env,
            "author": settings.author_name,
            "demo_mode": settings.demo_mode
        }

    # Register API routers under /api/v1
    application.include_router(auth.router, prefix="/api/v1")
    application.include_router(compiler.router, prefix="/api/v1")
    application.include_router(coverage.router, prefix="/api/v1")
    application.include_router(profiler.router, prefix="/api/v1")
    application.include_router(advisor.router, prefix="/api/v1")
    application.include_router(audit.router, prefix="/api/v1")

    # Global unhandled exception handler
    @application.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s %s: %s", request.method, request.url.path, str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal server error occurred while processing the request"}
        )

    return application


# Global application export used by Uvicorn and test runners
app = create_app()
