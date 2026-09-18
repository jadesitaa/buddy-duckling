"""Background jobs.

The streak check runs every hour rather than once a day on purpose: users live
in different timezones, so midnight happens at a different moment for each of
them, and an hourly sweep catches every one of those midnights.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.db import SessionLocal
from app.services.streak_check import run_daily_streak_check

logger = logging.getLogger(__name__)


async def streak_check_job() -> None:
    async with SessionLocal() as db:
        broken = await run_daily_streak_check(db)
    if broken:
        logger.info("streak check: reset %s habit(s)", broken)


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        streak_check_job,
        CronTrigger(minute=5),  # five past every hour
        id="streak_check",
        replace_existing=True,
        # If the app was down for a while, run once on startup instead of
        # firing one job per missed hour.
        coalesce=True,
        max_instances=1,
    )
    return scheduler
