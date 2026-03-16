'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { MapDataPoint } from '@/lib/api';

// Dynamically import the ENTIRE map component as one unit (no SSR)
const LeafletMap = dynamic(() => import('./LeafletMap'), {
  ssr: false,
  loading: () => (
    <div className="glass-card flex items-center justify-center" style={{ height: '500px' }}>
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-dark-400 text-sm">Loading map...</p>
      </div>
    </div>
  ),
});

interface OutbreakMapProps {
  data: MapDataPoint[];
  height?: string;
  onCountryClick?: (country: string) => void;
}

export default function OutbreakMap({ data, height = '500px', onCountryClick }: OutbreakMapProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="glass-card flex items-center justify-center" style={{ height }}>
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-dark-400 text-sm">Loading map...</p>
        </div>
      </div>
    );
  }

  return <LeafletMap data={data} height={height} onCountryClick={onCountryClick} />;
}
