import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Loader2, AlertCircle, Users, Shield } from 'lucide-react';
import MobileHeader from '../components/layout/MobileHeader';
import MatchLobbyCard from '../components/match/MatchLobbyCard';
import JoinMatchModal from '../components/match/JoinMatchModal';
import { useOpenMatches, useJoinMatch } from '../api/matches';
import { JoinMatchPayload } from '../types/api';
import { useAuth } from '../context/AuthContext';

type MatchTypeTab = 'OPEN_LOBBY' | 'SQUAD_CHALLENGE';

const MatchesPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const highlightId = searchParams.get('highlight');
  const { user } = useAuth();

  const [activeTab, setActiveTab] = useState<MatchTypeTab>('OPEN_LOBBY');
  const [roleFilter, setRoleFilter] = useState<'ALL' | 'GOALKEEPER'>('ALL');
  const [joiningMatchId, setJoiningMatchId] = useState<string | null>(null);

  const { data: matches = [], isLoading, isError } = useOpenMatches(undefined, 'OPEN');

  const filteredMatches = matches.filter((m) => {
    if (m.match_type !== activeTab) return false;
    if (roleFilter === 'GOALKEEPER') {
      return m.needed_positions?.some((p) =>
        p.toUpperCase().includes('GOALKEEPER')
      );
    }
    return true;
  });

  const joinMatch = useJoinMatch(joiningMatchId ?? '');

  const handleJoin = (matchId: string) => {
    setJoiningMatchId(matchId);
  };

  const handleConfirmJoin = (payload: JoinMatchPayload) => {
    if (!joiningMatchId) return;
    joinMatch.mutate(payload, {
      onSuccess: () => setJoiningMatchId(null),
      onError: () => setJoiningMatchId(null),
    });
  };

  return (
    <>
      <MobileHeader title="Open Lobbies" />

      {/* Segmented tab toggle */}
      <div className="px-4 pt-3 pb-2">
        <div className="flex gap-1 p-1 bg-slate-100 rounded-xl">
          {([
            { key: 'OPEN_LOBBY', label: 'Need Players (+1)' },
            { key: 'SQUAD_CHALLENGE', label: 'Squad vs Squad' },
          ] as Array<{ key: MatchTypeTab; label: string }>).map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`flex-1 py-2 rounded-lg text-xs font-semibold transition-all ${
                activeTab === key
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Role filter */}
      <div className="flex gap-2 px-4 pb-3">
        <button
          onClick={() => setRoleFilter('ALL')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${
            roleFilter === 'ALL'
              ? 'bg-slate-900 text-white border-slate-900'
              : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'
          }`}
        >
          <Users className="w-3 h-3" /> All Roles
        </button>
        <button
          onClick={() => setRoleFilter('GOALKEEPER')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${
            roleFilter === 'GOALKEEPER'
              ? 'bg-amber-500 text-white border-amber-500'
              : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'
          }`}
        >
          <Shield className="w-3 h-3" /> GK Needed
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 px-4 pb-4 space-y-3 overflow-y-auto">
        {isLoading && (
          <div className="flex flex-col items-center justify-center py-16 gap-3 text-slate-400">
            <Loader2 className="w-7 h-7 animate-spin text-emerald-500" />
            <p className="text-sm">Loading lobbies…</p>
          </div>
        )}

        {isError && (
          <div className="flex flex-col items-center justify-center py-16 gap-2">
            <AlertCircle className="w-7 h-7 text-red-400" />
            <p className="text-sm font-medium text-red-500">Could not load matches</p>
          </div>
        )}

        {!isLoading && !isError && filteredMatches.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 gap-2 text-slate-400">
            <Users className="w-10 h-10 opacity-30" />
            <p className="text-sm font-medium">No open lobbies right now</p>
            <p className="text-xs text-center px-6">
              Book a pitch and create an Open Lobby to invite other players
            </p>
          </div>
        )}

        {!isLoading &&
          filteredMatches.map((match) => (
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

      {/* Join modal */}
      <JoinMatchModal
        isOpen={Boolean(joiningMatchId)}
        matchId={joiningMatchId ?? ''}
        onClose={() => setJoiningMatchId(null)}
        onConfirm={handleConfirmJoin}
        isLoading={joinMatch.isPending}
      />
    </>
  );
};

export default MatchesPage;

