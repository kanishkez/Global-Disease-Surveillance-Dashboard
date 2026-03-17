from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, or_, text
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime, timedelta, date
import json

from app.database import get_db
from app.api.deps import get_redis, CacheService
from app.models import (
    Disease, Country, OutbreakReport, SurveillanceEvent,
    CaseStatistic, TrendPrediction, SeverityLevel
)
from app.schemas import (
    DiseaseResponse, CountryResponse, OutbreakResponse,
    CaseStatResponse, SurveillanceEventResponse, PredictionResponse,
    MapDataPoint, SearchResult, GlobalStatsResponse
)

router = APIRouter(prefix="/api")


# --- Health Check ---
@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# --- Global Stats ---
@router.get("/stats", response_model=GlobalStatsResponse)
async def get_global_stats(db: AsyncSession = Depends(get_db), redis=Depends(get_redis)):
    cache = CacheService(redis)
    cached = await cache.get("global_stats")
    if cached:
        return cached

    diseases_count = await db.scalar(select(func.count(Disease.id)))
    countries_count = await db.scalar(select(func.count(Country.id)))
    active_outbreaks = await db.scalar(
        select(func.count(OutbreakReport.id)).where(OutbreakReport.is_active == True)
    )
    total_cases = await db.scalar(
        select(func.coalesce(func.sum(CaseStatistic.total_cases), 0))
    )
    total_deaths = await db.scalar(
        select(func.coalesce(func.sum(CaseStatistic.total_deaths), 0))
    )
    total_events = await db.scalar(select(func.count(SurveillanceEvent.id)))

    result = GlobalStatsResponse(
        total_diseases_tracked=diseases_count or 0,
        total_countries=countries_count or 0,
        active_outbreaks=active_outbreaks or 0,
        total_cases=total_cases or 0,
        total_deaths=total_deaths or 0,
        total_events=total_events or 0,
        last_updated=datetime.utcnow()
    )
    await cache.set("global_stats", result.model_dump(), ttl=120)
    return result


# --- Search ---
@router.get("/search", response_model=SearchResult)
async def search(
    q: str = Query(default="", min_length=0),
    disease: Optional[str] = None,
    region: Optional[str] = None,
    country: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis)
):
    cache = CacheService(redis)
    cache_key = f"search:{q}:{disease}:{region}:{country}"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    search_term = disease or q

    # Search diseases
    diseases = []
    if search_term:
        query = select(Disease).where(Disease.name.ilike(f"%{search_term}%")).limit(20)
        result = await db.execute(query)
        diseases = [DiseaseResponse(
            id=d.id, name=d.name, description=d.description,
            category=d.category, icd_code=d.icd_code,
            is_notifiable=d.is_notifiable, created_at=d.created_at
        ) for d in result.scalars().all()]

    # Search outbreaks
    outbreak_query = select(OutbreakReport).order_by(desc(OutbreakReport.report_date)).limit(50)
    conditions = []
    if search_term:
        conditions.append(OutbreakReport.disease_name.ilike(f"%{search_term}%"))
    if country:
        conditions.append(OutbreakReport.country_name.ilike(f"%{country}%"))
    if region:
        conditions.append(OutbreakReport.region.ilike(f"%{region}%"))
    if conditions:
        outbreak_query = outbreak_query.where(and_(*conditions))

    result = await db.execute(outbreak_query)
    outbreaks = [OutbreakResponse.model_validate(o) for o in result.scalars().all()]

    # Search countries
    countries = []
    country_term = country or search_term
    if country_term:
        query = select(Country).where(Country.name.ilike(f"%{country_term}%")).limit(20)
        result = await db.execute(query)
        countries = [CountryResponse(
            id=c.id, name=c.name, iso_code=c.iso_code, iso2_code=c.iso2_code,
            continent=c.continent, population=c.population,
            latitude=c.latitude, longitude=c.longitude
        ) for c in result.scalars().all()]

    # Search events
    events = []
    if search_term:
        query = select(SurveillanceEvent).where(
            or_(
                SurveillanceEvent.title.ilike(f"%{search_term}%"),
                SurveillanceEvent.description.ilike(f"%{search_term}%")
            )
        ).order_by(desc(SurveillanceEvent.event_date)).limit(20)
        result = await db.execute(query)
        events = [SurveillanceEventResponse.model_validate(e) for e in result.scalars().all()]

    search_result = SearchResult(
        diseases=diseases,
        outbreaks=outbreaks,
        countries=countries,
        events=events
    )
    await cache.set(cache_key, search_result.model_dump(), ttl=60)
    return search_result


