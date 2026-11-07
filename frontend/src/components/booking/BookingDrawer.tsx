import React, { useState } from 'react';
import { X, Calendar, Clock, Users, ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import { TimeSlot, BookingCreatePayload } from '../../types/api';

interface BookingDrawerProps {
  isOpen: boolean;
  slot: TimeSlot | null;
  pitchId: string;
  pitchName: string;
  venueName: string;
  onClose: () => void;
  onConfirm: (payload: BookingCreatePayload) => void;
  isLoading: boolean;
}

const BookingDrawer: React.FC<BookingDrawerProps> = ({
  isOpen,
  slot,
  pitchId,
  pitchName,
  venueName,
  onClose,
  onConfirm,
  isLoading,
}) => {
  const [createLobby, setCreateLobby] = useState(false);
  const [targetPlayers, setTargetPlayers] = useState(10);
  const [neededPositions, setNeededPositions] = useState<string[]>([]);
  const [lobbyDescription, setLobbyDescription] = useState('');
  const [showLobbyOptions, setShowLobbyOptions] = useState(false);

  const POSITION_OPTIONS = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward'];

  const togglePosition = (pos: string) => {
    setNeededPositions((prev) =>
      prev.includes(pos) ? prev.filter((p) => p !== pos) : [...prev, pos]
    );
  };

  const handleConfirm = () => {
    if (!slot) return;
    const payload: BookingCreatePayload = {
      pitch_id: pitchId,
      start_time: slot.start_time,
      end_time: slot.end_time,
      create_open_lobby: createLobby,
      ...(createLobby
        ? {
            target_players: targetPlayers,
            needed_positions: neededPositions,
            lobby_description: lobbyDescription || undefined,
          }
        : {}),
    };
    onConfirm(payload);
  };

  const formatTime = (iso: string) =>
    new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString('en-GB', {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
    });

  if (!isOpen || !slot) return null;

  return (
    <div className="fixed inset-0 z-50 flex flex-col justify-end bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div
        className="max-w-md mx-auto w-full bg-white rounded-t-3xl shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Handle */}
        <div className="flex justify-center pt-3 pb-1">
          <div className="w-10 h-1 rounded-full bg-slate-200" />
        </div>

        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
          <div>
            <h2 className="text-base font-bold text-slate-900">Confirm Booking</h2>
            <p className="text-xs text-slate-500 mt-0.5">{venueName} · {pitchName}</p>
          </div>
          <button
            onClick={onClose}
            className="flex items-center justify-center w-8 h-8 rounded-full bg-slate-100 text-slate-500 hover:bg-slate-200"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Summary */}
        <div className="px-5 py-4 space-y-3">
          <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-xl">
            <Calendar className="w-4 h-4 text-slate-500 flex-shrink-0" />
            <span className="text-sm text-slate-700 font-medium">{formatDate(slot.start_time)}</span>
          </div>
          <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-xl">
            <Clock className="w-4 h-4 text-slate-500 flex-shrink-0" />
            <span className="text-sm text-slate-700 font-medium">
              {formatTime(slot.start_time)} – {formatTime(slot.end_time)}
            </span>
            <span className="ml-auto text-sm font-bold text-slate-900">{slot.price} RON</span>
          </div>

          {/* Open Lobby Toggle */}
          <div className="border border-slate-200 rounded-xl overflow-hidden">
            <button
              onClick={() => {
                setCreateLobby(!createLobby);
                setShowLobbyOptions(!createLobby);
              }}
              className="w-full flex items-center justify-between p-3.5 hover:bg-slate-50 transition-colors"
            >
              <div className="flex items-center gap-2.5">
                <Users className="w-4 h-4 text-amber-600" />
                <div className="text-left">
                  <p className="text-sm font-semibold text-slate-900">Create Open Lobby (+1)</p>
                  <p className="text-xs text-slate-500">Invite other players to join your match</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div
                  className={`w-10 h-5.5 rounded-full transition-colors relative ${
                    createLobby ? 'bg-amber-500' : 'bg-slate-200'
                  }`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-4.5 h-4.5 rounded-full bg-white shadow-sm transition-transform ${
                      createLobby ? 'translate-x-4.5' : 'translate-x-0'
                    }`}
                  />
                </div>
                {showLobbyOptions ? (
                  <ChevronUp className="w-4 h-4 text-slate-400" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-slate-400" />
                )}
              </div>
            </button>

            {createLobby && (
              <div className="px-4 pb-4 pt-2 border-t border-slate-100 space-y-3 bg-amber-50/40">
                {/* Players needed */}
                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    Total players needed
                  </label>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setTargetPlayers(Math.max(2, targetPlayers - 1))}
                      className="w-8 h-8 rounded-lg bg-white border border-slate-200 text-slate-700 font-bold text-lg flex items-center justify-center hover:bg-slate-50"
                    >
                      −
                    </button>
                    <span className="text-base font-bold text-slate-900 w-6 text-center">
                      {targetPlayers}
                    </span>
                    <button
                      onClick={() => setTargetPlayers(Math.min(22, targetPlayers + 1))}
                      className="w-8 h-8 rounded-lg bg-white border border-slate-200 text-slate-700 font-bold text-lg flex items-center justify-center hover:bg-slate-50"
                    >
                      +
                    </button>
                  </div>
                </div>

                {/* Positions */}
                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1.5 block">
                    Positions needed (optional)
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {POSITION_OPTIONS.map((pos) => (
                      <button
                        key={pos}
                        onClick={() => togglePosition(pos)}
                        className={`px-3 py-1 rounded-full text-xs font-medium border transition-all ${
                          neededPositions.includes(pos)
                            ? 'bg-amber-500 text-white border-amber-500'
                            : 'bg-white text-slate-600 border-slate-200 hover:border-amber-300'
                        }`}
                      >
                        {pos}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Description */}
                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    Announcement (optional)
                  </label>
                  <textarea
                    value={lobbyDescription}
                    onChange={(e) => setLobbyDescription(e.target.value)}
                    placeholder="e.g. Casual 6v6, all levels welcome!"
                    rows={2}
                    className="w-full text-xs rounded-xl border border-slate-200 bg-white p-2.5 resize-none focus:outline-none focus:border-amber-400 text-slate-700"
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 pb-8 pt-2">
          <button
            onClick={handleConfirm}
            disabled={isLoading}
            className="w-full h-12 rounded-2xl bg-emerald-600 text-white font-bold text-sm shadow-sm hover:bg-emerald-700 active:scale-[0.98] transition-all disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" /> Processing…
              </>
            ) : (
              `Book for ${slot.price} RON`
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default BookingDrawer;

