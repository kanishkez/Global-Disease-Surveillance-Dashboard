"""Celery Worker with Periodic Data Ingestion Tasks"""
from celery import Celery
from celery.schedules import crontab
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Create Celery app
celery_app = Celery(
    "disease_surveillance",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=300,
    task_time_limit=600,
)

# Periodic task schedule — runs every hour
celery_app.conf.beat_schedule = {
    "cdc-ingest-hourly": {
        "task": "app.worker.cdc_ingest_job",
        "schedule": crontab(minute=0),  # Every hour at :00
    },
    "disease-sh-ingest-hourly": {
        "task": "app.worker.disease_sh_job",
        "schedule": crontab(minute=5),  # Every hour at :05
    },
    "who-ingest-hourly": {
        "task": "app.worker.who_ingest_job",
        "schedule": crontab(minute=10),  # Every hour at :10
    },
    "promed-rss-hourly": {
        "task": "app.worker.promed_rss_job",
        "schedule": crontab(minute=15),  # Every hour at :15
    },
    "fluview-rss-hourly": {
        "task": "app.worker.fluview_rss_job",
        "schedule": crontab(minute=20),  # Every hour at :20
    },
    "healthmap-scraper-hourly": {
        "task": "app.worker.healthmap_scraper",
        "schedule": crontab(minute=25),  # Every hour at :25
    },
    "run-all-ingest-startup": {
        "task": "app.worker.run_all_ingestion",
        "schedule": crontab(minute=30),  # Every hour at :30
    },
}


def _get_db_session():
    """Get a synchronous database session for Celery tasks."""
    from app.database import SyncSessionLocal
    return SyncSessionLocal()


@celery_app.task(name="app.worker.cdc_ingest_job", bind=True, max_retries=3)
def cdc_ingest_job(self):
    """Ingest data from CDC Content Services API."""
    logger.info("Running CDC ingest job...")
    try:
        from app.ingestion.cdc import ingest_cdc_data
        db = _get_db_session()
        try:
            ingest_cdc_data(db)
        finally:
            db.close()
        logger.info("CDC ingest job completed successfully")
    except Exception as exc:
        logger.error(f"CDC ingest job failed: {exc}")
        self.retry(exc=exc, countdown=60)


@celery_app.task(name="app.worker.disease_sh_job", bind=True, max_retries=3)
def disease_sh_job(self):
    """Ingest data from disease.sh API."""
    logger.info("Running disease.sh ingest job...")
    try:
        from app.ingestion.disease_sh import ingest_disease_sh_data
        db = _get_db_session()
        try:
            ingest_disease_sh_data(db)
        finally:
            db.close()
        logger.info("disease.sh ingest job completed successfully")
    except Exception as exc:
        logger.error(f"disease.sh ingest job failed: {exc}")
        self.retry(exc=exc, countdown=60)


@celery_app.task(name="app.worker.who_ingest_job", bind=True, max_retries=3)
def who_ingest_job(self):
    """Ingest data from WHO GHO API."""
    logger.info("Running WHO ingest job...")
    try:
        from app.ingestion.who_gho import ingest_who_data
        db = _get_db_session()
        try:
            ingest_who_data(db)
        finally:
            db.close()
        logger.info("WHO ingest job completed successfully")
    except Exception as exc:
        logger.error(f"WHO ingest job failed: {exc}")
        self.retry(exc=exc, countdown=60)


@celery_app.task(name="app.worker.promed_rss_job", bind=True, max_retries=3)
def promed_rss_job(self):
    """Ingest data from ProMED Mail RSS feed."""
    logger.info("Running ProMED RSS ingest job...")
    try:
        from app.ingestion.promed_rss import ingest_promed_rss
        db = _get_db_session()
        try:
            ingest_promed_rss(db)
        finally:
            db.close()
        logger.info("ProMED RSS ingest job completed successfully")
    except Exception as exc:
        logger.error(f"ProMED RSS ingest job failed: {exc}")
        self.retry(exc=exc, countdown=60)


@celery_app.task(name="app.worker.fluview_rss_job", bind=True, max_retries=3)
def fluview_rss_job(self):
    """Ingest data from CDC FluView RSS feed."""
    logger.info("Running FluView RSS ingest job...")
    try:
        from app.ingestion.fluview_rss import ingest_fluview_rss
        db = _get_db_session()
        try:
            ingest_fluview_rss(db)
        finally:
            db.close()
        logger.info("FluView RSS ingest job completed successfully")
    except Exception as exc:
        logger.error(f"FluView RSS ingest job failed: {exc}")
        self.retry(exc=exc, countdown=60)


@celery_app.task(name="app.worker.healthmap_scraper", bind=True, max_retries=3)
def healthmap_scraper(self):
    """Scrape HealthMap for outbreak data."""
    logger.info("Running HealthMap scraper job...")
    try:
        from app.ingestion.healthmap import ingest_healthmap_data
        db = _get_db_session()
        try:
            ingest_healthmap_data(db)
        finally:
            db.close()
        logger.info("HealthMap scraper job completed successfully")
    except Exception as exc:
        logger.error(f"HealthMap scraper job failed: {exc}")
        self.retry(exc=exc, countdown=60)


@celery_app.task(name="app.worker.run_all_ingestion")
def run_all_ingestion():
    """Run all ingestion tasks sequentially. Useful for initial data load."""
    logger.info("Running all ingestion tasks...")
    db = _get_db_session()
    try:
        from app.ingestion.cdc import ingest_cdc_data
        from app.ingestion.disease_sh import ingest_disease_sh_data
        from app.ingestion.who_gho import ingest_who_data
        from app.ingestion.promed_rss import ingest_promed_rss
        from app.ingestion.fluview_rss import ingest_fluview_rss
        from app.ingestion.healthmap import ingest_healthmap_data

        tasks = [
            ("CDC", ingest_cdc_data),
            ("disease.sh", ingest_disease_sh_data),
            ("ProMED", ingest_promed_rss),
            ("FluView", ingest_fluview_rss),
            ("HealthMap", ingest_healthmap_data),
        ]

        for name, task_fn in tasks:
            try:
                logger.info(f"Running {name} ingestion...")
                task_fn(db)
                logger.info(f"{name} ingestion completed")
            except Exception as e:
                logger.error(f"{name} ingestion failed: {e}")

        # WHO is slower, run last
        try:
            logger.info("Running WHO ingestion...")
            ingest_who_data(db)
            logger.info("WHO ingestion completed")
        except Exception as e:
            logger.error(f"WHO ingestion failed: {e}")

    finally:
        db.close()

    logger.info("All ingestion tasks completed")
