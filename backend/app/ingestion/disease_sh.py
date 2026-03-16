"""disease.sh Global Disease API Ingestor"""
import httpx
import logging
from datetime import datetime, date
from sqlalchemy.orm import Session
from app.models import Country, CaseStatistic, Disease, OutbreakReport, SeverityLevel
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Country coordinates for map
COUNTRY_COORDS = {
    "USA": (39.8283, -98.5795), "Brazil": (-14.235, -51.9253), "India": (20.5937, 78.9629),
    "Russia": (61.524, 105.3188), "France": (46.6034, 1.8883), "UK": (55.3781, -3.436),
    "Germany": (51.1657, 10.4515), "Italy": (41.8719, 12.5674), "Spain": (40.4637, -3.7492),
    "Turkey": (38.9637, 35.2433), "Colombia": (4.5709, -74.2973), "Argentina": (-38.4161, -63.6167),
    "Mexico": (23.6345, -102.5528), "Poland": (51.9194, 19.1451), "South Africa": (-30.5595, 22.9375),
    "Iran": (32.4279, 53.688), "Peru": (-9.19, -75.0152), "Indonesia": (-0.7893, 113.9213),
    "Czech Republic": (49.8175, 15.473), "Netherlands": (52.1326, 5.2913),
    "Chile": (-35.6751, -71.543), "Canada": (56.1304, -106.3468), "Japan": (36.2048, 138.2529),
    "Philippines": (12.8797, 121.774), "Sweden": (60.1282, 18.6435),
    "Australia": (-25.2744, 133.7751), "China": (35.8617, 104.1954), "Nigeria": (9.082, 8.6753),
    "Egypt": (26.8206, 30.8025), "Kenya": (-0.0236, 37.9062), "Ethiopia": (9.145, 40.4897),
    "Thailand": (15.87, 100.9925), "Pakistan": (30.3753, 69.3451), "Bangladesh": (23.685, 90.3563),
    "Vietnam": (14.0583, 108.2772), "South Korea": (35.9078, 127.7669),
}


def ingest_disease_sh_data(db: Session):
    """Fetch COVID-19 global and country data from disease.sh."""
    logger.info("Starting disease.sh data ingestion...")

    try:
        _ensure_covid_disease(db)
        _fetch_global_stats(db)
        _fetch_country_stats(db)
        _fetch_historical_data(db)
        db.commit()
        logger.info("disease.sh data ingestion completed.")
    except Exception as e:
        db.rollback()
        logger.error(f"disease.sh ingestion failed: {e}")
        raise


def _ensure_covid_disease(db: Session):
    existing = db.query(Disease).filter(Disease.name == "COVID-19").first()
    if not existing:
        db.add(Disease(
            name="COVID-19",
            description="Coronavirus disease 2019 caused by SARS-CoV-2",
            category="Respiratory",
            is_notifiable=True
        ))
        db.flush()


def _fetch_global_stats(db: Session):
    """Fetch global COVID-19 stats."""
    with httpx.Client(timeout=30) as client:
        try:
            resp = client.get(f"{settings.DISEASE_SH_BASE}/all")
            if resp.status_code != 200:
                return

            data = resp.json()
            today = date.today()

            existing = db.query(CaseStatistic).filter(
                CaseStatistic.disease_name == "COVID-19",
                CaseStatistic.country_name == "Global",
                CaseStatistic.date == today
            ).first()

            if not existing:
                stat = CaseStatistic(
                    disease_name="COVID-19",
                    country_name="Global",
                    date=today,
                    total_cases=data.get("cases", 0),
                    new_cases=data.get("todayCases", 0),
                    total_deaths=data.get("deaths", 0),
                    new_deaths=data.get("todayDeaths", 0),
                    total_recovered=data.get("recovered", 0),
                    active_cases=data.get("active", 0),
                    cases_per_million=data.get("casesPerOneMillion"),
                    deaths_per_million=data.get("deathsPerOneMillion"),
                    tests_total=data.get("tests"),
                    source="disease.sh"
                )
                db.add(stat)
        except Exception as e:
            logger.error(f"Error fetching global stats: {e}")


