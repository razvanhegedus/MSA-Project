import React from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Calendar, LogOut, Loader2, AlertCircle, ChevronRight } from 'lucide-react';
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
      <>
        <MobileHeader title="Profile" />
        <div className="flex flex-col items-center justify-center flex-1 py-20 gap-4 px-6">
          <User className="w-16 h-16 text-slate-200" />
          <p className="text-sm font-semibold text-slate-700 text-center">
            Sign in to view your bookings and hosted matches
          </p>
          <button
            onClick={() => navigate('/login')}
            className="w-full max-w-xs h-11 rounded-xl bg-slate-900 text-white font-bold text-sm"
          >
            Sign In
          </button>
          <button
            onClick={() => navigate('/register')}
            className="text-sm font-medium text-emerald-600"
          >
            Create account →
          </button>
        </div>
      </>
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
    <>
      <MobileHeader title="My Profile" />

      {/* User card */}
      <div className="mx-4 mt-4 bg-white border border-slate-200 rounded-2xl p-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-700 font-bold text-lg">
            {user?.full_name.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-bold text-slate-900 truncate">{user?.full_name}</p>
            <p className="text-xs text-slate-500 truncate">{user?.email}</p>
            <span className="inline-block mt-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-600">
              {user?.role}
            </span>
          </div>
        </div>
      </div>

      {/* Bookings section */}
      <div className="flex-1 px-4 py-4 space-y-5 overflow-y-auto">
        {isLoading && (
          <div className="flex justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-emerald-500" />
          </div>
        )}
        {isError && (
          <div className="flex flex-col items-center gap-2 py-6 text-slate-400">
            <AlertCircle className="w-6 h-6 text-red-400" />
            <p className="text-xs text-red-400">Could not load bookings</p>
          </div>
        )}

        {!isLoading && !isError && (
          <>
            {/* Upcoming bookings */}
            <section>
              <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">
                Upcoming ({upcoming.length})
              </h2>
              {upcoming.length === 0 ? (
                <div className="text-center py-6 text-slate-400 text-xs">
                  No upcoming bookings. Book a pitch! ⚽
                </div>
              ) : (
                <div className="space-y-2">
                  {upcoming.map((b) => (
                    <div
                      key={b.id}
                      className="flex items-center gap-3 bg-white border border-slate-200 rounded-xl p-3"
                    >
                      <div className="w-9 h-9 rounded-xl bg-emerald-100 flex items-center justify-center flex-shrink-0">
                        <Calendar className="w-4 h-4 text-emerald-600" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-semibold text-slate-900 truncate">
                          {formatBookingTime(b.start_time)}
                        </p>
                        <p className="text-[11px] text-slate-500 mt-0.5">
                          {b.total_price} RON · {b.status}
                        </p>
                      </div>
                      <ChevronRight className="w-4 h-4 text-slate-300 flex-shrink-0" />
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Past bookings */}
            {past.length > 0 && (
              <section>
                <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">
                  Past ({past.length})
                </h2>
                <div className="space-y-2">
                  {past.slice(0, 5).map((b) => (
                    <div
                      key={b.id}
                      className="flex items-center gap-3 bg-slate-50 border border-slate-100 rounded-xl p-3 opacity-70"
                    >
                      <div className="w-9 h-9 rounded-xl bg-slate-100 flex items-center justify-center flex-shrink-0">
                        <Calendar className="w-4 h-4 text-slate-400" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-semibold text-slate-600 truncate">
                          {formatBookingTime(b.start_time)}
                        </p>
                        <p className="text-[11px] text-slate-400 mt-0.5">{b.total_price} RON</p>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}
          </>
        )}
      </div>

      {/* Logout */}
      <div className="px-4 pb-4">
        <button
          onClick={() => void handleLogout()}
          className="w-full h-11 rounded-xl border border-red-200 text-red-500 text-sm font-semibold flex items-center justify-center gap-2 hover:bg-red-50 active:scale-[0.98] transition-all"
        >
          <LogOut className="w-4 h-4" /> Sign Out
        </button>
      </div>
    </>
  );
};

export default ProfilePage;

