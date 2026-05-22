from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import engine, Base, AsyncSessionLocal
from app.core.scheduler import setup_scheduler, shutdown_scheduler
from app.api.v1.router import api_router

# Import all models so Base.metadata knows about them
from app.models import country, ndvi_data, rainfall_data, risk_score, alert, chat_history  # noqa: F401

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting HarvestGuard API...")

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")

    # Seed countries if needed
    async with AsyncSessionLocal() as db:
        from app.utils.seed_countries import seed_countries
        await seed_countries(db)

    # Start scheduler
    setup_scheduler(app)
    logger.info("HarvestGuard API ready")

    yield

    # Shutdown
    shutdown_scheduler()
    await engine.dispose()
    logger.info("HarvestGuard API shutdown complete")


app = FastAPI(
    title="HarvestGuard API",
    description="AI-Powered Food Insecurity Early Warning System — Real-time satellite + field data analysis",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health():
    """Health check — verifies DB connectivity."""
    async with AsyncSessionLocal() as db:
        try:
            await db.execute(text("SELECT 1"))
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {e}"
    return {"status": "ok", "db": db_status, "app": settings.app_name}


@app.post("/api/v1/admin/refresh")
async def trigger_refresh():
    """Manually trigger a full data refresh (development/admin use)."""
    from app.utils.ingest import run_full_refresh
    async with AsyncSessionLocal() as db:
        stats = await run_full_refresh(db)
    return {"status": "complete", "stats": stats}
