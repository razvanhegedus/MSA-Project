import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Loader2, AlertCircle, Users, Shield, Sparkles, CheckCircle2, X } from 'lucide-react';
import MobileHeader from '../components/layout/MobileHeader';
import MatchLobbyCard from '../components/match/MatchLobbyCard';
import JoinMatchModal from '../components/match/JoinMatchModal';
import { useOpenMatches, useJoinMatch } from '../api/matches';
import { JoinMatchPayload } from '../types/api';
import { useAuth } from '../context/AuthContext';

type MatchTypeTab = 'OPEN_LOBBY' | 'SQUAD_CHALLENGE';
type RoleFilterType = 'ALL' | 'GOALKEEPER' | 'DEFENDER' | 'MIDFIELDER' | 'FORWARD';

const MatchesPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const highlightId = searchParams.get('highlight');
  const { user } = useAuth();

  const [activeTab, setActiveTab] = useState<MatchTypeTab>('OPEN_LOBBY');
  const [roleFilter, setRoleFilter] = useState<RoleFilterType>('ALL');
  const [joiningMatchId, setJoiningMatchId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const { data: matches = [], isLoading, isError } = useOpenMatches(undefined, 'OPEN');

  const filteredMatches = matches.filter((m) => {
    if (m.match_type !== activeTab) return false;
    if (roleFilter !== 'ALL') {
      return m.needed_positions?.some((p) => p.toUpperCase().includes(roleFilter));
    }
    return true;
  });

  const joinMatch = useJoinMatch(joiningMatchId ?? '');

  const handleJoin = (matchId: string) => {
    setJoiningMatchId(matchId);
  };

  const handleConfirmJoin = (payload: JoinMatchPayload) => {
    if (!joiningMatchId) return;
    setErrorMessage(null);
    joinMatch.mutate(payload, {
      onSuccess: () => {
        setJoiningMatchId(null);
        setSuccessMessage('🎉 Successfully joined the match lobby!');
        setTimeout(() => setSuccessMessage(null), 4000);
      },
      onError: (err: any) => {
        setJoiningMatchId(null);
        const msg =
          err?.response?.data?.detail || err?.message || 'Failed to join match lobby.';
        setErrorMessage(typeof msg === 'string' ? msg : JSON.stringify(msg));
      },
    });
  };

  return (
    <div className="w-full space-y-6">
      <MobileHeader title="Open Lobbies" />

      {/* Alert Notifications */}
      {errorMessage && (
        <div className="flex items-center gap-3 bg-red-50 border border-red-300 rounded-2xl p-4 text-sm font-semibold text-red-900 shadow-sm animate-in fade-in slide-in-from-top-2">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
          <span>{errorMessage}</span>
          <button
            type="button"
            onClick={() => setErrorMessage(null)}
            className="ml-auto text-red-600 hover:text-red-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {successMessage && (
        <div className="flex items-center gap-3 bg-emerald-50 border border-emerald-300 rounded-2xl p-4 text-sm font-semibold text-emerald-900 shadow-sm animate-in fade-in slide-in-from-top-2">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
          <span>{successMessage}</span>
          <button
            type="button"
            onClick={() => setSuccessMessage(null)}
            className="ml-auto text-emerald-600 hover:text-emerald-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Desktop / Responsive Page Header */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-5 shadow-sm space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
              Matchmaking & Open Lobbies
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
              Jump into games as a solo player (+1) or enter your team in a squad challenge.
            </p>
          </div>
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-50 text-amber-800 text-xs font-bold border border-amber-200 self-start sm:self-auto">
            <Sparkles className="w-3.5 h-3.5 text-amber-600" />
            {filteredMatches.length} Lobbies Available
          </span>
        </div>

        {/* Filters and Tabs */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2 border-t border-slate-100">
          {/* Segmented tab toggle */}
          <div className="flex gap-1 p-1 bg-slate-100 rounded-xl max-w-sm">
            {(
              [
                { key: 'OPEN_LOBBY', label: 'Need Players (+1)' },
                { key: 'SQUAD_CHALLENGE', label: 'Squad vs Squad' },
              ] as Array<{ key: MatchTypeTab; label: string }>
            ).map(({ key, label }) => (
              <button
                key={key}
                type="button"
                onClick={() => setActiveTab(key)}
                className={`flex-1 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  activeTab === key
                    ? 'bg-white text-slate-900 shadow-sm'
                    : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Role filter */}
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => setRoleFilter('ALL')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold border transition-all ${
                roleFilter === 'ALL'
                  ? 'bg-slate-900 text-white border-slate-900'
                  : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'
              }`}
            >
              <Users className="w-3.5 h-3.5" /> All Roles
            </button>
            <button
              type="button"
              onClick={() => setRoleFilter('GOALKEEPER')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold border transition-all ${
                roleFilter === 'GOALKEEPER'
                  ? 'bg-amber-500 text-white border-amber-500'
                  : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'
              }`}
            >
              <Shield className="w-3.5 h-3.5 text-amber-500" /> GK Needed
            </button>
            <button
              type="button"
              onClick={() => setRoleFilter('DEFENDER')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold border transition-all ${
                roleFilter === 'DEFENDER'
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'
              }`}
            >
              Defender
            </button>
            <button
              type="button"
              onClick={() => setRoleFilter('MIDFIELDER')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold border transition-all ${
                roleFilter === 'MIDFIELDER'
                  ? 'bg-emerald-600 text-white border-emerald-600'
                  : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'
              }`}
            >
              Midfielder
            </button>
            <button
              type="button"
              onClick={() => setRoleFilter('FORWARD')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold border transition-all ${
                roleFilter === 'FORWARD'
                  ? 'bg-red-600 text-white border-red-600'
                  : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'
              }`}
            >
              Forward
            </button>
          </div>
        </div>
      </div>

      {/* Lobbies Stream: Responsive 2-Column Grid on Desktop */}
      <div className="w-full">
        {isLoading && (
          <div className="flex flex-col items-center justify-center py-20 gap-3 bg-white rounded-2xl border border-slate-200 text-slate-400">
            <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
            <p className="text-sm font-semibold">Finding open match lobbies…</p>
          </div>
        )}

        {isError && (
          <div className="flex flex-col items-center justify-center py-16 gap-2 bg-white rounded-2xl border border-slate-200">
            <AlertCircle className="w-8 h-8 text-red-400" />
            <p className="text-sm font-bold text-red-500">Could not load match lobbies</p>
          </div>
        )}

        {!isLoading && !isError && filteredMatches.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 gap-3 bg-white rounded-2xl border border-dashed border-slate-200 text-slate-400 text-center p-6">
            <Users className="w-12 h-12 opacity-30" />
            <p className="text-base font-bold text-slate-800">No open matches right now</p>
            <p className="text-xs text-slate-500 max-w-sm">
              Reserve any pitch and toggle &quot;Create Open Lobby&quot; to invite fellow players.
            </p>
          </div>
        )}

        {!isLoading && !isError && filteredMatches.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredMatches.map((match) => (
              <div
                key={match.id}
                id={`match-${match.id}`}
                className={
                  match.id === highlightId
                    ? 'ring-2 ring-emerald-500 rounded-2xl'
                    : ''
                }
              >
                <MatchLobbyCard
                  match={match}
                  onJoin={handleJoin}
                  isCurrentUserOrganizer={user?.id === match.organizer_id}
                />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Join modal */}
      <JoinMatchModal
        isOpen={Boolean(joiningMatchId)}
        matchId={joiningMatchId ?? ''}
        onClose={() => setJoiningMatchId(null)}
        onConfirm={handleConfirmJoin}
        isLoading={joinMatch.isPending}
      />
    </div>
  );
};

export default MatchesPage;
