"""CDC Content Services API Ingestor"""
import httpx
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import SurveillanceEvent, Disease, OutbreakReport
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def ingest_cdc_data(db: Session):
    """Fetch disease media content from CDC Content Services API."""
    logger.info("Starting CDC data ingestion...")

    try:
        # Fetch media items related to outbreaks
        disease_queries = ["outbreak", "influenza", "covid", "measles", "ebola", "cholera", "mpox", "malaria"]

        for query in disease_queries:
            try:
                _fetch_cdc_media(db, query)
            except Exception as e:
                logger.error(f"Error fetching CDC media for '{query}': {e}")

        # Fetch topics for disease catalog
        _fetch_cdc_topics(db)

        db.commit()
        logger.info("CDC data ingestion completed.")
    except Exception as e:
        db.rollback()
        logger.error(f"CDC ingestion failed: {e}")
        raise


def _fetch_cdc_media(db: Session, query: str):
    """Fetch and store CDC media items for a given query."""
    url = f"{settings.CDC_API_BASE}/media"
    params = {"q": query, "max": 25, "pagenum": 1}

    with httpx.Client(timeout=30) as client:
        resp = client.get(url, params=params)
        if resp.status_code != 200:
            logger.warning(f"CDC API returned {resp.status_code} for query '{query}'")
            return

        data = resp.json()
        results = data.get("results", [])

        for item in results:
            try:
                media_id = str(item.get("id", ""))
                title = item.get("name", "")[:500]
                description = item.get("description", "")
                source_url = item.get("sourceUrl", "")
                date_published = item.get("datePublished", "")

                # Parse date
                event_date = datetime.utcnow()
                if date_published:
                    try:
                        event_date = datetime.fromisoformat(date_published.replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        pass

                # Check if already exists
                existing = db.query(SurveillanceEvent).filter(
                    SurveillanceEvent.source == "CDC",
                    SurveillanceEvent.title == title
                ).first()

                if not existing:
                    event = SurveillanceEvent(
                        title=title,
                        description=description[:2000] if description else None,
                        source="CDC",
                        source_url=source_url,
                        event_date=event_date,
                        location="United States",
                        country_name="United States",
                        event_type="surveillance_report",
                        raw_content=str(item)[:5000]
                    )
                    db.add(event)

                # Ensure disease exists
                _ensure_disease(db, query)

            except Exception as e:
                logger.error(f"Error processing CDC media item: {e}")


def _fetch_cdc_topics(db: Session):
    """Fetch CDC topics to populate disease catalog."""
    url = f"{settings.CDC_API_BASE}/topics"

    with httpx.Client(timeout=30) as client:
        try:
            resp = client.get(url)
            if resp.status_code != 200:
                return

            data = resp.json()
            for topic in data.get("results", [])[:50]:
                name = topic.get("name", "")
                if name:
                    _ensure_disease(db, name)
        except Exception as e:
            logger.error(f"Error fetching CDC topics: {e}")


def _ensure_disease(db: Session, name: str):
    """Ensure a disease entry exists."""
    name = name.strip().title()
    existing = db.query(Disease).filter(Disease.name == name).first()
    if not existing:
        disease = Disease(name=name, category="Infectious", description=f"Disease tracked from CDC surveillance: {name}")
        db.add(disease)
