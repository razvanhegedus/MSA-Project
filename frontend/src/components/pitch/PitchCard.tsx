import React from 'react';
import { MapPin, Zap, Leaf, Wind, Grid3X3 } from 'lucide-react';
import { PitchResponse, SurfaceType } from '../../types/api';
import { useNavigate } from 'react-router-dom';

interface PitchCardProps {
  pitch: PitchResponse;
  venueName?: string;
  venueCity?: string;
  venueAddress?: string;
}

const SURFACE_CONFIG: Record<SurfaceType, { label: string; icon: React.ReactNode; color: string }> = {
  SYNTHETIC_3G: { label: '3G Synthetic', icon: <Zap className="w-3 h-3" />, color: 'bg-blue-100 text-blue-700' },
  INDOOR_TARAFLEX: { label: 'Indoor Taraflex', icon: <Grid3X3 className="w-3 h-3" />, color: 'bg-purple-100 text-purple-700' },
  NATURAL_GRASS: { label: 'Natural Grass', icon: <Leaf className="w-3 h-3" />, color: 'bg-green-100 text-green-700' },
  HYBRID: { label: 'Hybrid', icon: <Wind className="w-3 h-3" />, color: 'bg-orange-100 text-orange-700' },
};

const PitchCard: React.FC<PitchCardProps> = ({ pitch, venueName, venueCity, venueAddress }) => {
  const navigate = useNavigate();
  const surface = SURFACE_CONFIG[pitch.surface_type];

  return (
    <button
      onClick={() => navigate(`/pitches/${pitch.id}`)}
      className="w-full text-left bg-white border border-slate-200 rounded-2xl p-4 hover:border-slate-300 hover:shadow-sm active:scale-[0.99] transition-all"
    >
      {/* Top row */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-bold text-slate-900 truncate">{pitch.name}</h3>
          {venueName && (
            <p className="text-xs text-slate-500 mt-0.5 truncate font-medium">{venueName}</p>
          )}
        </div>
        <div className="flex-shrink-0 text-right">
          <span className="text-base font-bold text-slate-900">{pitch.hourly_rate}</span>
          <span className="text-xs text-slate-500"> RON/h</span>
        </div>
      </div>

      {/* Tags row */}
      <div className="flex items-center gap-2 flex-wrap">
        <span
          className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold ${surface.color}`}
        >
          {surface.icon}
          {surface.label}
        </span>
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-600">
          {pitch.team_size_capacity}v{pitch.team_size_capacity}
        </span>
        {!pitch.is_active && (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-600">
            Closed
          </span>
        )}
      </div>

      {/* Location */}
      {(venueCity || venueAddress) && (
        <div className="flex items-center gap-1.5 mt-2.5 text-xs text-slate-400">
          <MapPin className="w-3 h-3 flex-shrink-0" />
          <span className="truncate">{venueAddress || venueCity}</span>
        </div>
      )}
    </button>
  );
};

export default PitchCard;

