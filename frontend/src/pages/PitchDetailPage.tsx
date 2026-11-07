import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Loader2,
  AlertCircle,
  CheckCircle2,
  Calendar,
  Clock,
  Users,
  ShieldCheck,
  Zap,
  Car,
  Sun,
  X,
  ChevronDown,
  ChevronUp,
  DollarSign,
  Info,
} from 'lucide-react';
import MobileHeader from '../components/layout/MobileHeader';
import DateScroller from '../components/booking/DateScroller';
import TimeSlotSelector from '../components/booking/TimeSlotSelector';
import BookingDrawer from '../components/booking/BookingDrawer';
import MatchLobbyCard from '../components/match/MatchLobbyCard';
import JoinMatchModal from '../components/match/JoinMatchModal';
import { usePitch } from '../api/venues';
import { usePitchAvailability, useCreateBooking } from '../api/bookings';
import { useOpenMatches, useJoinMatch } from '../api/matches';
import { TimeSlot, BookingCreatePayload, JoinMatchPayload } from '../types/api';
import { useAuth } from '../context/AuthContext';

const GALLERY_IMAGES = [
  'https://images.unsplash.com/photo-1529900748604-07564a03e7a6?auto=format&fit=crop&w=1200&q=80',
  'https://images.unsplash.com/photo-1575361204480-aadea25e6e68?auto=format&fit=crop&w=800&q=80',
  'https://images.unsplash.com/photo-1551958219-acbc608c6377?auto=format&fit=crop&w=800&q=80',
  'https://images.unsplash.com/photo-1518091043644-c1d4457512c6?auto=format&fit=crop&w=800&q=80',
];

const POSITION_OPTIONS = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward'];

const PitchDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const today = new Date().toISOString().slice(0, 10);
  const [selectedDate, setSelectedDate] = useState(today);
  const [selectedSlot, setSelectedSlot] = useState<TimeSlot | null>(null);
  const [drawerSlot, setDrawerSlot] = useState<TimeSlot | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [activeGalleryIndex, setActiveGalleryIndex] = useState(0);

  // Desktop Checkout Card Form State
  const [desktopCreateLobby, setDesktopCreateLobby] = useState(false);
  const [desktopTargetPlayers, setDesktopTargetPlayers] = useState(10);
  const [desktopNeededPositions, setDesktopNeededPositions] = useState<string[]>([]);
  const [desktopLobbyDescription, setDesktopLobbyDescription] = useState('');
  const [desktopShowLobbyOpts, setDesktopShowLobbyOpts] = useState(false);

  // Join Match Modal State
  const [joiningMatchId, setJoiningMatchId] = useState<string | null>(null);

  const pitchId = id ?? '';
  const { data: pitch, isLoading: pitchLoading, isError: pitchError } = usePitch(pitchId);
  const { data: slots = [], isLoading: slotsLoading, isError: slotsError } = usePitchAvailability(
    pitchId,
    selectedDate
  );
  const { data: openMatches = [] } = useOpenMatches();
  const createBooking = useCreateBooking(pitchId, selectedDate);
  const joinMatch = useJoinMatch(joiningMatchId ?? '');

  // Filter open matches relevant to this venue or general
  const pitchLobbies = openMatches.filter(
    (m) =>
      m.status === 'OPEN' &&
      (m.pitch_name === pitch?.name ||
        m.venue_name === pitch?.name ||
        slots.some((s) => s.open_match_id === m.id))
  );

  const toggleDesktopPosition = (pos: string) => {
    setDesktopNeededPositions((prev) =>
      prev.includes(pos) ? prev.filter((p) => p !== pos) : [...prev, pos]
    );
  };

  const handleSelectAvailableSlot = (slot: TimeSlot) => {
    setSelectedSlot(slot);
    // On mobile (< 1024px), open the slide-up drawer
    if (typeof window !== 'undefined' && window.innerWidth < 1024) {
      setDrawerSlot(slot);
    }
  };

  const handleSelectOpenLobby = (matchId: string) => {
    setJoiningMatchId(matchId);
  };

  const handleConfirmBooking = (payload: BookingCreatePayload) => {
    createBooking.mutate(payload, {
      onSuccess: () => {
        setDrawerSlot(null);
        setSelectedSlot(null);
        setDesktopCreateLobby(false);
        setSuccessMessage(
          payload.create_open_lobby
            ? '🏆 Reservation confirmed! Open lobby (+1) created.'
            : '✅ Pitch reserved successfully! Confirmation sent.'
        );
        setTimeout(() => setSuccessMessage(null), 5000);
      },
      onError: () => {
        setDrawerSlot(null);
      },
    });
  };

  const handleDesktopConfirm = () => {
    if (!selectedSlot) return;
    const payload: BookingCreatePayload = {
      pitch_id: pitchId,
      start_time: selectedSlot.start_time,
      end_time: selectedSlot.end_time,
      create_open_lobby: desktopCreateLobby,
      ...(desktopCreateLobby
        ? {
            target_players: desktopTargetPlayers,
            needed_positions: desktopNeededPositions,
            lobby_description: desktopLobbyDescription || undefined,
          }
        : {}),
    };
    handleConfirmBooking(payload);
  };

  const handleConfirmJoin = (payload: JoinMatchPayload) => {
    if (!joiningMatchId) return;
    setErrorMessage(null);
    joinMatch.mutate(payload, {
      onSuccess: () => {
        setJoiningMatchId(null);
        setSuccessMessage('🎉 You have successfully joined the match squad!');
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

  const formatTime = (iso: string) =>
    new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });

  const formatDateLabel = (isoDate: string) => {
    const d = new Date(isoDate);
    return d.toLocaleDateString('en-GB', {
      weekday: 'long',
      day: 'numeric',
      month: 'short',
    });
  };

  if (pitchLoading) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 py-28 gap-3">
        <Loader2 className="w-10 h-10 animate-spin text-emerald-500" />
        <p className="text-sm font-semibold text-slate-500">Loading pitch details…</p>
      </div>
    );
  }

  if (pitchError || !pitch) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 py-28 gap-3">
        <AlertCircle className="w-10 h-10 text-red-400" />
        <p className="text-base font-bold text-red-500">Pitch not found</p>
        <button
          onClick={() => navigate('/')}
          className="mt-2 px-4 py-2 bg-slate-900 text-white text-xs font-semibold rounded-xl"
        >
          Back to Pitches
        </button>
      </div>
    );
  }

  const teamCapacityTotal = pitch.team_size_capacity * 2;
  const splitCostPerPlayer = selectedSlot
    ? (Number(selectedSlot.price) / teamCapacityTotal).toFixed(2)
    : (Number(pitch.hourly_rate) / teamCapacityTotal).toFixed(2);

  return (
    <div className="w-full space-y-6">
      {/* Mobile Sticky Header */}
      <MobileHeader title={pitch.name} showBack />

      {/* Success Notification Alert */}
      {successMessage && (
        <div className="flex items-center gap-3 bg-emerald-50 border border-emerald-300 rounded-2xl p-4 text-sm font-semibold text-emerald-900 shadow-sm animate-in fade-in slide-in-from-top-2">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
          <span>{successMessage}</span>
          <button
            onClick={() => setSuccessMessage(null)}
            className="ml-auto text-emerald-600 hover:text-emerald-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Error Notification Alert */}
      {errorMessage && (
        <div className="flex items-center gap-3 bg-red-50 border border-red-300 rounded-2xl p-4 text-sm font-semibold text-red-900 shadow-sm animate-in fade-in slide-in-from-top-2">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
          <span>{errorMessage}</span>
          <button
            onClick={() => setErrorMessage(null)}
            className="ml-auto text-red-600 hover:text-red-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* ─── 12-Column Desktop Adaptive Grid ─── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* ─── LEFT COLUMN: Pitch Info, Gallery, Facilities, Date, Slots, Lobbies ─── */}
        <div className="lg:col-span-7 xl:col-span-8 space-y-7">
          {/* Pitch Hero Image Gallery */}
          <div className="space-y-3">
            {/* Desktop 1 Large + 3 Thumbnails / Mobile Single Banner */}
            <div className="hidden sm:grid grid-cols-12 gap-3 h-64 md:h-72 overflow-hidden rounded-2xl">
              <div className="col-span-8 h-full min-h-0 rounded-2xl overflow-hidden relative shadow-sm group">
                <img
                  src={GALLERY_IMAGES[activeGalleryIndex]}
                  alt={pitch.name}
                  className="w-full h-full object-cover group-hover:scale-102 transition-transform duration-300"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
                <div className="absolute bottom-4 left-4 right-4 text-white">
                  <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-600/90 backdrop-blur-md shadow-sm">
                    {pitch.surface_type.replace(/_/g, ' ')}
                  </span>
                  <h1 className="text-2xl font-black mt-2 drop-shadow-sm">{pitch.name}</h1>
                  <p className="text-xs text-slate-200 mt-0.5">
                    {pitch.team_size_capacity}v{pitch.team_size_capacity} Mini-Football Pitch
                  </p>
                </div>
              </div>

              {/* 3 Grid Thumbnails on Desktop */}
              <div className="col-span-4 grid grid-rows-3 gap-2.5 h-full min-h-0 overflow-hidden">
                {GALLERY_IMAGES.slice(1, 4).map((img, idx) => {
                  const actualIdx = idx + 1;
                  const isActive = activeGalleryIndex === actualIdx;
                  return (
                    <button
                      key={img}
                      type="button"
                      onClick={() => setActiveGalleryIndex(actualIdx)}
                      className={`h-full w-full min-h-0 relative rounded-xl overflow-hidden border-2 transition-all group ${
                        isActive
                          ? 'border-emerald-500 shadow-md ring-2 ring-emerald-500/30'
                          : 'border-transparent opacity-75 hover:opacity-100'
                      }`}
                    >
                      <img
                        src={img}
                        alt={`Thumbnail ${actualIdx}`}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                      />
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Mobile Single Hero Banner */}
            <div className="sm:hidden relative h-56 rounded-2xl overflow-hidden shadow-sm">
              <img
                src={GALLERY_IMAGES[activeGalleryIndex]}
                alt={pitch.name}
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
              <div className="absolute bottom-3 left-3 right-3 text-white">
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-600 shadow-sm">
                  {pitch.surface_type.replace(/_/g, ' ')}
                </span>
                <h1 className="text-xl font-bold mt-1 text-white">{pitch.name}</h1>
                <p className="text-xs text-slate-200">
                  {pitch.team_size_capacity}v{pitch.team_size_capacity} Mini-Football Arena
                </p>
              </div>
            </div>
          </div>

          {/* Facility Chips Row */}
          <div className="space-y-2.5">
            <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
              Pitch Amenities & Features
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              <div className="bg-white border border-slate-200 rounded-xl p-3 flex items-center gap-2.5 text-xs font-semibold text-slate-800 shadow-sm">
                <Zap className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                <div>
                  <p className="leading-tight">Turf Quality</p>
                  <p className="text-[10px] text-slate-400 font-normal">FIFA Approved</p>
                </div>
              </div>

              <div className="bg-white border border-slate-200 rounded-xl p-3 flex items-center gap-2.5 text-xs font-semibold text-slate-800 shadow-sm">
                <Sun className="w-4 h-4 text-amber-500 flex-shrink-0" />
                <div>
                  <p className="leading-tight">Floodlights</p>
                  <p className="text-[10px] text-slate-400 font-normal">Night matches</p>
                </div>
              </div>

              <div className="bg-white border border-slate-200 rounded-xl p-3 flex items-center gap-2.5 text-xs font-semibold text-slate-800 shadow-sm">
                <Car className="w-4 h-4 text-blue-500 flex-shrink-0" />
                <div>
                  <p className="leading-tight">Free Parking</p>
                  <p className="text-[10px] text-slate-400 font-normal">On-site spots</p>
                </div>
              </div>

              <div className="bg-white border border-slate-200 rounded-xl p-3 flex items-center gap-2.5 text-xs font-semibold text-slate-800 shadow-sm">
                <ShieldCheck className="w-4 h-4 text-purple-500 flex-shrink-0" />
                <div>
                  <p className="leading-tight">Lockers & Showers</p>
                  <p className="text-[10px] text-slate-400 font-normal">Included</p>
                </div>
              </div>
            </div>
          </div>

          {/* Date Picker (Accessible Multi-Day Ribbon) */}
          <div className="space-y-2">
            <DateScroller selectedDate={selectedDate} onDateChange={setSelectedDate} />
          </div>

          {/* Time Slot Matrix */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-slate-900">Available Time Slots</h2>
                <p className="text-xs text-slate-500">
                  {formatDateLabel(selectedDate)} · Select 60 min session
                </p>
              </div>
              <span className="text-xs font-semibold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full">
                {slots.filter((s) => s.status === 'AVAILABLE').length} Slots Available
              </span>
            </div>

            {slotsLoading ? (
              <div className="flex flex-col items-center justify-center py-16 gap-3 bg-white rounded-2xl border border-slate-200">
                <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
                <p className="text-sm font-medium text-slate-400">Loading live availability…</p>
              </div>
            ) : slotsError ? (
              <div className="flex flex-col items-center justify-center py-12 gap-2 bg-white rounded-2xl border border-slate-200 text-slate-400">
                <AlertCircle className="w-7 h-7 text-red-400" />
                <p className="text-sm font-medium text-red-500">Could not load schedule slots</p>
              </div>
            ) : (
              <TimeSlotSelector
                slots={slots}
                selectedSlot={selectedSlot}
                onSelectAvailableSlot={handleSelectAvailableSlot}
                onSelectOpenLobby={handleSelectOpenLobby}
              />
            )}
          </div>

          {/* Open Matches (+1 Lobbies) Section with Squad Cards */}
          <div className="space-y-3 pt-4 border-t border-slate-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-amber-100 text-amber-700 flex items-center justify-center">
                  <Users className="w-4 h-4" />
                </div>
                <div>
                  <h2 className="text-sm font-bold text-slate-900">Open Lobbies (+1 Matches)</h2>
                  <p className="text-xs text-slate-500">Join an existing squad without booking</p>
                </div>
              </div>
              <span className="text-xs font-bold text-amber-800 bg-amber-100 px-2.5 py-1 rounded-full">
                {pitchLobbies.length} Active
              </span>
            </div>

            {pitchLobbies.length === 0 ? (
              <div className="bg-white rounded-2xl border border-dashed border-slate-200 p-6 text-center text-slate-400 space-y-1">
                <p className="text-xs font-semibold text-slate-600">No open lobbies at this pitch yet</p>
                <p className="text-[11px] text-slate-400">
                  Book a slot and toggle &quot;Create Open Lobby&quot; to invite other players!
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {pitchLobbies.map((match) => (
                  <MatchLobbyCard
                    key={match.id}
                    match={match}
                    onJoin={handleSelectOpenLobby}
                    isCurrentUserOrganizer={user?.id === match.organizer_id}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* ─── RIGHT COLUMN: Sticky Desktop Checkout Card & Summary ─── */}
        <div className="hidden lg:block lg:col-span-5 xl:col-span-4 sticky top-24">
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-5">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <h3 className="text-base font-bold text-slate-900">Reservation Summary</h3>
                <p className="text-xs text-slate-500 mt-0.5">{pitch.name}</p>
              </div>
              <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                Instant Lock
              </span>
            </div>

            {selectedSlot ? (
              <div className="space-y-4">
                {/* Date & Time pills */}
                <div className="space-y-2">
                  <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-xl">
                    <Calendar className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                    <div>
                      <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                        Date
                      </p>
                      <p className="text-sm font-bold text-slate-900">
                        {formatDateLabel(selectedSlot.start_time)}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-xl">
                    <Clock className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                    <div className="flex-1">
                      <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                        Time Window
                      </p>
                      <p className="text-sm font-bold text-slate-900">
                        {formatTime(selectedSlot.start_time)} – {formatTime(selectedSlot.end_time)}{' '}
                        <span className="text-xs font-normal text-slate-500">(60 min)</span>
                      </p>
                    </div>
                    <span className="text-sm font-bold text-slate-900">{selectedSlot.price} RON</span>
                  </div>
                </div>

                {/* Split payment preview */}
                <div className="bg-emerald-50/70 border border-emerald-200 rounded-xl p-3 space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-emerald-950 flex items-center gap-1.5">
                      <DollarSign className="w-3.5 h-3.5 text-emerald-600" />
                      Split Bill Preview
                    </span>
                    <span className="font-black text-emerald-800">
                      {splitCostPerPlayer} RON / player
                    </span>
                  </div>
                  <p className="text-[11px] text-emerald-700">
                    Based on {teamCapacityTotal} players ({pitch.team_size_capacity}v
                    {pitch.team_size_capacity}). Share link after booking to split automatically.
                  </p>
                </div>

                {/* Open Lobby (+1) Toggle for Desktop */}
                <div className="border border-slate-200 rounded-xl overflow-hidden">
                  <button
                    type="button"
                    onClick={() => {
                      setDesktopCreateLobby(!desktopCreateLobby);
                      setDesktopShowLobbyOpts(!desktopCreateLobby);
                    }}
                    className="w-full flex items-center justify-between p-3.5 hover:bg-slate-50 transition-colors text-left"
                  >
                    <div className="flex items-center gap-2.5">
                      <Users className="w-4 h-4 text-amber-600" />
                      <div>
                        <p className="text-xs font-bold text-slate-900">Create Open Lobby (+1)</p>
                        <p className="text-[11px] text-slate-500">Need extra players to fill squad</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div
                        className={`w-9 h-5 rounded-full transition-colors relative ${
                          desktopCreateLobby ? 'bg-amber-500' : 'bg-slate-200'
                        }`}
                      >
                        <span
                          className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow-sm transition-transform ${
                            desktopCreateLobby ? 'translate-x-4' : 'translate-x-0'
                          }`}
                        />
                      </div>
                      {desktopShowLobbyOpts ? (
                        <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                      )}
                    </div>
                  </button>

                  {desktopCreateLobby && (
                    <div className="px-4 pb-4 pt-2 border-t border-slate-100 space-y-3 bg-amber-50/40">
                      <div>
                        <label className="text-[11px] font-bold text-slate-700 mb-1 block">
                          Total squad players needed
                        </label>
                        <div className="flex items-center gap-3">
                          <button
                            type="button"
                            onClick={() =>
                              setDesktopTargetPlayers(Math.max(2, desktopTargetPlayers - 1))
                            }
                            className="w-7 h-7 rounded-lg bg-white border border-slate-200 text-slate-700 font-bold flex items-center justify-center hover:bg-slate-50"
                          >
                            −
                          </button>
                          <span className="text-sm font-bold text-slate-900 w-6 text-center">
                            {desktopTargetPlayers}
                          </span>
                          <button
                            type="button"
                            onClick={() =>
                              setDesktopTargetPlayers(Math.min(22, desktopTargetPlayers + 1))
                            }
                            className="w-7 h-7 rounded-lg bg-white border border-slate-200 text-slate-700 font-bold flex items-center justify-center hover:bg-slate-50"
                          >
                            +
                          </button>
                        </div>
                      </div>

                      <div>
                        <label className="text-[11px] font-bold text-slate-700 mb-1 block">
                          Positions needed
                        </label>
                        <div className="flex flex-wrap gap-1.5">
                          {POSITION_OPTIONS.map((pos) => (
                            <button
                              key={pos}
                              type="button"
                              onClick={() => toggleDesktopPosition(pos)}
                              className={`px-2.5 py-1 rounded-full text-[10px] font-semibold border transition-all ${
                                desktopNeededPositions.includes(pos)
                                  ? 'bg-amber-500 text-white border-amber-500'
                                  : 'bg-white text-slate-600 border-slate-200 hover:border-amber-300'
                              }`}
                            >
                              {pos}
                            </button>
                          ))}
                        </div>
                      </div>

                      <div>
                        <label className="text-[11px] font-bold text-slate-700 mb-1 block">
                          Announcement (optional)
                        </label>
                        <textarea
                          value={desktopLobbyDescription}
                          onChange={(e) => setDesktopLobbyDescription(e.target.value)}
                          placeholder="Casual game, all skill levels welcome!"
                          rows={2}
                          className="w-full text-xs rounded-xl border border-slate-200 bg-white p-2 resize-none focus:outline-none focus:border-amber-400 text-slate-700"
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* Price breakdown */}
                <div className="pt-2 border-t border-slate-100 space-y-1.5">
                  <div className="flex justify-between text-xs text-slate-500">
                    <span>Pitch Hire (60 min)</span>
                    <span>{selectedSlot.price} RON</span>
                  </div>
                  <div className="flex justify-between text-xs text-slate-500">
                    <span>Service & Protection Fee</span>
                    <span className="text-emerald-600 font-semibold">0.00 RON</span>
                  </div>
                  <div className="flex justify-between text-sm font-black text-slate-900 pt-2 border-t border-slate-100">
                    <span>Total Due</span>
                    <span className="text-emerald-600">{selectedSlot.price} RON</span>
                  </div>
                </div>

                {/* Confirm Action Button */}
                <button
                  type="button"
                  onClick={handleDesktopConfirm}
                  disabled={createBooking.isPending}
                  className="w-full h-12 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm shadow-md shadow-emerald-600/20 active:scale-[0.99] transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {createBooking.isPending ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Securing Pitch…
                    </>
                  ) : (
                    `Confirm Reservation · ${selectedSlot.price} RON`
                  )}
                </button>

                <div className="flex items-center gap-1.5 text-[11px] text-slate-400 justify-center">
                  <Info className="w-3.5 h-3.5 flex-shrink-0" />
                  <span>Free cancellation up to 6 hours before kickoff</span>
                </div>
              </div>
            ) : (
              /* Empty State Prompt when no slot is picked */
              <div className="py-8 text-center space-y-3">
                <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto">
                  <Clock className="w-6 h-6" />
                </div>
                <div className="space-y-1">
                  <p className="text-sm font-bold text-slate-800">Choose a time slot</p>
                  <p className="text-xs text-slate-400 px-4">
                    Click any available green time slot on the schedule to view the cost breakdown
                    and complete reservation.
                  </p>
                </div>
                <div className="pt-3 border-t border-slate-100">
                  <span className="text-xs font-semibold text-slate-500">Standard Rate: </span>
                  <span className="text-sm font-black text-slate-900">
                    {pitch.hourly_rate} RON / hour
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Mobile Drawer (Only mounted/shown on Mobile via lg:hidden) */}
      <BookingDrawer
        isOpen={Boolean(drawerSlot)}
        slot={drawerSlot}
        pitchId={pitchId}
        pitchName={pitch.name}
        venueName={pitch.venue_id}
        onClose={() => setDrawerSlot(null)}
        onConfirm={handleConfirmBooking}
        isLoading={createBooking.isPending}
      />

      {/* Join Match Modal */}
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

export default PitchDetailPage;