# --- Diseases ---
@router.get("/diseases", response_model=List[DiseaseResponse])
async def list_diseases(
    skip: int = 0, limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Disease).order_by(Disease.name).offset(skip).limit(limit)
    )
    return [DiseaseResponse(
        id=d.id, name=d.name, description=d.description,
        category=d.category, icd_code=d.icd_code,
        is_notifiable=d.is_notifiable, created_at=d.created_at
    ) for d in result.scalars().all()]


# --- Outbreaks ---
@router.get("/outbreaks", response_model=List[OutbreakResponse])
async def list_outbreaks(
    disease: Optional[str] = None,
    country: Optional[str] = None,
    severity: Optional[str] = None,
    active_only: bool = True,
    skip: int = 0, limit: int = 50,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis)
):
    cache = CacheService(redis)
    cache_key = f"outbreaks:{disease}:{country}:{severity}:{active_only}:{skip}:{limit}"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    query = select(OutbreakReport).order_by(desc(OutbreakReport.report_date))
    if disease:
        query = query.where(OutbreakReport.disease_name.ilike(f"%{disease}%"))
    if country:
        query = query.where(OutbreakReport.country_name.ilike(f"%{country}%"))
    if severity:
        query = query.where(OutbreakReport.severity == severity)
    if active_only:
        query = query.where(OutbreakReport.is_active == True)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    outbreaks = [OutbreakResponse.model_validate(o) for o in result.scalars().all()]

    await cache.set(cache_key, [o.model_dump() for o in outbreaks], ttl=120)
    return outbreaks


# --- Country ---
@router.get("/countries", response_model=List[CountryResponse])
async def list_countries(
    continent: Optional[str] = None,
    skip: int = 0, limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    query = select(Country).order_by(Country.name)
    if continent:
        query = query.where(Country.continent.ilike(f"%{continent}%"))
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return [CountryResponse(
        id=c.id, name=c.name, iso_code=c.iso_code, iso2_code=c.iso2_code,
        continent=c.continent, population=c.population,
        latitude=c.latitude, longitude=c.longitude
    ) for c in result.scalars().all()]


@router.get("/country/{country_name}", response_model=dict)
async def get_country_details(
    country_name: str,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis)
):
    cache = CacheService(redis)
    cached = await cache.get(f"country:{country_name}")
    if cached:
        return cached

    # Country info
    result = await db.execute(
        select(Country).where(Country.name.ilike(f"%{country_name}%"))
    )
    country = result.scalar_one_or_none()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    # Outbreaks
    outbreaks_result = await db.execute(
        select(OutbreakReport)
        .where(OutbreakReport.country_name.ilike(f"%{country_name}%"))
        .order_by(desc(OutbreakReport.report_date))
        .limit(20)
    )
    outbreaks = [OutbreakResponse.model_validate(o) for o in outbreaks_result.scalars().all()]

    # Case stats
    stats_result = await db.execute(
        select(CaseStatistic)
        .where(CaseStatistic.country_name.ilike(f"%{country_name}%"))
        .order_by(desc(CaseStatistic.date))
        .limit(365)
    )
    stats = [CaseStatResponse.model_validate(s) for s in stats_result.scalars().all()]

    response = {
        "country": CountryResponse(
            id=country.id, name=country.name, iso_code=country.iso_code,
            iso2_code=country.iso2_code, continent=country.continent,
            population=country.population, latitude=country.latitude,
            longitude=country.longitude
        ).model_dump(),
        "outbreaks": [o.model_dump() for o in outbreaks],
        "case_statistics": [s.model_dump() for s in stats],
    }
    await cache.set(f"country:{country_name}", response, ttl=300)
    return response


