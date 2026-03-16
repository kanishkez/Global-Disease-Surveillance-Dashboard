"""Startup seed script — runs initial data ingestion on first launch."""
import logging
from sqlalchemy import text
from app.database import sync_engine, SyncSessionLocal

logger = logging.getLogger(__name__)


def seed_initial_data():
    """
    Called from FastAPI lifespan if the database is empty.
    Populates database with data from all sources.
    """
    session = SyncSessionLocal()
    try:
        # Check if we already have data
        result = session.execute(text("SELECT COUNT(*) FROM diseases"))
        count = result.scalar()
        if count and count > 0:
            logger.info(f"Database already has {count} diseases, skipping seed.")
            return

        logger.info("Database is empty — running initial data seed...")

        from app.ingestion.disease_sh import ingest_disease_sh_data
        from app.ingestion.promed_rss import ingest_promed_rss
        from app.ingestion.fluview_rss import ingest_fluview_rss
        from app.ingestion.healthmap import ingest_healthmap_data
        from app.ingestion.cdc import ingest_cdc_data

        tasks = [
            ("disease.sh", ingest_disease_sh_data),
            ("ProMED", ingest_promed_rss),
            ("FluView", ingest_fluview_rss),
            ("HealthMap", ingest_healthmap_data),
            ("CDC", ingest_cdc_data),
        ]

        for name, fn in tasks:
            try:
                logger.info(f"  ↳ Seeding from {name}...")
                fn(session)
                logger.info(f"  ✓ {name} seed complete")
            except Exception as e:
                logger.error(f"  ✗ {name} seed failed: {e}")
                session.rollback()

        logger.info("Initial data seed completed!")

    except Exception as e:
        logger.error(f"Seed failed (table may not exist yet): {e}")
    finally:
        session.close()
