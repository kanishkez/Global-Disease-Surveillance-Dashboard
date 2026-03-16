'use client';

import { Suspense } from 'react';
import DiseasesContent from './DiseasesContent';

export default function DiseasesPage() {
  return (
    <Suspense fallback={
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
      </div>
    }>
      <DiseasesContent />
    </Suspense>
  );
}
