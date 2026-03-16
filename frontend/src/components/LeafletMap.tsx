'use client';

import { MapContainer, TileLayer, CircleMarker, Popup, Tooltip } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { MapDataPoint } from '@/lib/api';

interface LeafletMapProps {
  data: MapDataPoint[];
  height?: string;
  onCountryClick?: (country: string) => void;
}

const severityColors: Record<string, string> = {
  critical: '#ff1744',
  high: '#ff6d00',
  medium: '#ffea00',
  low: '#00e676',
};

export default function LeafletMap({ data, height = '500px', onCountryClick }: LeafletMapProps) {
  return (
    <div className="glass-card overflow-hidden" style={{ height }}>
      <MapContainer
        center={[20, 10]}
        zoom={2}
        style={{ height: '100%', width: '100%', borderRadius: '12px' }}
        scrollWheelZoom={true}
        zoomControl={true}
        minZoom={2}
        maxZoom={8}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        {data.map((point, idx) => {
          const color = severityColors[point.severity || 'low'] || '#22c55e';
          const radius = Math.max(5, Math.min(25, Math.log10(point.total_cases + 1) * 3));

          return (
            <CircleMarker
              key={`${point.country_name}-${idx}`}
              center={[point.latitude, point.longitude]}
              radius={radius}
              pathOptions={{
                color: color,
                fillColor: color,
                fillOpacity: 0.6,
                weight: 2,
                opacity: 1,
              }}
              eventHandlers={{
                click: () => onCountryClick?.(point.country_name),
              }}
            >
              <Popup>
                <div className="min-w-[180px]">
                  <h3 className="font-bold text-sm mb-2">{point.country_name}</h3>
                  <div className="space-y-1 text-xs">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Cases:</span>
                      <span className="font-semibold">{point.total_cases.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Deaths:</span>
                      <span className="font-semibold text-red-400">{point.total_deaths.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Outbreaks:</span>
                      <span className="font-semibold text-orange-400">{point.active_outbreaks}</span>
                    </div>
                    {point.diseases.length > 0 && (
                      <div className="pt-1 border-t border-gray-600">
                        <span className="text-gray-400">Diseases: </span>
                        <span className="text-yellow-400">{point.diseases.join(', ')}</span>
                      </div>
                    )}
                  </div>
                </div>
              </Popup>
              <Tooltip direction="top" offset={[0, -10]} opacity={0.95}>
                <span className="text-xs font-medium">{point.country_name}</span>
              </Tooltip>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
}
