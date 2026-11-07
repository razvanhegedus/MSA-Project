import React from 'react';
import { MapPin, Zap, Leaf, Wind, Grid3X3, ArrowRight, ShieldCheck } from 'lucide-react';
import { PitchResponse, SurfaceType } from '../../types/api';
import { useNavigate } from 'react-router-dom';

interface PitchCardProps {
  pitch: PitchResponse;
  venueName?: string;
  venueCity?: string;
  venueAddress?: string;
}

const SURFACE_CONFIG: Record<
  SurfaceType,
  { label: string; icon: React.ReactNode; color: string; image: string }
> = {
  SYNTHETIC_3G: {
    label: '3G Synthetic',
    icon: <Zap className="w-3 h-3" />,
    color: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    image:
      'https://images.unsplash.com/photo-1529900748604-07564a03e7a6?auto=format&fit=crop&w=800&q=80',
  },
  INDOOR_TARAFLEX: {
    label: 'Indoor Taraflex',
    icon: <Grid3X3 className="w-3 h-3" />,
    color: 'bg-purple-100 text-purple-800 border-purple-200',
    image:
      'https://images.unsplash.com/photo-1551958219-acbc608c6377?auto=format&fit=crop&w=800&q=80',
  },
  NATURAL_GRASS: {
    label: 'Natural Grass',
    icon: <Leaf className="w-3 h-3" />,
    color: 'bg-green-100 text-green-800 border-green-200',
    image:
      'https://images.unsplash.com/photo-1575361204480-aadea25e6e68?auto=format&fit=crop&w=800&q=80',
  },
  HYBRID: {
    label: 'Hybrid Turf',
    icon: <Wind className="w-3 h-3" />,
    color: 'bg-amber-100 text-amber-800 border-amber-200',
    image:
      'https://images.unsplash.com/photo-1518091043644-c1d4457512c6?auto=format&fit=crop&w=800&q=80',
  },
};

const PitchCard: React.FC<PitchCardProps> = ({ pitch, venueName, venueCity, venueAddress }) => {
  const navigate = useNavigate();
  const surface = SURFACE_CONFIG[pitch.surface_type] ?? SURFACE_CONFIG.SYNTHETIC_3G;

  return (
    <div
      onClick={() => navigate(`/pitches/${pitch.id}`)}
      className="group bg-white border border-slate-200 rounded-2xl overflow-hidden hover:border-slate-300 hover:shadow-md active:scale-[0.99] transition-all cursor-pointer flex flex-col h-full"
    >
      {/* Card Visual Header with Image */}
      <div className="relative h-40 sm:h-44 w-full bg-slate-900 overflow-hidden">
        <img
          src={surface.image}
          alt={pitch.name}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300 opacity-90"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />

        {/* Top Badges */}
        <div className="absolute top-3 left-3 right-3 flex items-center justify-between gap-2">
          <span
            className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold border backdrop-blur-md shadow-sm ${surface.color}`}
          >
            {surface.icon}
            {surface.label}
          </span>

          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-white/90 text-slate-900 backdrop-blur-md shadow-sm">
            {pitch.team_size_capacity}v{pitch.team_size_capacity}
          </span>
        </div>

        {/* Bottom Banner inside Image */}
        <div className="absolute bottom-2.5 left-3 right-3 flex items-end justify-between text-white">
          <div className="min-w-0 pr-2">
            <h3 className="text-base font-bold text-white truncate drop-shadow-sm group-hover:text-emerald-300 transition-colors">
              {pitch.name}
            </h3>
            {venueName && (
              <p className="text-xs text-slate-200 truncate font-medium drop-shadow-sm">
                {venueName}
              </p>
            )}
          </div>

          <div className="flex-shrink-0 text-right bg-slate-900/80 backdrop-blur-md px-2.5 py-1 rounded-xl border border-white/10">
            <span className="text-sm font-black text-emerald-400">{pitch.hourly_rate}</span>
            <span className="text-[10px] text-slate-300"> RON/h</span>
          </div>
        </div>
      </div>

      {/* Card Body & Facility Meta */}
      <div className="p-4 flex flex-col justify-between flex-1 gap-3">
        <div className="space-y-2">
          {/* Location info */}
          {(venueCity || venueAddress) && (
            <div className="flex items-center gap-1.5 text-xs text-slate-500">
              <MapPin className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
              <span className="truncate">{venueAddress || venueCity}</span>
            </div>
          )}

          {/* Quick Perks / Features */}
          <div className="flex items-center gap-2 text-[11px] text-slate-600 font-medium">
            <span className="flex items-center gap-1">
              <ShieldCheck className="w-3 h-3 text-emerald-600" /> Instant Booking
            </span>
            <span>·</span>
            <span>Floodlights</span>
            <span>·</span>
            <span>Changing Rooms</span>
          </div>
        </div>

        {/* Action Row */}
        <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500">
            {pitch.is_active ? (
              <span className="text-emerald-600 font-bold flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                Slots Available Today
              </span>
            ) : (
              <span className="text-red-500 font-semibold">Closed</span>
            )}
          </span>

          <span className="inline-flex items-center gap-1 text-xs font-bold text-slate-900 group-hover:text-emerald-700 transition-colors">
            View Schedule
            <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
          </span>
        </div>
      </div>
    </div>
  );
};

export default PitchCard;
