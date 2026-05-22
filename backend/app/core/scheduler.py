"""
APScheduler background jobs for periodic data refresh.
Runs inside the FastAPI lifespan context.
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def setup_scheduler(app):
    """Register all background jobs. Called during app startup."""

    @scheduler.scheduled_job(IntervalTrigger(hours=6), id="refresh_hunger_map", misfire_grace_time=600)
    async def refresh_wfp_data():
        """Refresh WFP HungerMap data every 6 hours."""
        from app.core.database import AsyncSessionLocal
        from app.utils.ingest import run_full_refresh
        logger.info("Scheduled: starting data refresh")
        async with AsyncSessionLocal() as db:
            stats = await run_full_refresh(db)
        logger.info("Scheduled refresh complete: %s", stats)

    scheduler.start()
    logger.info("Scheduler started with %d jobs", len(scheduler.get_jobs()))


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
