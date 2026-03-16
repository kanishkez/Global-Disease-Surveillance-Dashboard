'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function SearchBar() {
  const [query, setQuery] = useState('');
  const [focused, setFocused] = useState(false);
  const router = useRouter();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/diseases?q=${encodeURIComponent(query.trim())}`);
      setQuery('');
    }
  };

  return (
    <form onSubmit={handleSearch} className="relative">
      <div className={`relative transition-all duration-300 ${focused ? 'scale-[1.02]' : ''}`}>
        <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder="Search diseases, countries..."
          className="w-full pl-10 pr-4 py-2 rounded-lg text-sm bg-white/5 border border-white/10 
                     text-white placeholder-dark-400 outline-none
                     focus:border-primary-500/50 focus:bg-white/8 focus:ring-1 focus:ring-primary-500/20
                     transition-all duration-200"
        />
      </div>
    </form>
  );
}
