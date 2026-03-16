'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { api, Country, Outbreak, CaseStat } from '@/lib/api';
import StatsCard from '@/components/StatsCard';
import AlertFeed from '@/components/AlertFeed';
import TrendChart from '@/components/TrendChart';

export default function CountriesContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const nameParam = searchParams.get('name') || '';

  const [countries, setCountries] = useState<Country[]>([]);
  const [selectedCountry, setSelectedCountry] = useState<string>(nameParam);
  const [countryDetail, setCountryDetail] = useState<{
    country: Country; outbreaks: Outbreak[]; case_statistics: CaseStat[];
  } | null>(null);
  const [filterContinent, setFilterContinent] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCountries();
  }, []);

  useEffect(() => {
    if (nameParam) {
      setSelectedCountry(nameParam);
    }
  }, [nameParam]);

  useEffect(() => {
    if (selectedCountry) {
      loadCountryDetails(selectedCountry);
    }
  }, [selectedCountry]);

  async function loadCountries() {
    try {
      const data = await api.getCountries();
      setCountries(data);
    } catch (err) {
      console.error('Failed to load countries:', err);
    } finally {
      setLoading(false);
    }
  }

  async function loadCountryDetails(name: string) {
    try {
      const detail = await api.getCountryDetails(name);
      setCountryDetail(detail);
    } catch (err) {
      console.error('Failed to load country details:', err);
    }
  }

  const filteredCountries = countries.filter(c => {
    const matchesSearch = !searchQuery || c.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesContinent = !filterContinent || c.continent === filterContinent;
    return matchesSearch && matchesContinent;
  });

  const continents = [...new Set(countries.map(c => c.continent).filter(Boolean))].sort();

  const caseStats = countryDetail?.case_statistics || [];
  const sortedStats = [...caseStats].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">🗺️ Country Intelligence</h1>
        <p className="text-dark-400 text-sm mt-1">Disease surveillance data by country</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Country List */}
        <div className="lg:col-span-1 space-y-3">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter countries..."
            className="w-full px-3 py-2 rounded-lg text-sm bg-white/5 border border-white/10 text-white placeholder-dark-400 outline-none focus:border-primary-500/50 transition-all"
          />
          <div className="flex flex-wrap gap-1">
            <button
              onClick={() => setFilterContinent('')}
              className={`px-2 py-1 rounded text-[11px] transition-all ${
                !filterContinent ? 'bg-primary-600/30 text-primary-300 border border-primary-500/30' : 'text-dark-400 hover:text-white hover:bg-white/5'
              }`}
            >
              All
            </button>
            {continents.map(c => (
              <button
                key={c}
                onClick={() => setFilterContinent(c === filterContinent ? '' : c!)}
                className={`px-2 py-1 rounded text-[11px] transition-all ${
                  filterContinent === c ? 'bg-primary-600/30 text-primary-300 border border-primary-500/30' : 'text-dark-400 hover:text-white hover:bg-white/5'
                }`}
              >
                {c}
              </button>
            ))}
          </div>

          <div className="space-y-1 max-h-[520px] overflow-y-auto pr-1">
            {filteredCountries.map((country) => (
              <button
                key={country.id}
                onClick={() => setSelectedCountry(country.name)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all duration-200 flex items-center justify-between
                  ${selectedCountry === country.name
                    ? 'bg-primary-600/20 border border-primary-500/30 text-white'
                    : 'text-dark-300 hover:bg-white/5 hover:text-white border border-transparent'
                  }`}
              >
                <div>
                  <span className="font-medium">{country.name}</span>
                  {country.continent && (
                    <span className="block text-[11px] text-dark-500">{country.continent}</span>
                  )}
                </div>
                {country.iso2_code && (
                  <span className="text-xs text-dark-500">{country.iso2_code}</span>
                )}
              </button>
            ))}
            {filteredCountries.length === 0 && (
              <p className="text-dark-400 text-sm text-center py-4">No countries found</p>
            )}
          </div>
        </div>

        {/* Country Details */}
        <div className="lg:col-span-3 space-y-4">
          {countryDetail ? (
            <>
              <div className="glass-card p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-bold text-white">{countryDetail.country.name}</h2>
                    <p className="text-dark-400 text-sm mt-1">
                      {countryDetail.country.continent}
                      {countryDetail.country.population && ` • Pop. ${(countryDetail.country.population / 1e6).toFixed(1)}M`}
                      {countryDetail.country.iso_code && ` • ${countryDetail.country.iso_code}`}
                    </p>
                  </div>
                </div>
              </div>

              {sortedStats.length > 0 && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <StatsCard title="Total Cases" value={sortedStats[sortedStats.length - 1]?.total_cases || 0} icon="📊" variant="warning" />
                  <StatsCard title="Total Deaths" value={sortedStats[sortedStats.length - 1]?.total_deaths || 0} icon="💀" variant="danger" />
                  <StatsCard title="Recovered" value={sortedStats[sortedStats.length - 1]?.total_recovered || 0} icon="💚" variant="success" />
                  <StatsCard title="Active" value={sortedStats[sortedStats.length - 1]?.active_cases || 0} icon="🔴" variant="default" />
                </div>
              )}

              {sortedStats.length > 1 && (
                <div className="glass-card p-5">
                  <h3 className="text-sm font-semibold text-white mb-4">📈 Case Trend</h3>
                  <TrendChart
                    labels={sortedStats.map(s => new Date(s.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }))}
                    datasets={[
                      { label: 'New Cases', data: sortedStats.map(s => s.new_cases), color: '#f59e0b' },
                      { label: 'New Deaths', data: sortedStats.map(s => s.new_deaths), color: '#ef4444' },
                    ]}
                    height={300}
                  />
                </div>
              )}

              {countryDetail.outbreaks.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-white mb-3">
                    🚨 Outbreak Reports ({countryDetail.outbreaks.length})
                  </h3>
                  <AlertFeed outbreaks={countryDetail.outbreaks} maxItems={10} />
                </div>
              )}

              {countryDetail.outbreaks.length === 0 && sortedStats.length === 0 && (
                <div className="glass-card p-8 text-center">
                  <p className="text-dark-400 text-sm">No detailed data available yet. Data will populate after ingestion runs.</p>
                </div>
              )}
            </>
          ) : (
            <div className="glass-card p-12 text-center">
              <p className="text-4xl mb-4">🗺️</p>
              <h3 className="text-lg font-semibold text-white mb-2">Select a Country</h3>
              <p className="text-dark-400 text-sm">Choose a country to view detailed surveillance data and case statistics.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
