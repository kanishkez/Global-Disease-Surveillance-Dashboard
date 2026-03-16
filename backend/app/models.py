import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, Date,
    Boolean, ForeignKey, Index, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class SeverityLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReportClassification(str, enum.Enum):
    CONFIRMED = "confirmed_outbreak"
    SUSPECTED = "suspected_outbreak"
    NEWS = "news_mention"


class Disease(Base):
    __tablename__ = "diseases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    icd_code = Column(String(20), nullable=True)
    is_notifiable = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    outbreak_reports = relationship("OutbreakReport", back_populates="disease")
    case_statistics = relationship("CaseStatistic", back_populates="disease")
    trend_predictions = relationship("TrendPrediction", back_populates="disease")
    surveillance_events = relationship("SurveillanceEvent", back_populates="disease")


class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    iso_code = Column(String(3), unique=True, nullable=True)
    iso2_code = Column(String(2), nullable=True)
    continent = Column(String(50), nullable=True)
    population = Column(Integer, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    outbreak_reports = relationship("OutbreakReport", back_populates="country")
    case_statistics = relationship("CaseStatistic", back_populates="country")
    trend_predictions = relationship("TrendPrediction", back_populates="country")


class OutbreakReport(Base):
    __tablename__ = "outbreak_reports"

    id = Column(Integer, primary_key=True, index=True)
    disease_id = Column(Integer, ForeignKey("diseases.id"), nullable=True)
    disease_name = Column(String(255), nullable=False, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=True)
    country_name = Column(String(255), nullable=True)
    region = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    source = Column(String(100), nullable=False)
    source_url = Column(Text, nullable=True)
    report_date = Column(DateTime, nullable=False, index=True)
    description = Column(Text, nullable=True)
    severity = Column(SAEnum(SeverityLevel), default=SeverityLevel.MEDIUM)
    classification = Column(SAEnum(ReportClassification), nullable=True)
    cases_count = Column(Integer, nullable=True)
    deaths_count = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    disease = relationship("Disease", back_populates="outbreak_reports")
    country = relationship("Country", back_populates="outbreak_reports")

    __table_args__ = (
        Index("ix_outbreak_disease_date", "disease_name", "report_date"),
        Index("ix_outbreak_country_date", "country_name", "report_date"),
    )


class SurveillanceEvent(Base):
    __tablename__ = "surveillance_events"

    id = Column(Integer, primary_key=True, index=True)
    disease_id = Column(Integer, ForeignKey("diseases.id"), nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String(100), nullable=False)
    source_url = Column(Text, nullable=True)
    event_date = Column(DateTime, nullable=False, index=True)
    location = Column(String(255), nullable=True)
    country_name = Column(String(255), nullable=True)
    event_type = Column(String(100), nullable=True)
    raw_content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    disease = relationship("Disease", back_populates="surveillance_events")


class CaseStatistic(Base):
    __tablename__ = "case_statistics"

    id = Column(Integer, primary_key=True, index=True)
    disease_id = Column(Integer, ForeignKey("diseases.id"), nullable=True)
    disease_name = Column(String(255), nullable=False, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=True)
    country_name = Column(String(255), nullable=True)
    date = Column(Date, nullable=False, index=True)
    total_cases = Column(Integer, default=0)
    new_cases = Column(Integer, default=0)
    total_deaths = Column(Integer, default=0)
    new_deaths = Column(Integer, default=0)
    total_recovered = Column(Integer, default=0)
    active_cases = Column(Integer, default=0)
    cases_per_million = Column(Float, nullable=True)
    deaths_per_million = Column(Float, nullable=True)
    tests_total = Column(Integer, nullable=True)
    vaccinations_total = Column(Integer, nullable=True)
    source = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    disease = relationship("Disease", back_populates="case_statistics")
    country = relationship("Country", back_populates="case_statistics")

    __table_args__ = (
        Index("ix_case_stats_disease_country_date", "disease_name", "country_name", "date"),
    )


class TrendPrediction(Base):
    __tablename__ = "trend_predictions"

    id = Column(Integer, primary_key=True, index=True)
    disease_id = Column(Integer, ForeignKey("diseases.id"), nullable=True)
    disease_name = Column(String(255), nullable=False, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=True)
    country_name = Column(String(255), nullable=True)
    prediction_date = Column(Date, nullable=False)
    predicted_cases = Column(Integer, nullable=True)
    confidence_lower = Column(Integer, nullable=True)
    confidence_upper = Column(Integer, nullable=True)
    model_type = Column(String(50), default="lstm")
    is_anomaly = Column(Boolean, default=False)
    anomaly_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    disease = relationship("Disease", back_populates="trend_predictions")
    country = relationship("Country", back_populates="trend_predictions")