def _fetch_country_stats(db: Session):
    """Fetch per-country COVID-19 stats."""
    with httpx.Client(timeout=60) as client:
        try:
            resp = client.get(f"{settings.DISEASE_SH_BASE}/countries")
            if resp.status_code != 200:
                return

            countries_data = resp.json()
            today = date.today()

            for c in countries_data[:100]:  # Top 100 countries
                country_name = c.get("country", "")
                if not country_name:
                    continue

                # Ensure country exists
                country_info = c.get("countryInfo", {})
                _ensure_country(
                    db, country_name,
                    iso3=country_info.get("iso3"),
                    iso2=country_info.get("iso2"),
                    lat=country_info.get("lat"),
                    lng=country_info.get("long"),
                    continent=c.get("continent"),
                    population=c.get("population")
                )

                # Add case stats
                existing = db.query(CaseStatistic).filter(
                    CaseStatistic.disease_name == "COVID-19",
                    CaseStatistic.country_name == country_name,
                    CaseStatistic.date == today
                ).first()

                if not existing:
                    stat = CaseStatistic(
                        disease_name="COVID-19",
                        country_name=country_name,
                        date=today,
                        total_cases=c.get("cases", 0),
                        new_cases=c.get("todayCases", 0),
                        total_deaths=c.get("deaths", 0),
                        new_deaths=c.get("todayDeaths", 0),
                        total_recovered=c.get("recovered", 0),
                        active_cases=c.get("active", 0),
                        cases_per_million=c.get("casesPerOneMillion"),
                        deaths_per_million=c.get("deathsPerOneMillion"),
                        tests_total=c.get("tests"),
                        source="disease.sh"
                    )
                    db.add(stat)

                # Create outbreak report for countries with active cases
                if c.get("todayCases", 0) > 100:
                    severity = SeverityLevel.LOW
                    if c.get("todayCases", 0) > 10000:
                        severity = SeverityLevel.CRITICAL
                    elif c.get("todayCases", 0) > 5000:
                        severity = SeverityLevel.HIGH
                    elif c.get("todayCases", 0) > 1000:
                        severity = SeverityLevel.MEDIUM

                    existing_report = db.query(OutbreakReport).filter(
                        OutbreakReport.disease_name == "COVID-19",
                        OutbreakReport.country_name == country_name,
                        OutbreakReport.report_date >= datetime.combine(today, datetime.min.time())
                    ).first()

                    if not existing_report:
                        report = OutbreakReport(
                            disease_name="COVID-19",
                            country_name=country_name,
                            latitude=country_info.get("lat"),
                            longitude=country_info.get("long"),
                            source="disease.sh",
                            source_url=f"https://disease.sh/v3/covid-19/countries/{country_name}",
                            report_date=datetime.utcnow(),
                            description=f"COVID-19 update: {c.get('todayCases', 0):,} new cases, {c.get('todayDeaths', 0):,} deaths in {country_name}",
                            severity=severity,
                            cases_count=c.get("todayCases", 0),
                            deaths_count=c.get("todayDeaths", 0),
                            is_active=True
                        )
                        db.add(report)

        except Exception as e:
            logger.error(f"Error fetching country stats: {e}")


def _fetch_historical_data(db: Session):
    """Fetch historical data for key countries."""
    top_countries = ["USA", "India", "Brazil", "France", "Germany", "UK", "Italy", "Russia", "Japan", "South Korea"]

    with httpx.Client(timeout=30) as client:
        for country in top_countries:
            try:
                resp = client.get(f"{settings.DISEASE_SH_BASE}/historical/{country}?lastdays=30")
                if resp.status_code != 200:
                    continue

                data = resp.json()
                timeline = data.get("timeline", {})
                cases = timeline.get("cases", {})
                deaths = timeline.get("deaths", {})

                prev_cases = 0
                prev_deaths = 0
                for date_str, total in cases.items():
                    try:
                        d = datetime.strptime(date_str, "%m/%d/%y").date()
                        death_total = deaths.get(date_str, 0)
                        new_c = max(0, total - prev_cases) if prev_cases else 0
                        new_d = max(0, death_total - prev_deaths) if prev_deaths else 0

                        existing = db.query(CaseStatistic).filter(
                            CaseStatistic.disease_name == "COVID-19",
                            CaseStatistic.country_name == data.get("country", country),
                            CaseStatistic.date == d
                        ).first()

                        if not existing:
                            db.add(CaseStatistic(
                                disease_name="COVID-19",
                                country_name=data.get("country", country),
                                date=d,
                                total_cases=total,
                                new_cases=new_c,
                                total_deaths=death_total,
                                new_deaths=new_d,
                                source="disease.sh"
                            ))

                        prev_cases = total
                        prev_deaths = death_total
                    except ValueError:
                        continue
            except Exception as e:
                logger.error(f"Error fetching historical data for {country}: {e}")


def _ensure_country(db: Session, name: str, iso3=None, iso2=None, lat=None, lng=None, continent=None, population=None):
    existing = db.query(Country).filter(Country.name == name).first()
    if existing:
        if lat and not existing.latitude:
            existing.latitude = lat
            existing.longitude = lng
        if population and not existing.population:
            existing.population = population
        return existing

    country = Country(
        name=name, iso_code=iso3, iso2_code=iso2,
        continent=continent, population=population,
        latitude=lat, longitude=lng
    )
    db.add(country)
    db.flush()
    return country
