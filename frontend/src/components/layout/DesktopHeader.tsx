import React, { useState, useRef, useEffect } from 'react';
import { NavLink, Link, useNavigate } from 'react-router-dom';
import {
  Bell,
  LogOut,
  User as UserIcon,
  ChevronDown,
  Sparkles,
  Calendar,
  Users,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface DesktopHeaderProps {
  className?: string;
}

const DesktopHeader: React.FC<DesktopHeaderProps> = ({
  className = '',
}) => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  const userMenuRef = useRef<HTMLDivElement>(null);
  const notifRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false);
      }
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setNotificationsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = async () => {
    setUserMenuOpen(false);
    await logout();
    navigate('/login');
  };

  return (
    <header
      className={`bg-white/95 backdrop-blur-sm border-b border-slate-200 sticky top-0 z-40 px-6 lg:px-8 py-3.5 items-center justify-between ${className}`}
    >
      {/* ─── Left: Brand Logo ─── */}
      <div className="flex items-center">
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-emerald-700 to-emerald-500 flex items-center justify-center text-white shadow-md shadow-emerald-500/20 group-hover:scale-105 transition-transform">
            <span className="text-xl">⚽</span>
          </div>
          <div className="flex flex-col">
            <span className="text-lg font-black tracking-tight text-slate-900 group-hover:text-emerald-700 transition-colors">
              Pitchup
            </span>
            <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-600 -mt-1">
              Arena Booking
            </span>
          </div>
        </Link>
      </div>

      {/* ─── Center: Main Navigation Links ─── */}
      <nav className="flex items-center gap-1.5">
        <NavLink
          to="/"
          end
          className={({ isActive }) =>
            `flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
              isActive
                ? 'bg-emerald-50 text-emerald-700 font-bold shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`
          }
        >
          <Calendar className="w-4 h-4" />
          <span>Pitches</span>
        </NavLink>

        <NavLink
          to="/matches"
          className={({ isActive }) =>
            `flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
              isActive
                ? 'bg-emerald-50 text-emerald-700 font-bold shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`
          }
        >
          <Users className="w-4 h-4" />
          <span>Open Matches</span>
          <span className="px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800">
            +1
          </span>
        </NavLink>

        <NavLink
          to="/profile"
          className={({ isActive }) =>
            `flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
              isActive
                ? 'bg-emerald-50 text-emerald-700 font-bold shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`
          }
        >
          <UserIcon className="w-4 h-4" />
          <span>My Bookings</span>
        </NavLink>

        <NavLink
          to="/ai-assistant"
          className={({ isActive }) =>
            `flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
              isActive
                ? 'bg-emerald-50 text-emerald-700 font-bold shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`
          }
        >
          <Sparkles className="w-4 h-4 text-emerald-600" />
          <span>AI Scout</span>
        </NavLink>
      </nav>

      {/* ─── Right: Notification & User Profile Menu ─── */}
      <div className="flex items-center gap-3">
        {/* Notification Bell */}
        <div className="relative" ref={notifRef}>
          <button
            type="button"
            onClick={() => setNotificationsOpen(!notificationsOpen)}
            aria-label="Notifications"
            className="relative p-2.5 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-emerald-500 ring-2 ring-white" />
          </button>

          {notificationsOpen && (
            <div className="absolute right-0 mt-2 w-72 bg-white border border-slate-200 rounded-2xl shadow-xl p-4 z-50 animate-in fade-in zoom-in-95 duration-100">
              <div className="flex items-center justify-between pb-2 border-b border-slate-100 mb-2">
                <span className="text-xs font-bold text-slate-900">Notifications</span>
                <span className="text-[10px] text-emerald-600 font-semibold">1 New</span>
              </div>
              <div className="p-2.5 rounded-xl bg-emerald-50/70 border border-emerald-100 text-xs">
                <p className="font-semibold text-emerald-950">Match Lobbies Open!</p>
                <p className="text-emerald-800 text-[11px] mt-0.5">
                  A new 6v6 squad challenge in your area needs a Goalkeeper tonight.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* User Account / Sign In */}
        {isAuthenticated && user ? (
          <div className="relative" ref={userMenuRef}>
            <button
              type="button"
              onClick={() => setUserMenuOpen(!userMenuOpen)}
              className="flex items-center gap-2.5 pl-2 pr-3 py-1.5 rounded-2xl border border-slate-200 bg-slate-50 hover:bg-slate-100 transition-colors"
            >
              <div className="w-8 h-8 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-xs uppercase shadow-sm">
                {user.full_name ? user.full_name.charAt(0) : 'U'}
              </div>
              <div className="text-left hidden sm:block">
                <p className="text-xs font-bold text-slate-900 leading-tight truncate max-w-[120px]">
                  {user.full_name || user.email}
                </p>
                <p className="text-[10px] font-semibold text-slate-400 capitalize">
                  {user.role?.toLowerCase() || 'player'}
                </p>
              </div>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            </button>

            {userMenuOpen && (
              <div className="absolute right-0 mt-2 w-56 bg-white border border-slate-200 rounded-2xl shadow-xl py-2 z-50 animate-in fade-in zoom-in-95 duration-100">
                <div className="px-4 py-2 border-b border-slate-100">
                  <p className="text-xs font-bold text-slate-900 truncate">{user.full_name}</p>
                  <p className="text-[11px] text-slate-500 truncate">{user.email}</p>
                  <span className="inline-block mt-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-600">
                    {user.role}
                  </span>
                </div>
                <Link
                  to="/profile"
                  onClick={() => setUserMenuOpen(false)}
                  className="w-full px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 flex items-center gap-2 transition-colors"
                >
                  <UserIcon className="w-4 h-4 text-slate-400" />
                  My Profile & Bookings
                </Link>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="w-full text-left px-4 py-2 text-xs font-medium text-red-600 hover:bg-red-50 flex items-center gap-2 transition-colors"
                >
                  <LogOut className="w-4 h-4 text-red-400" />
                  Sign Out
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <Link
              to="/login"
              className="px-3.5 py-2 text-xs font-semibold text-slate-700 hover:text-slate-900 hover:bg-slate-100 rounded-xl transition-colors"
            >
              Sign In
            </Link>
            <Link
              to="/register"
              className="px-4 py-2 text-xs font-bold text-white bg-slate-900 hover:bg-slate-800 rounded-xl shadow-sm transition-all active:scale-95"
            >
              Sign Up
            </Link>
          </div>
        )}
      </div>
    </header>
  );
};

export default DesktopHeader;

