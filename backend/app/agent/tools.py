"""Tools for the LangGraph disease intelligence agent."""

import logging
from typing import Optional

from langchain_core.tools import tool
from sqlalchemy import create_engine, text
from tavily import TavilyClient

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# --- Sync DB engine for tool use (LangGraph tools run synchronously) ---
_sync_engine = create_engine(settings.SYNC_DATABASE_URL)


@tool
def search_web(query: str) -> str:
    """Search the internet for current information about diseases, treatments,
    drugs, outbreaks, and medical topics. Returns relevant web results.

    Args:
        query: The search query about a disease, drug, or medical topic.
    """
    try:
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        results = client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_answer=True,
        )
        # Format results
        output_parts = []
        if results.get("answer"):
            output_parts.append(f"Summary: {results['answer']}\n")

        for i, r in enumerate(results.get("results", []), 1):
            output_parts.append(
                f"[{i}] {r.get('title', 'Untitled')}\n"
                f"URL: {r.get('url', '')}\n"
                f"Content: {r.get('content', '')[:500]}\n"
            )
        return "\n".join(output_parts) if output_parts else "No results found."
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return f"Web search error: {str(e)}"


@tool
def lookup_database_outbreaks(disease_name: str) -> str:
    """Look up active outbreak reports for a specific disease from the local
    surveillance database. Returns recent outbreak data including location,
    severity, cases, and dates.

    Args:
        disease_name: The name of the disease to look up outbreaks for.
    """
    try:
        with _sync_engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT disease_name, country_name, region, severity, "
                    "cases_count, deaths_count, report_date, description, source "
                    "FROM outbreak_reports "
                    "WHERE LOWER(disease_name) LIKE LOWER(:name) "
                    "AND is_active = true "
                    "ORDER BY report_date DESC LIMIT 10"
                ),
                {"name": f"%{disease_name}%"},
            )
            rows = result.fetchall()
            if not rows:
                return f"No active outbreaks found for '{disease_name}' in the database."

            parts = [f"Found {len(rows)} active outbreak(s) for '{disease_name}':\n"]
            for row in rows:
                parts.append(
                    f"- {row.disease_name} in {row.country_name or 'Unknown'}"
                    f" ({row.region or 'N/A'})"
                    f" | Severity: {row.severity or 'N/A'}"
                    f" | Cases: {row.cases_count or 0}"
                    f" | Deaths: {row.deaths_count or 0}"
                    f" | Date: {row.report_date}"
                    f" | Source: {row.source or 'N/A'}"
                )
            return "\n".join(parts)
    except Exception as e:
        logger.error(f"DB outbreak lookup failed: {e}")
        return f"Database lookup error: {str(e)}"


@tool
def lookup_database_stats(
    disease_name: str, country: Optional[str] = None
) -> str:
    """Look up case statistics for a disease from the local surveillance
    database. Optionally filter by country. Returns case counts, death counts,
    and trends.

    Args:
        disease_name: The disease to look up statistics for.
        country: Optional country name to filter results.
    """
    try:
        with _sync_engine.connect() as conn:
            query = (
                "SELECT disease_name, country_name, date, "
                "total_cases, new_cases, total_deaths, new_deaths, "
                "total_recovered, active_cases "
                "FROM case_statistics "
                "WHERE LOWER(disease_name) LIKE LOWER(:name) "
            )
            params: dict = {"name": f"%{disease_name}%"}

            if country:
                query += "AND LOWER(country_name) LIKE LOWER(:country) "
                params["country"] = f"%{country}%"

            query += "ORDER BY date DESC LIMIT 15"

            result = conn.execute(text(query), params)
            rows = result.fetchall()
            if not rows:
                return f"No case statistics found for '{disease_name}' in the database."

            parts = [f"Recent statistics for '{disease_name}':\n"]
            for row in rows:
                parts.append(
                    f"- {row.date} | {row.country_name or 'Global'}"
                    f" | Cases: {row.total_cases} (new: {row.new_cases})"
                    f" | Deaths: {row.total_deaths} (new: {row.new_deaths})"
                    f" | Recovered: {row.total_recovered}"
                    f" | Active: {row.active_cases}"
                )
            return "\n".join(parts)
    except Exception as e:
        logger.error(f"DB stats lookup failed: {e}")
        return f"Database lookup error: {str(e)}"