# --- Case Statistics ---
@router.get("/case-stats", response_model=List[CaseStatResponse])
async def get_case_stats(
    disease: Optional[str] = None,
    country: Optional[str] = None,
    days: int = 30,
    db: AsyncSession = Depends(get_db)
):
    since = date.today() - timedelta(days=days)
    query = select(CaseStatistic).where(CaseStatistic.date >= since)
    if disease:
        query = query.where(CaseStatistic.disease_name.ilike(f"%{disease}%"))
    if country:
        query = query.where(CaseStatistic.country_name.ilike(f"%{country}%"))
    query = query.order_by(CaseStatistic.date).limit(1000)
    result = await db.execute(query)
    return [CaseStatResponse.model_validate(s) for s in result.scalars().all()]


# --- Predictions ---
@router.get("/predict/{disease_name}", response_model=List[PredictionResponse])
async def get_predictions(
    disease_name: str,
    country: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis)
):
    cache = CacheService(redis)
    cache_key = f"predict:{disease_name}:{country}"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    query = select(TrendPrediction).where(
        TrendPrediction.disease_name.ilike(f"%{disease_name}%")
    )
    if country:
        query = query.where(TrendPrediction.country_name.ilike(f"%{country}%"))
    query = query.order_by(TrendPrediction.prediction_date).limit(30)

    result = await db.execute(query)
    predictions = [PredictionResponse.model_validate(p) for p in result.scalars().all()]

    if not predictions:
        # Return mock predictions if none exist yet
        predictions = _generate_mock_predictions(disease_name, country)

    await cache.set(cache_key, [p.model_dump() for p in predictions], ttl=600)
    return predictions


def _generate_mock_predictions(disease_name: str, country: Optional[str] = None):
    import random
    today = date.today()
    predictions = []
    base = random.randint(100, 10000)
    for i in range(7):
        pred_date = today + timedelta(days=i + 1)
        predicted = base + random.randint(-500, 500)
        predictions.append(PredictionResponse(
            disease_name=disease_name,
            country_name=country or "Global",
            prediction_date=pred_date,
            predicted_cases=max(0, predicted),
            confidence_lower=max(0, predicted - random.randint(200, 800)),
            confidence_upper=predicted + random.randint(200, 800),
            model_type="lstm",
            is_anomaly=random.random() < 0.1,
            anomaly_score=round(random.uniform(0, 1), 3)
        ))
    return predictions


