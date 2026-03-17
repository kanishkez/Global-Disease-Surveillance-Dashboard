"use client";

import { useState } from "react";
import {
  Search,
  Loader2,
  Brain,
  Pill,
  Shield,
  AlertCircle,
  ExternalLink,
  Sparkles,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

interface DrugInfo {
  name: string;
  usage: string;
  notes?: string;
}

interface DiseaseIntelligence {
  disease_name: string;
  overview: string;
  symptoms: string[];
  transmission: string;
  treatments: string[];
  drugs: DrugInfo[];
  prevention: string[];
  risk_factors: string[];
  prognosis: string;
  current_outbreak_context: string;
  key_statistics: string;
  sources: string[];
}

interface AgentResponse {
  query: string;
  intelligence: DiseaseIntelligence;
  raw_sources: { url: string }[];
  processing_time_seconds: number;
  model_used: string;
}

const EXAMPLE_QUERIES = [
  "What are the symptoms and treatment for cholera?",
  "Tell me about Ebola drugs and prevention",
  "Malaria treatment guidelines and recommended drugs",
  "Current monkeypox outbreak situation",
];

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function DiseaseAgent() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<AgentResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<
    Record<string, boolean>
  >({
    overview: true,
    symptoms: true,
    treatments: true,
    drugs: true,
    prevention: false,
    risk_factors: false,
    outbreak: true,
  });

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  const handleQuery = async (q?: string) => {
    const searchQuery = q || query;
    if (!searchQuery.trim()) return;

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const params = new URLSearchParams({ query: searchQuery });
      const res = await fetch(`${API_BASE}/api/agent/query?${params}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => null);
        throw new Error(
          errData?.detail || `Agent request failed (${res.status})`,
        );
      }

      const data: AgentResponse = await res.json();
      setResponse(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to get AI response",
      );
    } finally {
      setLoading(false);
    }
  };

  const SectionHeader = ({
    title,
    icon: Icon,
    sectionKey,
    count,
  }: {
    title: string;
    icon: React.ElementType;
    sectionKey: string;
    count?: number;
  }) => (
    <button
      onClick={() => toggleSection(sectionKey)}
      className="w-full flex items-center justify-between py-2 px-1 text-left group"
    >
      <div className="flex items-center gap-2">
        <Icon className="w-4 h-4 text-primary-400" />
        <span className="text-sm font-semibold text-[color:var(--text-primary)]">
          {title}
        </span>
        {count !== undefined && (
          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-primary-500/20 text-primary-400">
            {count}
          </span>
        )}
      </div>
      {expandedSections[sectionKey] ? (
        <ChevronUp className="w-4 h-4 text-[color:var(--text-muted)] group-hover:text-primary-400 transition-colors" />
      ) : (
        <ChevronDown className="w-4 h-4 text-[color:var(--text-muted)] group-hover:text-primary-400 transition-colors" />
      )}
    </button>
  );

  const intel = response?.intelligence;

  return (
    <div className="glass-card p-5">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <div className="p-2 rounded-lg bg-gradient-to-br from-violet-500/20 to-cyan-500/20 border border-violet-500/20">
          <Brain className="w-5 h-5 text-violet-400" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-[color:var(--text-primary)]">
            AI Disease Research Agent
          </h3>
          <p className="text-[11px] text-[color:var(--text-muted)]">
            Powered by LangGraph • Web search + Database intel
          </p>
        </div>
      </div>

      {/* Search Input */}
      <div className="relative mb-3">
        <input
          id="agent-search-input"
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleQuery()}
          placeholder="Ask about any disease, treatment, or drug..."
          className="w-full pl-10 pr-24 py-2.5 rounded-xl text-sm
            bg-[color:var(--glass-bg)] border border-[color:var(--border-subtle)]
            text-[color:var(--text-primary)] placeholder:text-[color:var(--text-muted)]
            focus:outline-none focus:border-primary-500/50 focus:ring-1 focus:ring-primary-500/20
            transition-all"
          disabled={loading}
        />
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[color:var(--text-muted)]" />
        <button
          id="agent-search-button"
          onClick={() => handleQuery()}
          disabled={loading || !query.trim()}
          className="absolute right-1.5 top-1/2 -translate-y-1/2
            px-3 py-1.5 rounded-lg text-xs font-medium
            bg-gradient-to-r from-violet-600 to-cyan-600
            text-white hover:from-violet-500 hover:to-cyan-500
            disabled:opacity-40 disabled:cursor-not-allowed
            transition-all flex items-center gap-1.5"
        >
          {loading ? (
            <Loader2 className="w-3 h-3 animate-spin" />
          ) : (
            <Sparkles className="w-3 h-3" />
          )}
          {loading ? "Researching..." : "Research"}
        </button>
      </div>

      {/* Example Queries */}
      {!response && !loading && (
        <div className="flex flex-wrap gap-1.5 mb-4">
          {EXAMPLE_QUERIES.map((eq) => (
            <button
              key={eq}
              onClick={() => {
                setQuery(eq);
                handleQuery(eq);
              }}
              className="text-[11px] px-2.5 py-1 rounded-lg
                bg-[color:var(--glass-bg)] border border-[color:var(--border-subtle)]
                text-[color:var(--text-muted)] hover:text-primary-400
                hover:border-primary-500/30 transition-all"
            >
              {eq}
            </button>
          ))}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="py-12 text-center animate-fade-in">
          <div className="relative inline-block">
            <div className="w-16 h-16 rounded-full border-2 border-violet-500/20 border-t-violet-500 animate-spin" />
            <Brain className="w-6 h-6 text-violet-400 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
          </div>
          <p className="text-sm mt-4 text-[color:var(--text-primary)] font-medium">
            Researching...
          </p>
          <p className="text-[11px] mt-1 text-[color:var(--text-muted)]">
            Searching the web and querying the surveillance database
          </p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {/* Results */}
      {intel && (
        <div className="space-y-1 animate-fade-in">
          {/* Disease Title */}
          {intel.disease_name && (
            <div className="mb-3 pb-3 border-b border-[color:var(--border-subtle)]">
              <h4 className="text-lg font-bold text-[color:var(--text-primary)]">
                {intel.disease_name}
              </h4>
              {response && (
                <p className="text-[10px] text-[color:var(--text-muted)] mt-1">
                  {response.model_used} • {response.processing_time_seconds}s
                </p>
              )}
            </div>
          )}

          {/* Overview */}
          {intel.overview && (
            <div>
              <SectionHeader
                title="Overview"
                icon={Brain}
                sectionKey="overview"
              />
              {expandedSections.overview && (
                <p className="text-sm leading-relaxed pl-6 pb-2 text-[color:var(--text-secondary)]">
                  {intel.overview}
                </p>
              )}
            </div>
          )}

          {/* Symptoms */}
          {intel.symptoms.length > 0 && (
            <div>
              <SectionHeader
                title="Symptoms"
                icon={AlertCircle}
                sectionKey="symptoms"
                count={intel.symptoms.length}
              />
              {expandedSections.symptoms && (
                <div className="pl-6 pb-2 flex flex-wrap gap-1.5">
                  {intel.symptoms.map((s, i) => (
                    <span
                      key={i}
                      className="text-[11px] px-2 py-1 rounded-lg
                        bg-orange-500/10 text-orange-400 border border-orange-500/15"
                    >
                      {s}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Transmission */}
          {intel.transmission && (
            <div className="pl-6 py-2 border-t border-[color:var(--border-subtle)]">
              <p className="text-[11px] font-semibold text-[color:var(--text-muted)] uppercase tracking-wider mb-1">
                Transmission
              </p>
              <p className="text-sm text-[color:var(--text-secondary)]">
                {intel.transmission}
              </p>
            </div>
          )}

          {/* Treatments */}
          {intel.treatments.length > 0 && (
            <div>
              <SectionHeader
                title="Treatments"
                icon={Shield}
                sectionKey="treatments"
                count={intel.treatments.length}
              />
              {expandedSections.treatments && (
                <ul className="pl-6 pb-2 space-y-1">
                  {intel.treatments.map((t, i) => (
                    <li
                      key={i}
                      className="text-sm text-[color:var(--text-secondary)] flex items-start gap-2"
                    >
                      <span className="w-1 h-1 rounded-full bg-emerald-500 mt-2 flex-shrink-0" />
                      {t}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {/* Drugs */}
          {intel.drugs.length > 0 && (
            <div>
              <SectionHeader
                title="Recommended Drugs"
                icon={Pill}
                sectionKey="drugs"
                count={intel.drugs.length}
              />
              {expandedSections.drugs && (
                <div className="pl-6 pb-2 space-y-2">
                  {intel.drugs.map((drug, i) => (
                    <div
                      key={i}
                      className="p-2.5 rounded-lg bg-[color:var(--glass-bg)] border border-[color:var(--border-subtle)]"
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <Pill className="w-3 h-3 text-cyan-400" />
                        <span className="text-sm font-semibold text-cyan-400">
                          {drug.name}
                        </span>
                      </div>
                      <p className="text-[12px] text-[color:var(--text-secondary)] pl-5">
                        {drug.usage}
                      </p>
                      {drug.notes && (
                        <p className="text-[11px] text-[color:var(--text-muted)] pl-5 mt-0.5 italic">
                          {drug.notes}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Prevention */}
          {intel.prevention.length > 0 && (
            <div>
              <SectionHeader
                title="Prevention"
                icon={Shield}
                sectionKey="prevention"
                count={intel.prevention.length}
              />
              {expandedSections.prevention && (
                <ul className="pl-6 pb-2 space-y-1">
                  {intel.prevention.map((p, i) => (
                    <li
                      key={i}
                      className="text-sm text-[color:var(--text-secondary)] flex items-start gap-2"
                    >
                      <span className="w-1 h-1 rounded-full bg-blue-500 mt-2 flex-shrink-0" />
                      {p}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {/* Risk Factors */}
          {intel.risk_factors.length > 0 && (
            <div>
              <SectionHeader
                title="Risk Factors"
                icon={AlertCircle}
                sectionKey="risk_factors"
                count={intel.risk_factors.length}
              />
              {expandedSections.risk_factors && (
                <div className="pl-6 pb-2 flex flex-wrap gap-1.5">
                  {intel.risk_factors.map((r, i) => (
                    <span
                      key={i}
                      className="text-[11px] px-2 py-1 rounded-lg
                        bg-red-500/10 text-red-400 border border-red-500/15"
                    >
                      {r}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Prognosis */}
          {intel.prognosis && (
            <div className="pl-6 py-2 border-t border-[color:var(--border-subtle)]">
              <p className="text-[11px] font-semibold text-[color:var(--text-muted)] uppercase tracking-wider mb-1">
                Prognosis
              </p>
              <p className="text-sm text-[color:var(--text-secondary)]">
                {intel.prognosis}
              </p>
            </div>
          )}

          {/* Outbreak Context */}
          {intel.current_outbreak_context && (
            <div>
              <SectionHeader
                title="Current Outbreak Context"
                icon={AlertCircle}
                sectionKey="outbreak"
              />
              {expandedSections.outbreak && (
                <p className="text-sm leading-relaxed pl-6 pb-2 text-[color:var(--text-secondary)]">
                  {intel.current_outbreak_context}
                </p>
              )}
            </div>
          )}

          {/* Key Statistics */}
          {intel.key_statistics && (
            <div className="pl-6 py-2 border-t border-[color:var(--border-subtle)]">
              <p className="text-[11px] font-semibold text-[color:var(--text-muted)] uppercase tracking-wider mb-1">
                Key Statistics
              </p>
              <p className="text-sm text-[color:var(--text-secondary)]">
                {intel.key_statistics}
              </p>
            </div>
          )}

          {/* Sources */}
          {intel.sources.length > 0 && (
            <div className="pt-2 border-t border-[color:var(--border-subtle)]">
              <p className="text-[11px] font-semibold text-[color:var(--text-muted)] uppercase tracking-wider mb-2">
                Sources
              </p>
              <div className="space-y-1">
                {intel.sources.map((url, i) => (
                  <a
                    key={i}
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 text-[11px] text-primary-400 hover:text-primary-300 transition-colors truncate"
                  >
                    <ExternalLink className="w-3 h-3 flex-shrink-0" />
                    <span className="truncate">{url}</span>
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
