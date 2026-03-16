"""WHO Global Health Observatory API Ingestor"""
import httpx
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Disease, Country, CaseStatistic, SurveillanceEvent
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# WHO indicators related to disease surveillance
WHO_INDICATORS = {
    "WHOSIS_000001": "Life expectancy at birth",
    "MDG_0000000001": "Infant mortality rate",
    "WHS2_131": "Tuberculosis incidence",
    "MALARIA_EST_CASES": "Malaria estimated cases",
    "HIV_0000000001": "HIV prevalence",
    "CHOLERA_0000000001": "Cholera cases",
    "WHS3_41": "Measles reported cases",
    "WHS3_43": "Yellow fever cases",
    "NCDMORT3070": "NCD mortality",
}


def ingest_who_data(db: Session):
    """Fetch health indicators from WHO GHO API."""
    logger.info("Starting WHO GHO data ingestion...")

    try:
        _fetch_countries(db)

        for indicator_code, indicator_name in WHO_INDICATORS.items():
            try:
                _fetch_indicator_data(db, indicator_code, indicator_name)
            except Exception as e:
                logger.error(f"Error fetching WHO indicator {indicator_code}: {e}")

        db.commit()
        logger.info("WHO GHO data ingestion completed.")
    except Exception as e:
        db.rollback()
        logger.error(f"WHO GHO ingestion failed: {e}")
        raise


def _fetch_countries(db: Session):
    """Fetch country list from WHO."""
    with httpx.Client(timeout=30) as client:
        try:
            resp = client.get(f"{settings.WHO_GHO_BASE}/Country")
            if resp.status_code != 200:
                return

            data = resp.json()
            for c in data.get("value", []):
                code = c.get("Code", "")
                name = c.get("Title", "")
                if name and len(code) == 3:
                    existing = db.query(Country).filter(Country.iso_code == code).first()
                    if not existing:
                        existing = db.query(Country).filter(Country.name == name).first()
                    if not existing:
                        db.add(Country(name=name, iso_code=code))
        except Exception as e:
            logger.error(f"Error fetching WHO countries: {e}")


def _fetch_indicator_data(db: Session, indicator_code: str, indicator_name: str):
    """Fetch data for a specific WHO indicator."""
    with httpx.Client(timeout=60) as client:
        url = f"{settings.WHO_GHO_BASE}/{indicator_code}"
        params = {"$top": 500, "$orderby": "TimeDim desc"}

        resp = client.get(url, params=params)
        if resp.status_code != 200:
            logger.warning(f"WHO API returned {resp.status_code} for {indicator_code}")
            return

        data = resp.json()
        values = data.get("value", [])

        # Determine disease name from indicator
        disease_name = _indicator_to_disease(indicator_code)
        if disease_name:
            _ensure_disease(db, disease_name)

        for item in values[:200]:  # Limit to recent data
            try:
                country_code = item.get("SpatialDim", "")
                year = item.get("TimeDim")
                numeric_value = item.get("NumericValue")

                if not year or numeric_value is None:
                    continue

                # Create surveillance event
                title = f"{indicator_name}: {country_code} ({year})"
                existing = db.query(SurveillanceEvent).filter(
                    SurveillanceEvent.source == "WHO",
                    SurveillanceEvent.title == title
                ).first()

                if not existing:
                    event = SurveillanceEvent(
                        title=title,
                        description=f"{indicator_name} value: {numeric_value} for {country_code} in {year}",
                        source="WHO",
                        source_url=f"https://ghoapi.azureedge.net/api/{indicator_code}",
                        event_date=datetime(int(year), 1, 1) if str(year).isdigit() else datetime.utcnow(),
                        country_name=country_code,
                        event_type="health_indicator"
                    )
                    db.add(event)

            except Exception as e:
                logger.error(f"Error processing WHO data item: {e}")


def _indicator_to_disease(code: str) -> str:
    mapping = {
        "WHS2_131": "Tuberculosis",
        "MALARIA_EST_CASES": "Malaria",
        "HIV_0000000001": "HIV/AIDS",
        "CHOLERA_0000000001": "Cholera",
        "WHS3_41": "Measles",
        "WHS3_43": "Yellow Fever",
    }
    return mapping.get(code)


def _ensure_disease(db: Session, name: str):
    existing = db.query(Disease).filter(Disease.name == name).first()
    if not existing:
        db.add(Disease(name=name, category="Infectious", description=f"WHO-tracked disease: {name}"))
