import React from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Calendar, LogOut, Loader2, AlertCircle, ChevronRight, ShieldCheck, Mail, Phone } from 'lucide-react';
import MobileHeader from '../components/layout/MobileHeader';
import { useAuth } from '../context/AuthContext';
import { useUserBookings } from '../api/bookings';

const ProfilePage: React.FC = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const { data: bookings = [], isLoading, isError } = useUserBookings();

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

  const upcoming = bookings.filter(
    (b) => b.status !== 'CANCELLED' && new Date(b.start_time) > new Date()
  );
  const past = bookings.filter(
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

  return (
    <div className="w-full space-y-6">
      <MobileHeader title="My Profile" />

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

            <div className="pt-3 border-t border-slate-100 grid grid-cols-2 gap-2 text-center">
              <div className="p-2.5 bg-slate-50 rounded-xl">
                <p className="text-lg font-black text-slate-900">{upcoming.length}</p>
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Upcoming
                </p>
              </div>
              <div className="p-2.5 bg-slate-50 rounded-xl">
                <p className="text-lg font-black text-slate-900">{past.length}</p>
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Played
                </p>
              </div>
            </div>

            <button
              onClick={() => void handleLogout()}
              className="w-full h-11 rounded-xl border border-red-200 text-red-600 hover:bg-red-50 text-xs font-bold flex items-center justify-center gap-2 transition-colors"
            >
              <LogOut className="w-4 h-4" /> Sign Out
            </button>
          </div>
        </div>

        {/* Right Column: Bookings Lists */}
        <div className="lg:col-span-8 space-y-6">
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-6">
            <div>
              <h2 className="text-base font-bold text-slate-900">My Reservations</h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Keep track of your active pitch bookings and match schedule.
              </p>
            </div>

            {isLoading && (
              <div className="flex justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
              </div>
            )}

            {isError && (
              <div className="flex flex-col items-center gap-2 py-8 text-slate-400">
                <AlertCircle className="w-8 h-8 text-red-400" />
                <p className="text-xs font-bold text-red-500">Could not load bookings</p>
              </div>
            )}

            {!isLoading && !isError && (
              <>
                {/* Upcoming bookings */}
                <section className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                      Upcoming Sessions ({upcoming.length})
                    </h3>
                  </div>

                  {upcoming.length === 0 ? (
                    <div className="text-center py-8 bg-slate-50 rounded-xl border border-dashed border-slate-200 text-slate-400 text-xs">
                      No upcoming bookings scheduled. Explore pitches and book a game!
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {upcoming.map((b) => (
                        <div
                          key={b.id}
                          className="flex items-center gap-3 bg-slate-50/80 border border-slate-200 rounded-xl p-3.5 hover:border-emerald-300 transition-colors"
                        >
                          <div className="w-10 h-10 rounded-xl bg-emerald-100 flex items-center justify-center flex-shrink-0">
                            <Calendar className="w-5 h-5 text-emerald-600" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-bold text-slate-900 truncate">
                              {formatBookingTime(b.start_time)}
                            </p>
                            <p className="text-[11px] text-slate-500 mt-0.5">
                              {b.total_price} RON · <span className="font-semibold text-emerald-700">{b.status}</span>
                            </p>
                          </div>
                          <ChevronRight className="w-4 h-4 text-slate-400 flex-shrink-0" />
                        </div>
                      ))}
                    </div>
                  )}
                </section>

                {/* Past bookings */}
                {past.length > 0 && (
                  <section className="space-y-3 pt-4 border-t border-slate-100">
                    <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                      Past Matches ({past.length})
                    </h3>
                    <div className="space-y-2">
                      {past.slice(0, 5).map((b) => (
                        <div
                          key={b.id}
                          className="flex items-center gap-3 bg-slate-50/60 border border-slate-100 rounded-xl p-3 opacity-80"
                        >
                          <div className="w-8 h-8 rounded-lg bg-slate-200 flex items-center justify-center flex-shrink-0">
                            <Calendar className="w-4 h-4 text-slate-500" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-semibold text-slate-700 truncate">
                              {formatBookingTime(b.start_time)}
                            </p>
                            <p className="text-[11px] text-slate-400 mt-0.5">
                              {b.total_price} RON · {b.status}
                            </p>
                          </div>
                          <ShieldCheck className="w-4 h-4 text-slate-300" />
                        </div>
                      ))}
                    </div>
                  </section>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