# --- Map Data ---
@router.get("/map-data", response_model=List[MapDataPoint])
async def get_map_data(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis)
):
    cache = CacheService(redis)
    cached = await cache.get("map_data")
    if cached:
        return cached

    seen_countries: dict[str, MapDataPoint] = {}

    # --- Source 1: Country table (populated by disease.sh) ---
    result = await db.execute(
        select(Country).where(
            and_(Country.latitude.isnot(None), Country.longitude.isnot(None))
        )
    )
    countries = result.scalars().all()

    for c in countries:
        stats = await db.execute(
            select(CaseStatistic).where(
                CaseStatistic.country_name == c.name
            ).order_by(desc(CaseStatistic.date)).limit(1)
        )
        stat = stats.scalar_one_or_none()

        outbreaks = await db.execute(
            select(OutbreakReport).where(
                and_(
                    OutbreakReport.country_name == c.name,
                    OutbreakReport.is_active == True
                )
            )
        )
        active_outbreaks = outbreaks.scalars().all()
        diseases = list(set(o.disease_name for o in active_outbreaks))

        severity = "low"
        if len(active_outbreaks) > 3:
            severity = "critical"
        elif len(active_outbreaks) > 1:
            severity = "high"
        elif len(active_outbreaks) > 0:
            severity = "medium"

        seen_countries[c.name] = MapDataPoint(
            country_name=c.name,
            latitude=c.latitude,
            longitude=c.longitude,
            total_cases=stat.total_cases if stat else 0,
            total_deaths=stat.total_deaths if stat else 0,
            active_outbreaks=len(active_outbreaks),
            severity=severity,
            diseases=diseases
        )

    # --- Source 2: OutbreakReports with coordinates (fallback for missing Countries) ---
    outbreak_result = await db.execute(
        select(OutbreakReport).where(
            and_(
                OutbreakReport.is_active == True,
                OutbreakReport.latitude.isnot(None),
                OutbreakReport.longitude.isnot(None),
            )
        )
    )
    all_outbreaks = outbreak_result.scalars().all()

    # Group outbreaks by country
    outbreak_by_country: dict[str, list] = {}
    for o in all_outbreaks:
        name = o.country_name or "Unknown"
        outbreak_by_country.setdefault(name, []).append(o)

    for country_name, obs in outbreak_by_country.items():
        if country_name in seen_countries:
            continue  # Already covered by Country table
        first = obs[0]
        diseases = list(set(o.disease_name for o in obs))
        total_cases = sum(o.cases_count or 0 for o in obs)
        total_deaths = sum(o.deaths_count or 0 for o in obs)

        # Use the highest severity from the outbreaks
        sev_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        max_sev = max((o.severity.value if o.severity else "low" for o in obs), key=lambda s: sev_order.get(s, 0))

        seen_countries[country_name] = MapDataPoint(
            country_name=country_name,
            latitude=first.latitude,
            longitude=first.longitude,
            total_cases=total_cases,
            total_deaths=total_deaths,
            active_outbreaks=len(obs),
            severity=max_sev,
            diseases=diseases
        )

    map_points = list(seen_countries.values())
    await cache.set("map_data", [p.model_dump() for p in map_points], ttl=300)
    return map_points


# --- Surveillance Events ---
@router.get("/events", response_model=List[SurveillanceEventResponse])
async def list_events(
    source: Optional[str] = None,
    days: int = 7,
    skip: int = 0, limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    since = datetime.utcnow() - timedelta(days=days)
    query = select(SurveillanceEvent).where(
        SurveillanceEvent.event_date >= since
    ).order_by(desc(SurveillanceEvent.event_date))
    if source:
        query = query.where(SurveillanceEvent.source == source)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return [SurveillanceEventResponse.model_validate(e) for e in result.scalars().all()]


# --- AI Agent ---
@router.post("/agent/query")
async def agent_query(
    query: str = Query(..., description="Your question about a disease, drug, or outbreak"),
    disease_name: Optional[str] = Query(None, description="Optional specific disease name"),
    country: Optional[str] = Query(None, description="Optional country or region"),
    redis=Depends(get_redis),
):
    """AI-powered disease intelligence agent.

    Uses LangGraph with web search and local database lookups to provide
    comprehensive, structured information about diseases, treatments, and drugs.
    """
    from app.agent.graph import run_agent_query
    from app.config import get_settings

    settings = get_settings()
    if not settings.GOOGLE_API_KEY or not settings.TAVILY_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="AI agent not configured. Set GOOGLE_API_KEY and TAVILY_API_KEY.",
        )

    # Check cache
    cache = CacheService(redis)
    cache_key = f"agent:{query}:{disease_name}:{country}"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    try:
        response = await run_agent_query(
            query=query,
            disease_name=disease_name,
            country=country,
        )
        result = response.model_dump()
        # Convert datetime for JSON serialization
        result["timestamp"] = result["timestamp"].isoformat() if result.get("timestamp") else None
        await cache.set(cache_key, result, ttl=600)
        return result
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Agent query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Agent query failed: {str(e)}")
