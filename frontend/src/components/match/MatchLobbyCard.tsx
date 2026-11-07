import React from 'react';
import { Users, MapPin, Clock, Shield, Star } from 'lucide-react';
import { MatchResponse } from '../../types/api';

interface MatchLobbyCardProps {
  match: MatchResponse;
  onJoin: (matchId: string) => void;
  isCurrentUserOrganizer?: boolean;
}

const MatchLobbyCard: React.FC<MatchLobbyCardProps> = ({
  match,
  onJoin,
  isCurrentUserOrganizer = false,
}) => {
  const spotsLeft = match.target_players - match.current_players_count;
  const fillPercent = Math.min(
    100,
    Math.round((match.current_players_count / match.target_players) * 100)
  );

  const formatScheduled = (iso: string) =>
    new Date(iso).toLocaleString('en-GB', {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    });

  const isFull = match.status === 'FULL' || spotsLeft <= 0;

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-4 space-y-3">
      {/* Header */}
      <div className="flex items-start gap-2 justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            {isCurrentUserOrganizer && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-700">
                <Star className="w-2.5 h-2.5" /> HOST
              </span>
            )}
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold ${
                isFull
                  ? 'bg-slate-100 text-slate-500'
                  : 'bg-amber-100 text-amber-700'
              }`}
            >
              {isFull ? 'FULL' : `${spotsLeft} SPOT${spotsLeft !== 1 ? 'S' : ''} LEFT`}
            </span>
          </div>
          <h3 className="text-sm font-bold text-slate-900 truncate">
            {match.venue_name ?? 'Venue'} · {match.pitch_name ?? 'Pitch'}
          </h3>
        </div>
        <div className="flex-shrink-0 flex flex-col items-end gap-1">
          <span className="text-xs font-bold text-slate-700">
            {match.current_players_count}/{match.target_players}
          </span>
          <Users className="w-4 h-4 text-slate-400" />
        </div>
      </div>

      {/* Fill bar */}
      <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${
            isFull ? 'bg-slate-400' : fillPercent >= 80 ? 'bg-amber-500' : 'bg-emerald-500'
          }`}
          style={{ width: `${fillPercent}%` }}
        />
      </div>

      {/* Meta */}
      <div className="flex items-center gap-4 text-xs text-slate-500">
        <span className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          {formatScheduled(match.scheduled_at)}
        </span>
        {match.city && (
          <span className="flex items-center gap-1">
            <MapPin className="w-3 h-3" />
            {match.city}
          </span>
        )}
      </div>

      {/* Needed positions */}
      {match.needed_positions && match.needed_positions.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          <Shield className="w-3.5 h-3.5 text-slate-400" />
          {match.needed_positions.map((pos) => (
            <span
              key={pos}
              className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-600"
            >
              {pos}
            </span>
          ))}
        </div>
      )}

      {/* Description */}
      {match.description && (
        <p className="text-xs text-slate-500 leading-relaxed line-clamp-2">{match.description}</p>
      )}

      {/* Join Button */}
      <button
        onClick={() => onJoin(match.id)}
        disabled={isFull || isCurrentUserOrganizer}
        className={`w-full h-11 rounded-xl font-bold text-sm transition-all active:scale-[0.98] ${
          isFull || isCurrentUserOrganizer
            ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
            : 'bg-slate-900 text-white hover:bg-slate-800 shadow-sm'
        }`}
      >
        {isCurrentUserOrganizer ? 'Your Lobby' : isFull ? 'Lobby Full' : '+ Join Match'}
      </button>
    </div>
  );
};

export default MatchLobbyCard;

