'use client';

import { Outbreak } from '@/lib/api';

interface AlertFeedProps {
  outbreaks: Outbreak[];
  maxItems?: number;
}

const severityConfig: Record<string, { color: string; bg: string; label: string }> = {
  critical: { color: 'text-red-400', bg: 'bg-red-500/20', label: 'CRITICAL' },
  high: { color: 'text-orange-400', bg: 'bg-orange-500/20', label: 'HIGH' },
  medium: { color: 'text-yellow-400', bg: 'bg-yellow-500/20', label: 'MEDIUM' },
  low: { color: 'text-green-400', bg: 'bg-green-500/20', label: 'LOW' },
};

function timeAgo(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

export default function AlertFeed({ outbreaks, maxItems = 10 }: AlertFeedProps) {
  const items = outbreaks.slice(0, maxItems);

  if (items.length === 0) {
    return (
      <div className="glass-card p-6 text-center">
        <p className="text-dark-400 text-sm">No active alerts</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {items.map((outbreak, idx) => {
        const severity = severityConfig[outbreak.severity || 'medium'];
        return (
          <div
            key={outbreak.id || idx}
            className="glass-card p-4 animate-slide-up"
            style={{ animationDelay: `${idx * 50}ms` }}
          >
            <div className="flex items-start gap-3">
              <div className="mt-0.5">
                <div className={`pulse-dot ${outbreak.severity === 'critical' ? '' : 'bg-yellow-500'}`} 
                     style={outbreak.severity === 'low' ? { background: '#22c55e' } : {}} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <span className="font-semibold text-sm text-white">
                    {outbreak.disease_name}
                  </span>
                  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${severity.bg} ${severity.color}`}>
                    {severity.label}
                  </span>
                </div>
                <p className="text-xs text-dark-400 mb-1.5 line-clamp-2">
                  {outbreak.description || `Outbreak reported in ${outbreak.country_name || 'Unknown location'}`}
                </p>
                <div className="flex items-center gap-3 text-[11px] text-dark-500">
                  {outbreak.country_name && (
                    <span className="flex items-center gap-1">
                      📍 {outbreak.country_name}
                    </span>
                  )}
                  <span>{timeAgo(outbreak.report_date)}</span>
                  <span className="text-dark-600">via {outbreak.source}</span>
                </div>
                {(outbreak.cases_count || outbreak.deaths_count) && (
                  <div className="flex items-center gap-3 mt-2 text-xs">
                    {outbreak.cases_count && (
                      <span className="text-yellow-400">
                        {outbreak.cases_count.toLocaleString()} cases
                      </span>
                    )}
                    {outbreak.deaths_count && (
                      <span className="text-red-400">
                        {outbreak.deaths_count.toLocaleString()} deaths
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
