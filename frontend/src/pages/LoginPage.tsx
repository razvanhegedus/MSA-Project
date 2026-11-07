import React, { useState } from 'react';
import { useNavigate, useLocation, Navigate } from 'react-router-dom';
import { Loader2, Eye, EyeOff, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated, isLoading: authLoading } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Where to navigate after login
  const fromLocation = (location.state as { from?: { pathname?: string } })?.from?.pathname || '/';

  // If already logged in, redirect away from login page
  if (!authLoading && isAuthenticated) {
    return <Navigate to={fromLocation} replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login({ email, password });
      navigate(fromLocation, { replace: true });
    } catch {
      setError('Invalid email or password');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (authLoading) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 py-32 gap-3 min-h-[60vh]">
        <Loader2 className="w-10 h-10 animate-spin text-emerald-500" />
        <p className="text-sm font-semibold text-slate-500">Loading…</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col flex-1 items-center justify-center py-8 px-4 w-full">
      <div className="bg-white rounded-3xl border border-slate-200 shadow-md p-6 sm:p-8 max-w-md w-full mx-auto space-y-6">
        {/* Logo area */}
        <div className="text-center space-y-1">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-emerald-600 to-emerald-400 flex items-center justify-center text-white text-2xl shadow-md shadow-emerald-500/20 mx-auto mb-3">
            ⚽
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Sign In to Pitchup</h1>
          <p className="text-xs sm:text-sm text-slate-500">
            Book your pitch. Find your squad (+1). Manage tournaments.
          </p>
        </div>

        <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
          {error && (
            <div className="flex items-center gap-2.5 bg-red-50 border border-red-200 rounded-xl p-3 text-xs sm:text-sm font-medium text-red-600 animate-in fade-in">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="text-xs font-bold text-slate-700 mb-1.5 block uppercase tracking-wider">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              placeholder="player@example.com"
              className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 text-sm focus:outline-none focus:border-emerald-500 focus:bg-white text-slate-900 transition-all"
            />
          </div>

          <div>
            <label className="text-xs font-bold text-slate-700 mb-1.5 block uppercase tracking-wider">
              Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                placeholder="••••••••"
                className="w-full px-4 py-3 pr-12 rounded-xl border border-slate-200 bg-slate-50 text-sm focus:outline-none focus:border-emerald-500 focus:bg-white text-slate-900 transition-all"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting || !email || !password}
            className="w-full h-12 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm shadow-md shadow-emerald-600/20 active:scale-[0.99] transition-all disabled:opacity-50 flex items-center justify-center gap-2 mt-2"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" /> Signing in…
              </>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        <div className="pt-4 border-t border-slate-100 text-center space-y-2">
          <p className="text-xs text-slate-500">
            Don&apos;t have an account yet?{' '}
            <button
              type="button"
              onClick={() => navigate('/register')}
              className="font-bold text-emerald-600 hover:text-emerald-700 hover:underline"
            >
              Create Account →
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
