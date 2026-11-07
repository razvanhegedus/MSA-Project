import React, { useState, useMemo } from 'react';
import {
  Search,
  MapPin,
  SlidersHorizontal,
  Loader2,
  AlertCircle,
  X,
  RotateCcw,
  Sparkles,
  ArrowUpDown,
  Check,
} from 'lucide-react';
import MobileHeader from '../components/layout/MobileHeader';
import PitchCard from '../components/pitch/PitchCard';
import { useVenues } from '../api/venues';
import { SurfaceType, PitchResponse, VenueResponse } from '../types/api';

const SURFACE_OPTIONS: Array<{ value: SurfaceType | 'ALL'; label: string; dotColor: string }> = [
  { value: 'ALL', label: 'All Surfaces', dotColor: 'bg-slate-400' },
  { value: 'SYNTHETIC_3G', label: '3G Synthetic Turf', dotColor: 'bg-emerald-500' },
  { value: 'INDOOR_TARAFLEX', label: 'Indoor Taraflex', dotColor: 'bg-purple-500' },
  { value: 'NATURAL_GRASS', label: 'Natural Grass', dotColor: 'bg-green-500' },
  { value: 'HYBRID', label: 'Hybrid Turf', dotColor: 'bg-amber-500' },
];

const QUICK_CITIES = ['All', 'Cluj-Napoca', 'Timișoara', 'București', 'Iași', 'Brașov'];

type SortOption = 'RECOMMENDED' | 'PRICE_ASC' | 'PRICE_DESC' | 'CAPACITY_DESC';

interface PitchWithVenueMeta {
  pitch: PitchResponse;
  venue: VenueResponse;
}

