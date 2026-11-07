import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  User,
  Calendar,
  LogOut,
  Loader2,
  AlertCircle,
  CheckCircle2,
  ShieldCheck,
  Mail,
  Phone,
  Users,
  Plus,
  Edit3,
  ExternalLink,
  X,
} from 'lucide-react';
import MobileHeader from '../components/layout/MobileHeader';
import { useAuth } from '../context/AuthContext';
import { useUserBookings } from '../api/bookings';
import { useMyMatches, useCreateMatchFromBooking, useUpdateMatch } from '../api/matches';
import { BookingResponse, MatchDetailResponse } from '../types/api';

const POSITION_OPTIONS = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward'];

type ActiveTab = 'BOOKINGS' | 'JOINED_MATCHES' | 'PAST';

const ProfilePage: React.FC = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<ActiveTab>('BOOKINGS');
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Modal State for Creating Lobby
  const [lobbyBooking, setLobbyBooking] = useState<BookingResponse | null>(null);
  const [createSpotsNeeded, setCreateSpotsNeeded] = useState<number>(2);
  const [createPositions, setCreatePositions] = useState<string[]>([]);
  const [createDescription, setCreateDescription] = useState<string>('');

  // Modal State for Editing Existing Lobby
  const [editingMatch, setEditingMatch] = useState<MatchDetailResponse | null>(null);
  const [editSpotsNeeded, setEditSpotsNeeded] = useState<number>(1);
  const [editPositions, setEditPositions] = useState<string[]>([]);
  const [editDescription, setEditDescription] = useState<string>('');

  // Queries & Mutations
  const { data: bookings = [], isLoading: bookingsLoading, isError: bookingsError } = useUserBookings();
  const { data: myMatches = [], isLoading: matchesLoading } = useMyMatches();
  const createMatch = useCreateMatchFromBooking();
  const updateMatch = useUpdateMatch(editingMatch?.id ?? '');

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  if (!isAuthenticated) {
    return (
      <div className="w-full">
        <MobileHeader title="Profile" />
        <div className="flex flex-col items-center justify-center flex-1 py-20 gap-4 px-6 bg-white rounded-2xl border border-slate-200 shadow-sm max-w-md mx-auto my-8">
          <div className="w-16 h-16 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <User className="w-8 h-8" />
          </div>
          <div className="text-center space-y-1">
            <h2 className="text-base font-bold text-slate-900">Sign in to Pitchup</h2>
            <p className="text-xs text-slate-500 max-w-xs">
              Manage your upcoming reservations, match invites, and split payments.
            </p>
          </div>
          <button
            onClick={() => navigate('/login')}
            className="w-full h-11 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-sm transition-all"
          >
            Sign In
          </button>
          <button
            onClick={() => navigate('/register')}
            className="text-xs font-semibold text-emerald-600 hover:text-emerald-700"
          >
            Don&apos;t have an account? Sign up →
          </button>
        </div>
      </div>
    );
  }

  const upcomingBookings = bookings.filter(
    (b) => b.status !== 'CANCELLED' && new Date(b.start_time) > new Date()
  );
  const pastBookings = bookings.filter(
    (b) => b.status !== 'CANCELLED' && new Date(b.start_time) <= new Date()
  );

  const formatBookingTime = (iso: string) =>
    new Date(iso).toLocaleString('en-GB', {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    });

  // Open Create Lobby Modal
  const handleOpenCreateLobby = (booking: BookingResponse) => {
    setLobbyBooking(booking);
    setCreateSpotsNeeded(2);
    setCreatePositions([]);
    setCreateDescription(`Casual match at ${booking.pitch_name || 'pitch'}! Need extra players to join.`);
  };

  const handleToggleCreatePosition = (pos: string) => {
    setCreatePositions((prev) =>
      prev.includes(pos) ? prev.filter((p) => p !== pos) : [...prev, pos]
    );
  };

  const handleConfirmCreateLobby = () => {
    if (!lobbyBooking) return;
    setErrorMessage(null);

    // Target players = 1 (organizer) + extra spots needed
    const targetPlayers = 1 + Number(createSpotsNeeded);

    createMatch.mutate(
      {
        booking_id: lobbyBooking.id,
        target_players: targetPlayers,
        needed_positions: createPositions,
        description: createDescription,
      },
      {
        onSuccess: () => {
          setLobbyBooking(null);
          setSuccessMessage('🎉 Match lobby created! Players can now find and join your game.');
          setTimeout(() => setSuccessMessage(null), 5000);
        },
        onError: (err: any) => {
          const msg = err?.response?.data?.detail || err?.message || 'Failed to create match lobby.';
          setErrorMessage(typeof msg === 'string' ? msg : JSON.stringify(msg));
        },
      }
    );
  };

  // Open Edit Lobby Modal
  const handleOpenEditLobby = (match: MatchDetailResponse) => {
    setEditingMatch(match);
    const confirmedCount = match.current_players_count || 1;
    const currentSpots = Math.max(1, match.target_players - confirmedCount);
    setEditSpotsNeeded(currentSpots);
    setEditPositions(match.needed_positions || []);
    setEditDescription(match.description || '');
  };

  const handleToggleEditPosition = (pos: string) => {
    setEditPositions((prev) =>
      prev.includes(pos) ? prev.filter((p) => p !== pos) : [...prev, pos]
    );
  };

  const handleConfirmUpdateLobby = () => {
    if (!editingMatch) return;
    setErrorMessage(null);

    updateMatch.mutate(
      {
        spots_needed: Number(editSpotsNeeded),
        needed_positions: editPositions,
        description: editDescription,
      },
      {
        onSuccess: () => {
          setEditingMatch(null);
          setSuccessMessage('✅ Lobby updated successfully!');
          setTimeout(() => setSuccessMessage(null), 5000);
        },
        onError: (err: any) => {
          const msg = err?.response?.data?.detail || err?.message || 'Failed to update lobby.';
          setErrorMessage(typeof msg === 'string' ? msg : JSON.stringify(msg));
        },
      }
    );
  };

  return (
    <div className="w-full space-y-6">
      <MobileHeader title="My Profile" />

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

      {/* Responsive 12-Column Grid on Desktop */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: User Card & Account Stats */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
            <div className="flex items-center gap-3.5">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-emerald-600 to-emerald-400 flex items-center justify-center text-white font-black text-xl shadow-md shadow-emerald-500/20">
                {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
              </div>
              <div className="min-w-0 flex-1">
                <h2 className="text-base font-bold text-slate-900 truncate">{user?.full_name}</h2>
                <div className="flex items-center gap-1.5 text-xs text-slate-500 mt-0.5 truncate">
                  <Mail className="w-3 h-3 text-slate-400" />
                  <span className="truncate">{user?.email}</span>
                </div>
                <span className="inline-block mt-2 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">
                  {user?.role}
                </span>
              </div>
            </div>

            {user?.phone && (
              <div className="pt-3 border-t border-slate-100 flex items-center gap-2 text-xs text-slate-600">
                <Phone className="w-3.5 h-3.5 text-slate-400" />
                <span>{user.phone}</span>
              </div>
            )}

            <div className="pt-3 border-t border-slate-100 grid grid-cols-3 gap-2 text-center">
              <div className="p-2.5 bg-slate-50 rounded-xl">
                <p className="text-lg font-black text-slate-900">{upcomingBookings.length}</p>
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Bookings
                </p>
              </div>
              <div className="p-2.5 bg-slate-50 rounded-xl">
                <p className="text-lg font-black text-emerald-600">{myMatches.length}</p>
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Lobbies
                </p>
              </div>
              <div className="p-2.5 bg-slate-50 rounded-xl">
                <p className="text-lg font-black text-slate-900">{pastBookings.length}</p>
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Played
                </p>
              </div>
            </div>

            <button
              onClick={() => void handleLogout()}
              className="w-full h-11 rounded-xl border border-red-200 text-red-600 hover:bg-red-50 text-xs font-bold flex items-center justify-center gap-2 transition-colors cursor-pointer"
            >
              <LogOut className="w-4 h-4" /> Sign Out
            </button>
          </div>
        </div>

        {/* Right Column: Interactive Tabs & Activity Lists */}
        <div className="lg:col-span-8 space-y-6">
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-6">
            {/* Header with Switcher Tabs */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
              <div>
                <h1 className="text-lg font-black text-slate-900 tracking-tight">
                  My Activity & Schedule
                </h1>
                <p className="text-xs text-slate-500 mt-0.5">
                  Manage your pitch reservations, modify match lobbies, and track your teams.
                </p>
              </div>

              {/* Navigation Tabs */}
              <div className="flex items-center bg-slate-100 p-1 rounded-xl gap-1">
                <button
                  type="button"
                  onClick={() => setActiveTab('BOOKINGS')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                    activeTab === 'BOOKINGS'
                      ? 'bg-white text-slate-900 shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <Calendar className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Upcoming ({upcomingBookings.length})</span>
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('JOINED_MATCHES')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                    activeTab === 'JOINED_MATCHES'
                      ? 'bg-white text-slate-900 shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <Users className="w-3.5 h-3.5 text-amber-600" />
                  <span>My Matches ({myMatches.length})</span>
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('PAST')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                    activeTab === 'PAST'
                      ? 'bg-white text-slate-900 shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <ShieldCheck className="w-3.5 h-3.5 text-slate-400" />
                  <span>History ({pastBookings.length})</span>
                </button>
              </div>
            </div>

            {/* TAB 1: Upcoming Pitch Bookings */}
            {activeTab === 'BOOKINGS' && (
              <section className="space-y-3">
                {bookingsLoading ? (
                  <div className="flex justify-center py-12">
                    <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
                  </div>
                ) : bookingsError ? (
                  <div className="flex flex-col items-center gap-2 py-8 text-slate-400">
                    <AlertCircle className="w-8 h-8 text-red-400" />
                    <p className="text-xs font-bold text-red-500">Could not load bookings</p>
                  </div>
                ) : upcomingBookings.length === 0 ? (
                  <div className="text-center py-12 bg-slate-50 rounded-2xl border border-dashed border-slate-200 text-slate-500 space-y-2">
                    <Calendar className="w-8 h-8 mx-auto text-slate-300" />
                    <p className="text-sm font-bold text-slate-800">No upcoming bookings scheduled</p>
                    <p className="text-xs text-slate-400 max-w-sm mx-auto">
                      Reserve a pitch anytime to play with friends or open a lobby for extra players.
                    </p>
                    <button
                      type="button"
                      onClick={() => navigate('/')}
                      className="mt-2 inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-sm transition-all"
                    >
                      Browse Pitches →
                    </button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {upcomingBookings.map((b) => {
                      const hasLobby = Boolean(b.open_match_id || b.match);
                      const spotsNeeded = b.spots_left ?? (b.match ? b.match.target_players - b.match.current_players_count : null);

                      return (
                        <div
                          key={b.id}
                          className="bg-slate-50/90 border border-slate-200 rounded-2xl p-4 hover:border-emerald-300 transition-all space-y-3 shadow-xs"
                        >
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                            <div className="flex items-start gap-3">
                              <div className="w-11 h-11 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center flex-shrink-0 font-bold text-sm shadow-xs">
                                ⚽
                              </div>
                              <div>
                                <h3 className="text-sm font-bold text-slate-900 leading-tight">
                                  {b.pitch_name || 'Football Pitch'}
                                </h3>
                                <p className="text-xs text-slate-500 mt-0.5">
                                  {b.venue_name || 'Arena'} {b.city ? `· ${b.city}` : ''}
                                </p>
                              </div>
                            </div>

                            {/* Lobby Tag */}
                            <div>
                              {hasLobby ? (
                                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
                                  <Users className="w-3 h-3 text-amber-600" />
                                  Open Lobby (+{spotsNeeded ?? '?'} needed)
                                </span>
                              ) : (
                                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-100/80 text-emerald-800">
                                  Private Session
                                </span>
                              )}
                            </div>
                          </div>

                          {/* Time & Price metadata */}
                          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 py-2 px-3 bg-white rounded-xl border border-slate-100 text-xs">
                            <div>
                              <span className="text-[10px] text-slate-400 uppercase font-bold block">
                                Time Slot
                              </span>
                              <span className="font-semibold text-slate-800">
                                {formatBookingTime(b.start_time)}
                              </span>
                            </div>
                            <div>
                              <span className="text-[10px] text-slate-400 uppercase font-bold block">
                                Total Price
                              </span>
                              <span className="font-semibold text-slate-800">{b.total_price} RON</span>
                            </div>
                            <div>
                              <span className="text-[10px] text-slate-400 uppercase font-bold block">
                                Status
                              </span>
                              <span className="font-bold text-emerald-600">{b.status}</span>
                            </div>
                          </div>

                          {/* Actions Bar */}
                          <div className="flex flex-wrap items-center justify-end gap-2 pt-1">
                            {!hasLobby ? (
                              <button
                                type="button"
                                onClick={() => handleOpenCreateLobby(b)}
                                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs shadow-sm transition-all active:scale-95 cursor-pointer"
                              >
                                <Plus className="w-3.5 h-3.5" />
                                <span>Need Players (+1)</span>
                              </button>
                            ) : (
                              <>
                                <button
                                  type="button"
                                  onClick={() => b.match && handleOpenEditLobby(b.match)}
                                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl border border-amber-300 bg-amber-50 hover:bg-amber-100 text-amber-900 font-bold text-xs transition-colors cursor-pointer"
                                >
                                  <Edit3 className="w-3.5 h-3.5" />
                                  <span>Edit Needed Players (+{spotsNeeded})</span>
                                </button>
                                <button
                                  type="button"
                                  onClick={() => navigate(`/matches?highlight=${b.open_match_id}`)}
                                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs transition-colors cursor-pointer"
                                >
                                  <ExternalLink className="w-3.5 h-3.5" />
                                  <span>View Lobby</span>
                                </button>
                              </>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </section>
            )}

            {/* TAB 2: Joined Matches (+1 Lobbies) */}
            {activeTab === 'JOINED_MATCHES' && (
              <section className="space-y-3">
                {matchesLoading ? (
                  <div className="flex justify-center py-12">
                    <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
                  </div>
                ) : myMatches.length === 0 ? (
                  <div className="text-center py-12 bg-slate-50 rounded-2xl border border-dashed border-slate-200 text-slate-500 space-y-2">
                    <Users className="w-8 h-8 mx-auto text-slate-300" />
                    <p className="text-sm font-bold text-slate-800">You haven't joined any match lobbies yet</p>
                    <p className="text-xs text-slate-400 max-w-sm mx-auto">
                      Join games as a solo player (+1) to play football with teams looking for extra players.
                    </p>
                    <button
                      type="button"
                      onClick={() => navigate('/matches')}
                      className="mt-2 inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-sm transition-all"
                    >
                      Find Open Matches →
                    </button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {myMatches.map((m) => {
                      const userParticipant = m.participants?.find((p) => p.user_id === user?.id);
                      const isOrganizer = m.organizer_id === user?.id;

                      return (
                        <div
                          key={m.id}
                          className="bg-white border border-slate-200 rounded-2xl p-4 hover:border-emerald-300 transition-all space-y-3 shadow-xs"
                        >
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                            <div>
                              <div className="flex items-center gap-2">
                                <h3 className="text-sm font-bold text-slate-900 leading-tight">
                                  {m.pitch_name || 'Pitch Lobby'}
                                </h3>
                                <span
                                  className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                                    m.status === 'OPEN'
                                      ? 'bg-emerald-100 text-emerald-800'
                                      : 'bg-slate-100 text-slate-600'
                                  }`}
                                >
                                  {m.status}
                                </span>
                              </div>
                              <p className="text-xs text-slate-500 mt-0.5">
                                {m.venue_name} {m.city ? `· ${m.city}` : ''}
                              </p>
                            </div>

                            {/* Roster Badge */}
                            <div className="flex items-center gap-2">
                              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-900 border border-amber-200">
                                <Users className="w-3.5 h-3.5 text-amber-600" />
                                {m.current_players_count} / {m.target_players} Players
                              </span>
                            </div>
                          </div>

                          {m.description && (
                            <p className="text-xs text-slate-600 bg-slate-50 p-2.5 rounded-xl border border-slate-100 italic">
                              &ldquo;{m.description}&rdquo;
                            </p>
                          )}

                          {/* My Role / Team side metadata */}
                          <div className="flex flex-wrap items-center justify-between gap-2 text-xs pt-2 border-t border-slate-100">
                            <div className="flex items-center gap-3 text-slate-600">
                              <span>
                                <strong>Date:</strong> {formatBookingTime(m.scheduled_at)}
                              </span>
                              {userParticipant && (
                                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-100 font-bold text-slate-700">
                                  Side {userParticipant.team_side} · {isOrganizer ? 'Organizer' : userParticipant.role}
                                </span>
                              )}
                            </div>

                            <div className="flex items-center gap-2">
                              {isOrganizer && (
                                <button
                                  type="button"
                                  onClick={() => handleOpenEditLobby(m)}
                                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl border border-amber-300 bg-amber-50 hover:bg-amber-100 text-amber-900 font-bold text-xs transition-colors cursor-pointer"
                                >
                                  <Edit3 className="w-3 h-3" />
                                  <span>Edit Players</span>
                                </button>
                              )}
                              <button
                                type="button"
                                onClick={() => navigate(`/matches?highlight=${m.id}`)}
                                className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs transition-colors cursor-pointer"
                              >
                                <ExternalLink className="w-3.5 h-3.5" />
                                <span>View in Open Matches</span>
                              </button>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </section>
            )}

            {/* TAB 3: Past History */}
            {activeTab === 'PAST' && (
              <section className="space-y-3">
                {pastBookings.length === 0 ? (
                  <div className="text-center py-10 bg-slate-50 rounded-xl border border-dashed border-slate-200 text-slate-400 text-xs">
                    No past matches recorded.
                  </div>
                ) : (
                  <div className="space-y-2">
                    {pastBookings.map((b) => (
                      <div
                        key={b.id}
                        className="flex items-center gap-3 bg-slate-50/70 border border-slate-100 rounded-xl p-3 opacity-80"
                      >
                        <div className="w-9 h-9 rounded-lg bg-slate-200 flex items-center justify-center flex-shrink-0 text-slate-600 font-bold text-xs">
                          <Calendar className="w-4 h-4" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-bold text-slate-800 truncate">
                            {b.pitch_name || 'Pitch'} · {b.venue_name || 'Venue'}
                          </p>
                          <p className="text-[11px] text-slate-500 mt-0.5">
                            {formatBookingTime(b.start_time)} · {b.total_price} RON
                          </p>
                        </div>
                        <ShieldCheck className="w-4 h-4 text-emerald-600" />
                      </div>
                    ))}
                  </div>
                )}
              </section>
            )}
          </div>
        </div>
      </div>

      {/* ─── Modal 1: Open New Match Lobby from Booking ─── */}
      {lobbyBooking && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-150">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-lg w-full p-6 space-y-5 animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <div className="w-10 h-10 rounded-2xl bg-amber-100 text-amber-700 flex items-center justify-center">
                  <Users className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-black text-slate-900">Open Match Lobby (+1)</h3>
                  <p className="text-xs text-slate-500">
                    Invite solo players to fill remaining spots for your session
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setLobbyBooking(null)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-xs font-bold text-slate-700 uppercase tracking-wider block mb-1.5">
                  How many extra players do you need? (+X)
                </label>
                <div className="grid grid-cols-5 gap-2">
                  {[1, 2, 3, 4, 5].map((num) => (
                    <button
                      key={num}
                      type="button"
                      onClick={() => setCreateSpotsNeeded(num)}
                      className={`py-2 rounded-xl text-xs font-black border transition-all cursor-pointer ${
                        createSpotsNeeded === num
                          ? 'bg-amber-500 text-white border-amber-500 shadow-sm'
                          : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      +{num}
                    </button>
                  ))}
                </div>
                <div className="mt-2 flex items-center gap-2">
                  <span className="text-xs text-slate-500">Or custom amount:</span>
                  <input
                    type="number"
                    min={1}
                    max={21}
                    value={createSpotsNeeded}
                    onChange={(e) => setCreateSpotsNeeded(Math.max(1, Number(e.target.value)))}
                    className="w-20 px-3 py-1 text-xs font-bold border border-slate-200 rounded-lg text-center"
                  />
                  <span className="text-xs text-slate-400 font-medium">
                    (Total target players: {1 + Number(createSpotsNeeded)})
                  </span>
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 uppercase tracking-wider block mb-1.5">
                  Positions Needed (Optional)
                </label>
                <div className="flex flex-wrap gap-2">
                  {POSITION_OPTIONS.map((pos) => {
                    const isSelected = createPositions.includes(pos);
                    return (
                      <button
                        key={pos}
                        type="button"
                        onClick={() => handleToggleCreatePosition(pos)}
                        className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all cursor-pointer ${
                          isSelected
                            ? 'bg-emerald-600 text-white border-emerald-600 shadow-xs'
                            : 'bg-slate-50 text-slate-600 border-slate-200 hover:border-slate-300'
                        }`}
                      >
                        {pos}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 uppercase tracking-wider block mb-1.5">
                  Lobby Description
                </label>
                <textarea
                  rows={3}
                  value={createDescription}
                  onChange={(e) => setCreateDescription(e.target.value)}
                  placeholder="e.g., Casual friendly match, all levels welcome! Looking for a goalkeeper."
                  className="w-full p-3 rounded-xl border border-slate-200 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-amber-500"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setLobbyBooking(null)}
                className="px-4 py-2 text-xs font-bold text-slate-600 hover:text-slate-800"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmCreateLobby}
                disabled={createMatch.isPending}
                className="px-5 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs shadow-md shadow-amber-500/20 active:scale-95 transition-all flex items-center gap-2 cursor-pointer disabled:opacity-50"
              >
                {createMatch.isPending ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Creating Lobby…</span>
                  </>
                ) : (
                  <span>Publish Open Lobby (+1)</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─── Modal 2: Edit Existing Match Lobby ─── */}
      {editingMatch && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-150">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-lg w-full p-6 space-y-5 animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <div className="w-10 h-10 rounded-2xl bg-amber-100 text-amber-700 flex items-center justify-center">
                  <Edit3 className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-black text-slate-900">Edit Match Lobby</h3>
                  <p className="text-xs text-slate-500">
                    Adjust needed players or position preferences
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setEditingMatch(null)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div className="p-3 bg-amber-50/70 border border-amber-200 rounded-xl text-xs text-amber-900">
                <span>Currently confirmed players: </span>
                <strong>{editingMatch.current_players_count}</strong>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 uppercase tracking-wider block mb-1.5">
                  How many extra players are needed? (+X)
                </label>
                <div className="grid grid-cols-5 gap-2">
                  {[1, 2, 3, 4, 5].map((num) => (
                    <button
                      key={num}
                      type="button"
                      onClick={() => setEditSpotsNeeded(num)}
                      className={`py-2 rounded-xl text-xs font-black border transition-all cursor-pointer ${
                        editSpotsNeeded === num
                          ? 'bg-amber-500 text-white border-amber-500 shadow-sm'
                          : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      +{num}
                    </button>
                  ))}
                </div>
                <div className="mt-2 flex items-center gap-2">
                  <span className="text-xs text-slate-500">Or custom amount:</span>
                  <input
                    type="number"
                    min={0}
                    max={20}
                    value={editSpotsNeeded}
                    onChange={(e) => setEditSpotsNeeded(Math.max(0, Number(e.target.value)))}
                    className="w-20 px-3 py-1 text-xs font-bold border border-slate-200 rounded-lg text-center"
                  />
                  <span className="text-xs text-slate-400 font-medium">
                    (Total target players will be: {(editingMatch.current_players_count || 1) + Number(editSpotsNeeded)})
                  </span>
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 uppercase tracking-wider block mb-1.5">
                  Positions Needed
                </label>
                <div className="flex flex-wrap gap-2">
                  {POSITION_OPTIONS.map((pos) => {
                    const isSelected = editPositions.includes(pos);
                    return (
                      <button
                        key={pos}
                        type="button"
                        onClick={() => handleToggleEditPosition(pos)}
                        className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all cursor-pointer ${
                          isSelected
                            ? 'bg-emerald-600 text-white border-emerald-600 shadow-xs'
                            : 'bg-slate-50 text-slate-600 border-slate-200 hover:border-slate-300'
                        }`}
                      >
                        {pos}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 uppercase tracking-wider block mb-1.5">
                  Lobby Description
                </label>
                <textarea
                  rows={3}
                  value={editDescription}
                  onChange={(e) => setEditDescription(e.target.value)}
                  className="w-full p-3 rounded-xl border border-slate-200 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-amber-500"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setEditingMatch(null)}
                className="px-4 py-2 text-xs font-bold text-slate-600 hover:text-slate-800"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmUpdateLobby}
                disabled={updateMatch.isPending}
                className="px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs shadow-md transition-all flex items-center gap-2 cursor-pointer disabled:opacity-50"
              >
                {updateMatch.isPending ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Saving Changes…</span>
                  </>
                ) : (
                  <span>Save Changes</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProfilePage;
