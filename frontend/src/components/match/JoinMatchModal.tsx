import React, { useState } from 'react';
import { X, Loader2 } from 'lucide-react';
import { JoinMatchPayload, ParticipantRole, TeamSide } from '../../types/api';

interface JoinMatchModalProps {
  isOpen: boolean;
  matchId: string;
  onClose: () => void;
  onConfirm: (payload: JoinMatchPayload) => void;
  isLoading: boolean;
}

const JoinMatchModal: React.FC<JoinMatchModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  isLoading,
}) => {
  const [role, setRole] = useState<ParticipantRole>('PLAYER');
  const [teamSide, setTeamSide] = useState<TeamSide>('A');

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex flex-col justify-end lg:justify-center items-center bg-black/50 backdrop-blur-sm p-0 lg:p-4"
      onClick={onClose}
    >
      <div
        className="max-w-md mx-auto w-full bg-white rounded-t-3xl lg:rounded-2xl shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Handle */}
        <div className="flex justify-center pt-3 pb-1">
          <div className="w-10 h-1 rounded-full bg-slate-200" />
        </div>

        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
          <h2 className="text-base font-bold text-slate-900">Join Match</h2>
          <button
            onClick={onClose}
            className="flex items-center justify-center w-8 h-8 rounded-full bg-slate-100 text-slate-500 hover:bg-slate-200"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="px-5 py-4 space-y-5">
          {/* Role selection */}
          <div>
            <label className="text-xs font-semibold text-slate-700 mb-2 block uppercase tracking-wide">
              Your Role
            </label>
            <div className="grid grid-cols-3 gap-2">
              {(['PLAYER', 'GOALKEEPER', 'ORGANIZER'] as ParticipantRole[]).map((r) => (
                <button
                  key={r}
                  onClick={() => setRole(r)}
                  className={`py-2.5 rounded-xl text-xs font-semibold border transition-all ${
                    role === r
                      ? 'bg-slate-900 text-white border-slate-900'
                      : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'
                  }`}
                >
                  {r === 'GOALKEEPER' ? 'GK' : r.charAt(0) + r.slice(1).toLowerCase()}
                </button>
              ))}
            </div>
          </div>

          {/* Team side */}
          <div>
            <label className="text-xs font-semibold text-slate-700 mb-2 block uppercase tracking-wide">
              Team Side
            </label>
            <div className="grid grid-cols-2 gap-2">
              {(['A', 'B'] as TeamSide[]).map((side) => (
                <button
                  key={side}
                  onClick={() => setTeamSide(side)}
                  className={`py-2.5 rounded-xl text-sm font-bold border transition-all ${
                    teamSide === side
                      ? 'bg-emerald-600 text-white border-emerald-600'
                      : 'bg-white text-slate-600 border-slate-200 hover:border-emerald-300'
                  }`}
                >
                  Team {side}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 pb-8 pt-2">
          <button
            onClick={() => onConfirm({ role, team_side: teamSide })}
            disabled={isLoading}
            className="w-full h-12 rounded-2xl bg-slate-900 text-white font-bold text-sm shadow-sm hover:bg-slate-800 active:scale-[0.98] transition-all disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" /> Joining…
              </>
            ) : (
              'Confirm & Join Match'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default JoinMatchModal;

