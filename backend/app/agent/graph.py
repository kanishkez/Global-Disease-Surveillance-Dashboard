"""LangGraph agent for disease intelligence research."""

import json
import logging
import time
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent

from app.agent.schemas import (
    AgentQueryResponse,
    DiseaseIntelligence,
    DrugInfo,
)
from app.agent.tools import (
    lookup_database_outbreaks,
    lookup_database_stats,
    search_web,
)
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ── System prompt ──────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a disease intelligence research agent for a Global Disease Surveillance Dashboard.

Your job is to provide comprehensive, medically accurate intelligence reports about diseases, treatments, drugs, and outbreaks.

You have access to three tools:
1. **search_web** — Search the internet for the latest medical/epidemiological information
2. **lookup_database_outbreaks** — Check the local surveillance database for active outbreak reports
3. **lookup_database_stats** — Check the local database for case statistics

## Workflow
1. ALWAYS start by searching the web for authoritative information about the query
2. If the query mentions a specific disease, also look up outbreaks and stats from the database
3. Combine all information into a comprehensive response

## Response Format
After gathering information, respond with a JSON object matching this EXACT structure:
```json
{
  "disease_name": "Name of the disease",
  "overview": "Brief 2-3 sentence overview of what the disease is",
  "symptoms": ["symptom1", "symptom2", "symptom3"],
  "transmission": "How the disease spreads",
  "treatments": ["treatment approach 1", "treatment approach 2"],
  "drugs": [
    {"name": "Drug Name", "usage": "What it's used for", "notes": "Dosage or side effect info"},
    {"name": "Another Drug", "usage": "Usage context", "notes": "Important notes"}
  ],
  "prevention": ["prevention measure 1", "prevention measure 2"],
  "risk_factors": ["risk factor 1", "risk factor 2"],
  "prognosis": "Expected outcome with proper treatment",
  "current_outbreak_context": "Current global situation, any active outbreaks, recent trends",
  "key_statistics": "Key epidemiological numbers (incidence, mortality rate, etc.)",
  "sources": ["url1", "url2"]
}
```

IMPORTANT:
- Always provide factual, evidence-based medical information
- Cite your sources via URLs in the sources field
- Include drugs with their clinical names and usage context
- If the database has relevant outbreak/stats data, incorporate it into the context
- Respond ONLY with the JSON object, no other text
"""


def _build_agent():
    """Build the LangGraph ReAct agent."""
    llm = ChatGoogleGenerativeAI(
        model=settings.AGENT_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.1,
    )

    tools = [search_web, lookup_database_outbreaks, lookup_database_stats]

    agent = create_react_agent(
        model=llm,
        tools=tools,
        state_modifier=SYSTEM_PROMPT,
    )
    return agent


def _parse_intelligence(raw_text: str) -> DiseaseIntelligence:
    """Parse the LLM's JSON response into a DiseaseIntelligence object."""
    try:
        # Strip markdown code fences if present
        text = raw_text.strip()
        if text.startswith("```"):
            # Remove ```json or ``` prefix and trailing ```
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines)

        data = json.loads(text)

        # Convert drugs list
        drugs = []
        for d in data.get("drugs", []):
            if isinstance(d, dict):
                drugs.append(DrugInfo(**d))
            elif isinstance(d, str):
                drugs.append(DrugInfo(name=d, usage="See medical guidelines"))

        return DiseaseIntelligence(
            disease_name=data.get("disease_name", ""),
            overview=data.get("overview", ""),
            symptoms=data.get("symptoms", []),
            transmission=data.get("transmission", ""),
            treatments=data.get("treatments", []),
            drugs=drugs,
            prevention=data.get("prevention", []),
            risk_factors=data.get("risk_factors", []),
            prognosis=data.get("prognosis", ""),
            current_outbreak_context=data.get("current_outbreak_context", ""),
            key_statistics=data.get("key_statistics", ""),
            sources=data.get("sources", []),
        )
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"Failed to parse agent JSON: {e}. Using raw text.")
        return DiseaseIntelligence(
            disease_name="Unknown",
            overview=raw_text[:1000],
            sources=[],
        )


async def run_agent_query(
    query: str,
    disease_name: Optional[str] = None,
    country: Optional[str] = None,
) -> AgentQueryResponse:
    """Run the LangGraph disease intelligence agent.

    Args:
        query: User's natural language question.
        disease_name: Optional disease focus.
        country: Optional country/region focus.

    Returns:
        AgentQueryResponse with structured disease intelligence.
    """
    start = time.time()

    # Enrich the query with context
    enriched_query = query
    if disease_name:
        enriched_query += f"\n\nFocus on the disease: {disease_name}"
    if country:
        enriched_query += f"\nFocus on the country/region: {country}"

    agent = _build_agent()

    # Run the agent
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": enriched_query}]}
    )

    # Extract the final message
    last_message = result["messages"][-1]
    raw_content = (
        last_message.content
        if hasattr(last_message, "content")
        else str(last_message)
    )

    # Parse into structured output
    intelligence = _parse_intelligence(raw_content)

    # Collect raw sources from search results in intermediate messages
    raw_sources = []
    for msg in result["messages"]:
        if hasattr(msg, "content") and isinstance(msg.content, str):
            if "URL:" in msg.content:
                # Extract URLs from tool results
                for line in msg.content.split("\n"):
                    if line.startswith("URL:"):
                        url = line.replace("URL:", "").strip()
                        if url:
                            raw_sources.append({"url": url})

    elapsed = time.time() - start

    return AgentQueryResponse(
        query=query,
        intelligence=intelligence,
        raw_sources=raw_sources,
        processing_time_seconds=round(elapsed, 2),
        model_used=settings.AGENT_MODEL,
    )
