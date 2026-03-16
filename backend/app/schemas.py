from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


# --- Enums ---

class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReportClassification(str, Enum):
    CONFIRMED = "confirmed_outbreak"
    SUSPECTED = "suspected_outbreak"
    NEWS = "news_mention"


# --- Disease ---

class DiseaseBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    icd_code: Optional[str] = None


class DiseaseResponse(DiseaseBase):
    id: int
    is_notifiable: bool = False
    created_at: Optional[datetime] = None
    outbreak_count: int = 0
    total_cases: int = 0

    class Config:
        from_attributes = True


# --- Country ---

class CountryBase(BaseModel):
    name: str
    iso_code: Optional[str] = None
    continent: Optional[str] = None


class CountryResponse(CountryBase):
    id: int
    iso2_code: Optional[str] = None
    population: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    total_cases: int = 0
    total_deaths: int = 0
    active_outbreaks: int = 0

    class Config:
        from_attributes = True


# --- Outbreak ---

class OutbreakBase(BaseModel):
    disease_name: str
    country_name: Optional[str] = None
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source: str
    report_date: datetime
    description: Optional[str] = None
    severity: Optional[SeverityLevel] = SeverityLevel.MEDIUM


class OutbreakResponse(OutbreakBase):
    id: int
    source_url: Optional[str] = None
    classification: Optional[ReportClassification] = None
    cases_count: Optional[int] = None
    deaths_count: Optional[int] = None
    is_active: bool = True
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Case Statistics ---

class CaseStatResponse(BaseModel):
    id: int
    disease_name: str
    country_name: Optional[str] = None
    date: date
    total_cases: int = 0
    new_cases: int = 0
    total_deaths: int = 0
    new_deaths: int = 0
    total_recovered: int = 0
    active_cases: int = 0
    cases_per_million: Optional[float] = None
    deaths_per_million: Optional[float] = None
    source: Optional[str] = None

    class Config:
        from_attributes = True


# --- Surveillance Event ---

class SurveillanceEventResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    source: str
    source_url: Optional[str] = None
    event_date: datetime
    location: Optional[str] = None
    country_name: Optional[str] = None
    event_type: Optional[str] = None

    class Config:
        from_attributes = True


# --- Predictions ---

class PredictionResponse(BaseModel):
    disease_name: str
    country_name: Optional[str] = None
    prediction_date: date
    predicted_cases: Optional[int] = None
    confidence_lower: Optional[int] = None
    confidence_upper: Optional[int] = None
    model_type: str = "lstm"
    is_anomaly: bool = False
    anomaly_score: Optional[float] = None

    class Config:
        from_attributes = True


# --- Map Data ---

class MapDataPoint(BaseModel):
    country_name: str
    latitude: float
    longitude: float
    total_cases: int = 0
    total_deaths: int = 0
    active_outbreaks: int = 0
    severity: Optional[str] = None
    diseases: List[str] = []


# --- Search ---

class SearchResult(BaseModel):
    diseases: List[DiseaseResponse] = []
    outbreaks: List[OutbreakResponse] = []
    countries: List[CountryResponse] = []
    events: List[SurveillanceEventResponse] = []


# --- Global Stats ---

class GlobalStatsResponse(BaseModel):
    total_diseases_tracked: int = 0
    total_countries: int = 0
    active_outbreaks: int = 0
    total_cases: int = 0
    total_deaths: int = 0
    total_events: int = 0
    last_updated: Optional[datetime] = None


# --- Paginated ---

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int = 1
    per_page: int = 20
    pages: int = 1
