"use client";

import { useState, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Activity, TrendingUp, AlertTriangle, Search } from "lucide-react";
import { api, Disease, Outbreak, SearchResult } from "@/lib/api";
import AlertFeed from "@/components/AlertFeed";
import TrendChart from "@/components/TrendChart";

export default function DiseasesContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryParam = searchParams.get("q") || "";

  const [diseases, setDiseases] = useState<Disease[]>([]);
  const [selectedDisease, setSelectedDisease] = useState<string | null>(null);
  const [outbreaks, setOutbreaks] = useState<Outbreak[]>([]);
  const [predictions, setPredictions] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState(queryParam);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDiseases();
  }, []);

  useEffect(() => {
    if (queryParam) {
      setSearchQuery(queryParam);
      searchDiseases(queryParam);
    }
  }, [queryParam]);

  useEffect(() => {
    if (selectedDisease) {
      loadDiseaseDetails(selectedDisease);
    }
  }, [selectedDisease]);

  async function loadDiseases() {
    try {
      const data = await api.getDiseases();
      setDiseases(data);
      if (data.length > 0 && !selectedDisease && !queryParam) {
        setSelectedDisease(data[0].name);
      }
    } catch (err) {
      console.error("Failed to load diseases:", err);
    } finally {
      setLoading(false);
    }
  }

  async function searchDiseases(query: string) {
    try {
      setLoading(true);
      const result = await api.search({ q: query, disease: query });
      if (result.diseases.length > 0) {
        setDiseases(result.diseases);
        setSelectedDisease(result.diseases[0].name);
      }
      if (result.outbreaks.length > 0) {
        setOutbreaks(result.outbreaks);
      }
    } catch (err) {
      console.error("Search failed:", err);
    } finally {
      setLoading(false);
    }
  }

  async function loadDiseaseDetails(disease: string) {
    try {
      const [outbreakData, predData] = await Promise.allSettled([
        api.getOutbreaks({ disease }),
        api.getPredictions(disease),
      ]);
      if (outbreakData.status === "fulfilled") setOutbreaks(outbreakData.value);
      if (predData.status === "fulfilled") setPredictions(predData.value);
    } catch (err) {
      console.error("Failed to load disease details:", err);
    }
  }

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) searchDiseases(searchQuery.trim());
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header & Search */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Activity className="w-6 h-6 text-blue-500" />
            Disease Intelligence
          </h1>
          <p className="text-dark-400 text-sm mt-1">
            Search and analyze disease surveillance data
          </p>
        </div>
        <form onSubmit={handleSearchSubmit} className="w-full sm:w-80">
          <div className="relative">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search diseases (e.g., flu, covid, malaria)..."
              className="w-full pl-10 pr-4 py-2.5 rounded-lg text-sm bg-white/5 border border-white/10 text-white placeholder-dark-400 outline-none focus:border-primary-500/50 focus:ring-1 focus:ring-primary-500/20 transition-all"
            />
          </div>
        </form>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Disease List */}
        <div className="lg:col-span-1">
          <h2 className="text-sm font-semibold text-dark-400 uppercase tracking-wider mb-3">
            Tracked Diseases
          </h2>
          <div className="space-y-1 max-h-[600px] overflow-y-auto pr-1">
            {loading && diseases.length === 0 ? (
              Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="shimmer h-12 rounded-lg" />
              ))
            ) : diseases.length === 0 ? (
              <p className="text-dark-400 text-sm py-4 text-center">
                No diseases found
              </p>
            ) : (
              diseases.map((disease) => (
                <button
                  key={disease.id}
                  onClick={() => setSelectedDisease(disease.name)}
                  className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-all duration-200
                    ${
                      selectedDisease === disease.name
                        ? "bg-primary-600/20 border border-primary-500/30 text-white"
                        : "text-dark-300 hover:bg-white/5 hover:text-white border border-transparent"
                    }`}
                >
                  <span className="font-medium">{disease.name}</span>
                  {disease.category && (
                    <span className="block text-[11px] text-dark-500 mt-0.5">
                      {disease.category}
                    </span>
                  )}
                </button>
              ))
            )}
          </div>
        </div>

        {/* Disease Details */}
        <div className="lg:col-span-3 space-y-4">
          {selectedDisease ? (
            <>
              <div className="glass-card p-5">
                <h2 className="text-xl font-bold text-white mb-1">
                  {selectedDisease}
                </h2>
                <p className="text-dark-400 text-sm">
                  {diseases.find((d) => d.name === selectedDisease)
                    ?.description || "Disease surveillance data"}
                </p>
              </div>

              {/* Predictions Chart */}
              {predictions.length > 0 && (
                <div className="glass-card p-5">
                  <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-blue-500" />
                    7-Day Case Prediction
                  </h3>
                  <TrendChart
                    labels={predictions.map((p: any) =>
                      new Date(p.prediction_date).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                      }),
                    )}
                    datasets={[
                      {
                        label: "Predicted Cases",
                        data: predictions.map(
                          (p: any) => p.predicted_cases || 0,
                        ),
                        color: "#6366f1",
                      },
                      {
                        label: "Upper Bound",
                        data: predictions.map(
                          (p: any) => p.confidence_upper || 0,
                        ),
                        color: "#ef4444",
                        fill: false,
                      },
                      {
                        label: "Lower Bound",
                        data: predictions.map(
                          (p: any) => p.confidence_lower || 0,
                        ),
                        color: "#10b981",
                        fill: false,
                      },
                    ]}
                    height={280}
                  />
                  <div className="flex items-center gap-4 mt-3 text-[11px] text-dark-500">
                    <span>
                      Model:{" "}
                      {predictions[0]?.model_type?.toUpperCase() || "LSTM"}
                    </span>
                    {predictions.some((p: any) => p.is_anomaly) && (
                      <span className="text-red-400 flex items-center gap-1">
                        <AlertTriangle className="w-3 h-3" />
                        Anomaly detected
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Outbreaks */}
              <div>
                <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-red-500" />
                  Outbreak Reports ({outbreaks.length})
                </h3>
                <AlertFeed outbreaks={outbreaks} maxItems={20} />
              </div>
            </>
          ) : (
            <div className="glass-card p-12 text-center">
              <Activity className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-white mb-2">
                Select a Disease
              </h3>
              <p className="text-dark-400 text-sm">
                Choose a disease from the list or search to view detailed
                surveillance data.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
