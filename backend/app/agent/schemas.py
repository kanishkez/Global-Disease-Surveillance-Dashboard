from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class AgentQueryRequest(BaseModel):
    """User's question about a disease, drug, or outbreak."""
    query: str = Field(..., description="The user's natural language question")
    disease_name: Optional[str] = Field(None, description="Optional disease name to focus on")
    country: Optional[str] = Field(None, description="Optional country/region to focus on")


class DrugInfo(BaseModel):
    """Information about a drug or treatment."""
    name: str = ""
    usage: str = ""
    notes: Optional[str] = None


class DiseaseIntelligence(BaseModel):
    """Structured intelligence report about a disease."""
    disease_name: str = Field("", description="Name of the disease being researched")
    overview: str = Field("", description="Brief overview / what the disease is")
    symptoms: List[str] = Field(default_factory=list, description="List of symptoms")
    transmission: str = Field("", description="How the disease spreads")
    treatments: List[str] = Field(default_factory=list, description="Treatment approaches")
    drugs: List[DrugInfo] = Field(default_factory=list, description="Recommended drugs")
    prevention: List[str] = Field(default_factory=list, description="Prevention measures")
    risk_factors: List[str] = Field(default_factory=list, description="Risk factors")
    prognosis: str = Field("", description="Expected outcome / prognosis")
    current_outbreak_context: str = Field(
        "", description="Current global situation and active outbreaks"
    )
    key_statistics: str = Field("", description="Key epidemiological statistics")
    sources: List[str] = Field(default_factory=list, description="URLs and references used")


class AgentQueryResponse(BaseModel):
    """Full response from the disease intelligence agent."""
    query: str
    intelligence: DiseaseIntelligence
    raw_sources: List[dict] = Field(default_factory=list, description="Raw search results")
    processing_time_seconds: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    model_used: str = ""