const PitchListPage: React.FC = () => {
  // Filter States
  const [searchInput, setSearchInput] = useState('');
  const [activeCity, setActiveCity] = useState('');
  const [selectedSurface, setSelectedSurface] = useState<SurfaceType | 'ALL'>('ALL');
  const [environmentFilter, setEnvironmentFilter] = useState<'ALL' | 'INDOOR' | 'OUTDOOR'>('ALL');
  const [teamSizeFilter, setTeamSizeFilter] = useState<number | 'ALL'>('ALL');
  const [maxPrice, setMaxPrice] = useState<number>(500);
  const [sortBy, setSortBy] = useState<SortOption>('RECOMMENDED');

  // Mobile Filter Drawer State
  const [mobileFilterOpen, setMobileFilterOpen] = useState(false);

  // Queries
  const {
    data: venues = [],
    isLoading,
    isError,
  } = useVenues(activeCity || undefined, selectedSurface !== 'ALL' ? selectedSurface : undefined);

  // Flatten pitches across venues with venue context & deduplicate identical entries
  const allPitchesWithVenue: PitchWithVenueMeta[] = useMemo(() => {
    const list: PitchWithVenueMeta[] = [];
    const seen = new Set<string>();

    venues.forEach((v) => {
      if (v.pitches && v.pitches.length > 0) {
        v.pitches.forEach((p) => {
          const normName = p.name.trim().toLowerCase();
          const normAddress = v.address.trim().toLowerCase();
          const normSurface = p.surface_type.trim().toUpperCase();
          const normRate = Number(p.hourly_rate).toFixed(2);
          const dedupKey = `${normName}|${normAddress}|${normSurface}|${normRate}`;

          if (!seen.has(dedupKey)) {
            seen.add(dedupKey);
            list.push({ pitch: p, venue: v });
          }
        });
      }
    });
    return list;
  }, [venues]);

  // Apply Client-Side Filters (Search keyword, environment, team size, max price, sorting)
  const filteredPitches = useMemo(() => {
    let result = allPitchesWithVenue.filter(({ pitch, venue }) => {
      // Search input keyword (pitch name or venue name or city)
      if (searchInput.trim()) {
        const query = searchInput.toLowerCase();
        const matchName = pitch.name.toLowerCase().includes(query);
        const matchVenue = venue.name.toLowerCase().includes(query);
        const matchCity = venue.city.toLowerCase().includes(query);
        const matchAddress = venue.address.toLowerCase().includes(query);
        if (!matchName && !matchVenue && !matchCity && !matchAddress) return false;
      }

      // Surface
      if (selectedSurface !== 'ALL' && pitch.surface_type !== selectedSurface) {
        return false;
      }

      // Environment (Indoor vs Outdoor)
      if (environmentFilter === 'INDOOR' && pitch.surface_type !== 'INDOOR_TARAFLEX') {
        return false;
      }
      if (environmentFilter === 'OUTDOOR' && pitch.surface_type === 'INDOOR_TARAFLEX') {
        return false;
      }

      // Team Size Capacity
      if (teamSizeFilter !== 'ALL' && pitch.team_size_capacity !== teamSizeFilter) {
        return false;
      }

      // Pricing
      if (Number(pitch.hourly_rate) > maxPrice) {
        return false;
      }

      return true;
    });

    // Sorting
    result = [...result].sort((a, b) => {
      if (sortBy === 'PRICE_ASC') {
        return Number(a.pitch.hourly_rate) - Number(b.pitch.hourly_rate);
      }
      if (sortBy === 'PRICE_DESC') {
        return Number(b.pitch.hourly_rate) - Number(a.pitch.hourly_rate);
      }
      if (sortBy === 'CAPACITY_DESC') {
        return b.pitch.team_size_capacity - a.pitch.team_size_capacity;
      }
      // RECOMMENDED default
      return a.pitch.name.localeCompare(b.pitch.name);
    });

    return result;
  }, [
    allPitchesWithVenue,
    searchInput,
    selectedSurface,
    environmentFilter,
    teamSizeFilter,
    maxPrice,
    sortBy,
  ]);

  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (selectedSurface !== 'ALL') count++;
    if (environmentFilter !== 'ALL') count++;
    if (teamSizeFilter !== 'ALL') count++;
    if (maxPrice < 500) count++;
    if (activeCity) count++;
    return count;
  }, [selectedSurface, environmentFilter, teamSizeFilter, maxPrice, activeCity]);

  const handleResetFilters = () => {
    setSearchInput('');
    setActiveCity('');
    setSelectedSurface('ALL');
    setEnvironmentFilter('ALL');
    setTeamSizeFilter('ALL');
    setMaxPrice(500);
    setSortBy('RECOMMENDED');
  };

  // Reusable Filter Controls Component (Used both in Desktop Sidebar & Mobile Drawer)
  const FilterControlsContent = () => (
    <div className="space-y-6">
      {/* City Chips */}
      <div>
        <label className="text-xs font-bold text-slate-800 uppercase tracking-wider block mb-2.5">
          City Location
        </label>
        <div className="flex flex-wrap gap-1.5">
          {QUICK_CITIES.map((c) => {
            const isSelected = (c === 'All' && !activeCity) || activeCity === c;
            return (
              <button
                key={c}
                type="button"
                onClick={() => setActiveCity(c === 'All' ? '' : c)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
                  isSelected
                    ? 'bg-slate-900 text-white border-slate-900 shadow-sm'
                    : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'
                }`}
              >
                {c}
              </button>
            );
          })}
        </div>
      </div>

      {/* Surface Type */}
      <div>
        <label className="text-xs font-bold text-slate-800 uppercase tracking-wider block mb-2.5">
          Pitch Surface
        </label>
        <div className="space-y-1.5">
          {SURFACE_OPTIONS.map(({ value, label, dotColor }) => {
            const isSelected = selectedSurface === value;
            return (
              <button
                key={value}
                type="button"
                onClick={() => setSelectedSurface(value)}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium border transition-all ${
                  isSelected
                    ? 'bg-emerald-50/70 border-emerald-300 text-emerald-950 font-bold'
                    : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                }`}
              >
                <span className="flex items-center gap-2">
                  <span className={`w-2.5 h-2.5 rounded-full ${dotColor}`} />
                  {label}
                </span>
                {isSelected && <Check className="w-4 h-4 text-emerald-600" />}
              </button>
            );
          })}
        </div>
      </div>

      {/* Environment: Indoor vs Outdoor */}
      <div>
        <label className="text-xs font-bold text-slate-800 uppercase tracking-wider block mb-2.5">
          Facility Type
        </label>
        <div className="grid grid-cols-3 gap-1.5 p-1 bg-slate-100 rounded-xl">
          {(
            [
              { key: 'ALL', label: 'All' },
              { key: 'OUTDOOR', label: 'Outdoor' },
              { key: 'INDOOR', label: 'Indoor' },
            ] as const
          ).map(({ key, label }) => (
            <button
              key={key}
              type="button"
              onClick={() => setEnvironmentFilter(key)}
              className={`py-1.5 rounded-lg text-xs font-semibold transition-all ${
                environmentFilter === key
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Team Size Format */}
      <div>
        <label className="text-xs font-bold text-slate-800 uppercase tracking-wider block mb-2.5">
          Squad Format
        </label>
        <div className="flex flex-wrap gap-1.5">
          {([ 'ALL', 5, 6, 7, 8, 11 ] as const).map((size) => {
            const isSelected = teamSizeFilter === size;
            const label = size === 'ALL' ? 'All Formats' : `${size}v${size}`;
            return (
              <button
                key={String(size)}
                type="button"
                onClick={() => setTeamSizeFilter(size)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
                  isSelected
                    ? 'bg-slate-900 text-white border-slate-900 shadow-sm'
                    : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'
                }`}
              >
                {label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Price Slider */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            Max Hourly Rate
          </label>
          <span className="text-xs font-black text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
            {maxPrice} RON/h
          </span>
        </div>
        <input
          type="range"
          min="100"
          max="500"
          step="10"
          value={maxPrice}
          onChange={(e) => setMaxPrice(Number(e.target.value))}
          className="w-full accent-emerald-600 cursor-pointer"
        />
        <div className="flex justify-between text-[10px] text-slate-400 font-medium mt-1">
          <span>100 RON</span>
          <span>300 RON</span>
          <span>500 RON</span>
        </div>
      </div>

      {/* Reset Action */}
      {activeFilterCount > 0 && (
        <button
          type="button"
          onClick={handleResetFilters}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl border border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-50 text-xs font-semibold transition-colors"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Reset All Filters
        </button>
      )}
    </div>
  );

  return (
    <div className="w-full space-y-6">
      {/* Mobile Header (Hidden on Desktop via lg:hidden) */}
      <MobileHeader
        title="Find a Pitch"
        rightElement={
          <button
            type="button"
            onClick={() => setMobileFilterOpen(true)}
            className={`relative flex items-center justify-center w-9 h-9 rounded-xl transition-all ${
              activeFilterCount > 0
                ? 'bg-emerald-100 text-emerald-800'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            <SlidersHorizontal className="w-4 h-4" />
            {activeFilterCount > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-emerald-600 text-white text-[10px] font-black flex items-center justify-center">
                {activeFilterCount}
              </span>
            )}
          </button>
        }
      />

      {/* Page Title & Search Bar Ribbon */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-5 shadow-sm space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
              Football Pitches & Arenas
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
              Book real-time slots across Romania or split match fees with open lobbies.
            </p>
          </div>

          {/* Quick Stats Pill */}
          <div className="flex items-center gap-2 self-start sm:self-auto">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-50 text-emerald-700 text-xs font-bold border border-emerald-200">
              <Sparkles className="w-3.5 h-3.5" />
              {filteredPitches.length} Pitches Available
            </span>
          </div>
        </div>

        {/* Search Bar Input */}
        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search by arena name, neighborhood, or city (e.g. Cluj, Timișoara)…"
              className="w-full pl-10 pr-10 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-emerald-500 focus:bg-white transition-all"
            />
            {searchInput && (
              <button
                type="button"
                onClick={() => setSearchInput('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Mobile Filter Button trigger next to search bar */}
          <button
            type="button"
            onClick={() => setMobileFilterOpen(true)}
            className="lg:hidden flex items-center gap-2 px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-700 text-xs font-bold hover:bg-slate-100 transition-colors"
          >
            <SlidersHorizontal className="w-4 h-4 text-emerald-600" />
            <span>Filters</span>
            {activeFilterCount > 0 && (
              <span className="w-4 h-4 rounded-full bg-emerald-600 text-white text-[10px] font-black flex items-center justify-center">
                {activeFilterCount}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* ─── Main Content: Desktop 2-Column Split (Left Sidebar Filters + Right Grid) ─── */}
      <div className="flex flex-col lg:flex-row items-start gap-8">
        {/* Left Sidebar Filter Panel (Hidden on Mobile, Sticky on Desktop) */}
        <aside className="hidden lg:block lg:w-72 xl:w-80 flex-shrink-0 bg-white rounded-2xl border border-slate-200 p-5 shadow-sm sticky top-24 self-start">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-5">
            <div className="flex items-center gap-2">
              <SlidersHorizontal className="w-4 h-4 text-emerald-600" />
              <h2 className="text-sm font-bold text-slate-900">Filter Pitches</h2>
            </div>
            {activeFilterCount > 0 && (
              <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                {activeFilterCount} active
              </span>
            )}
          </div>

          <FilterControlsContent />
        </aside>

        {/* Right Area: Results Header, Sort, and Responsive Grid */}
        <div className="flex-1 min-w-0 w-full space-y-5">
          {/* Active Filter Badges & Sort Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 bg-white rounded-2xl border border-slate-200 p-3 sm:px-4 shadow-sm">
            <div className="flex flex-wrap items-center gap-1.5 text-xs">
              <span className="font-bold text-slate-700">
                Showing {filteredPitches.length} {filteredPitches.length === 1 ? 'pitch' : 'pitches'}
              </span>

              {activeCity && (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 font-semibold text-[11px]">
                  📍 {activeCity}
                  <button type="button" onClick={() => setActiveCity('')}>
                    <X className="w-3 h-3 hover:text-slate-900" />
                  </button>
                </span>
              )}

              {selectedSurface !== 'ALL' && (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 font-semibold text-[11px] border border-emerald-200">
                  {selectedSurface.replace(/_/g, ' ')}
                  <button type="button" onClick={() => setSelectedSurface('ALL')}>
                    <X className="w-3 h-3 hover:text-emerald-950" />
                  </button>
                </span>
              )}

              {maxPrice < 500 && (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 font-semibold text-[11px]">
                  ≤ {maxPrice} RON
                  <button type="button" onClick={() => setMaxPrice(500)}>
                    <X className="w-3 h-3 hover:text-slate-900" />
                  </button>
                </span>
              )}
            </div>

            {/* Sort selector */}
            <div className="flex items-center gap-2 text-xs">
              <ArrowUpDown className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-slate-500 font-medium">Sort:</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortOption)}
                aria-label="Sort pitches"
                className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 text-xs font-semibold text-slate-700 focus:outline-none focus:border-emerald-500 cursor-pointer"
              >
                <option value="RECOMMENDED">Recommended</option>
                <option value="PRICE_ASC">Price: Low to High</option>
                <option value="PRICE_DESC">Price: High to Low</option>
                <option value="CAPACITY_DESC">Capacity (Team Size)</option>
              </select>
            </div>
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="flex flex-col items-center justify-center py-24 gap-3 bg-white rounded-2xl border border-slate-200">
              <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
              <p className="text-sm font-semibold text-slate-500">Discovering pitches…</p>
            </div>
          )}

          {/* Error State */}
          {isError && (
            <div className="flex flex-col items-center justify-center py-20 gap-2 bg-white rounded-2xl border border-slate-200 text-slate-400">
              <AlertCircle className="w-8 h-8 text-red-400" />
              <p className="text-sm font-bold text-red-500">Could not load pitches</p>
              <p className="text-xs text-slate-400">Please check your connection and retry</p>
            </div>
          )}

          {/* Empty State */}
          {!isLoading && !isError && filteredPitches.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 gap-3 bg-white rounded-2xl border border-dashed border-slate-200 p-8 text-center">
              <div className="w-12 h-12 rounded-2xl bg-slate-100 flex items-center justify-center text-slate-400">
                <MapPin className="w-6 h-6" />
              </div>
              <div>
                <p className="text-base font-bold text-slate-800">No pitches match your filters</p>
                <p className="text-xs text-slate-400 mt-1 max-w-sm">
                  Try adjusting the surface type, expanding your city radius, or raising the price
                  ceiling.
                </p>
              </div>
              <button
                type="button"
                onClick={handleResetFilters}
                className="mt-2 px-4 py-2 rounded-xl bg-slate-900 text-white text-xs font-bold hover:bg-slate-800 transition-colors"
              >
                Clear All Filters
              </button>
            </div>
          )}

          {/* Responsive Cards Grid: 1 col on mobile, 2 on md, 3 on lg/xl */}
          {!isLoading && !isError && filteredPitches.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredPitches.map(({ pitch, venue }) => (
                <PitchCard
                  key={pitch.id}
                  pitch={pitch}
                  venueName={venue.name}
                  venueCity={venue.city}
                  venueAddress={venue.address}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Mobile Slide-Up Filters Bottom Drawer */}
      {mobileFilterOpen && (
        <div
          className="fixed inset-0 z-50 flex flex-col justify-end bg-black/50 backdrop-blur-sm lg:hidden"
          onClick={() => setMobileFilterOpen(false)}
        >
          <div
            className="max-w-md mx-auto w-full bg-white rounded-t-3xl shadow-2xl max-h-[85vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Drawer Drag Handle */}
            <div className="flex justify-center pt-3 pb-1">
              <div className="w-10 h-1 rounded-full bg-slate-200" />
            </div>

            {/* Drawer Header */}
            <div className="flex items-center justify-between px-5 py-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <SlidersHorizontal className="w-4 h-4 text-emerald-600" />
                <h3 className="text-sm font-bold text-slate-900">Filter Pitches</h3>
              </div>
              <button
                type="button"
                onClick={() => setMobileFilterOpen(false)}
                className="w-8 h-8 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center hover:bg-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Drawer Scrollable Body */}
            <div className="p-5 overflow-y-auto flex-1">
              <FilterControlsContent />
            </div>

            {/* Drawer Footer Actions */}
            <div className="p-4 border-t border-slate-100 flex gap-2">
              <button
                type="button"
                onClick={handleResetFilters}
                className="flex-1 h-11 rounded-xl border border-slate-200 text-slate-700 text-xs font-bold hover:bg-slate-50 transition-colors"
              >
                Reset
              </button>
              <button
                type="button"
                onClick={() => setMobileFilterOpen(false)}
                className="flex-[2] h-11 rounded-xl bg-slate-900 text-white text-xs font-bold hover:bg-slate-800 transition-colors shadow-sm"
              >
                Show {filteredPitches.length} Pitches
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PitchListPage;

