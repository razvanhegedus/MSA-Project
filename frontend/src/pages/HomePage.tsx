import React, { useState } from 'react';
import { Search, MapPin, SlidersHorizontal, Loader2, AlertCircle } from 'lucide-react';
import MobileHeader from '../components/layout/MobileHeader';
import PitchCard from '../components/pitch/PitchCard';
import { useVenues } from '../api/venues';
import { SurfaceType, VenueResponse } from '../types/api';
import { useVenuePitches } from '../api/venues';

// ─── Venue row expanded with pitches ─────────────────────────────────────────
const VenuePitchRow: React.FC<{ venue: VenueResponse; surfaceFilter?: SurfaceType }> = ({
  venue,
  surfaceFilter,
}) => {
  const { data: pitches = [], isLoading } = useVenuePitches(venue.id);

  const filtered = surfaceFilter
    ? pitches.filter((p) => p.surface_type === surfaceFilter)
    : pitches;

  const active = filtered.filter((p) => p.is_active);
  if (!isLoading && active.length === 0) return null;

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1.5 px-1">
        <MapPin className="w-3.5 h-3.5 text-slate-400" />
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
          {venue.name} · {venue.city}
        </span>
      </div>
      {isLoading ? (
        <div className="flex items-center justify-center py-4">
          <Loader2 className="w-5 h-5 animate-spin text-slate-300" />
        </div>
      ) : (
        active.map((pitch) => (
          <PitchCard
            key={pitch.id}
            pitch={pitch}
            venueName={venue.name}
            venueCity={venue.city}
            venueAddress={venue.address}
          />
        ))
      )}
    </div>
  );
};

// ─── Surface filter pills ─────────────────────────────────────────────────────
const SURFACE_PILLS: Array<{ value: SurfaceType | undefined; label: string }> = [
  { value: undefined, label: 'All' },
  { value: 'SYNTHETIC_3G', label: '3G Synthetic' },
  { value: 'INDOOR_TARAFLEX', label: 'Indoor' },
  { value: 'NATURAL_GRASS', label: 'Grass' },
  { value: 'HYBRID', label: 'Hybrid' },
];

const HomePage: React.FC = () => {
  const [city, setCity] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [surfaceFilter, setSurfaceFilter] = useState<SurfaceType | undefined>(undefined);
  const [showFilters, setShowFilters] = useState(false);

  const { data: venues = [], isLoading, isError } = useVenues(city || undefined, surfaceFilter);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCity(searchInput.trim());
  };

  return (
    <>
      <MobileHeader
        title="Pitchup ⚽"
        rightElement={
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center justify-center w-9 h-9 rounded-xl transition-all ${
              surfaceFilter ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            <SlidersHorizontal className="w-4 h-4" />
          </button>
        }
      />

      {/* Search bar */}
      <div className="px-4 pt-3 pb-2">
        <form onSubmit={handleSearch} className="relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search city (e.g. Cluj, Timișoara…)"
            className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 bg-white text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-emerald-500 focus:bg-white"
          />
        </form>
      </div>

      {/* Surface filter pills */}
      {showFilters && (
        <div className="flex gap-2 overflow-x-auto no-scrollbar px-4 pb-3">
          {SURFACE_PILLS.map(({ value, label }) => (
            <button
              key={label}
              onClick={() => setSurfaceFilter(value)}
              className={`flex-shrink-0 px-3.5 py-1.5 rounded-full text-xs font-semibold border transition-all ${
                surfaceFilter === value
                  ? 'bg-slate-900 text-white border-slate-900'
                  : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      )}

      {/* Content */}
      <div className="flex-1 px-4 py-2 space-y-5 overflow-y-auto">
        {isLoading && (
          <div className="flex flex-col items-center justify-center py-20 gap-3 text-slate-400">
            <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
            <p className="text-sm">Loading pitches…</p>
          </div>
        )}

        {isError && (
          <div className="flex flex-col items-center justify-center py-16 gap-2 text-slate-400">
            <AlertCircle className="w-8 h-8 text-red-400" />
            <p className="text-sm font-medium text-red-500">Could not load venues</p>
            <p className="text-xs text-slate-400">Check your connection or try again</p>
          </div>
        )}

        {!isLoading && !isError && venues.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 gap-2 text-slate-400">
            <MapPin className="w-10 h-10 opacity-30" />
            <p className="text-sm font-medium">No venues found</p>
            <p className="text-xs">Try searching a different city</p>
          </div>
        )}

        {!isLoading &&
          venues.map((venue) => (
            <VenuePitchRow key={venue.id} venue={venue} surfaceFilter={surfaceFilter} />
          ))}
      </div>
    </>
  );
};

export default HomePage;

