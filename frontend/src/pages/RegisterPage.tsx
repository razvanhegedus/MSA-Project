import React, { useState } from 'react';
import { useNavigate, useLocation, Navigate } from 'react-router-dom';
import { Loader2, Eye, EyeOff, AlertCircle, ChevronLeft } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { UserRole } from '../types/api';

const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { register, isAuthenticated, isLoading: authLoading } = useAuth();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<UserRole>('PLAYER');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fromLocation = (location.state as { from?: { pathname?: string } })?.from?.pathname || '/';

  if (!authLoading && isAuthenticated) {
    return <Navigate to={fromLocation} replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await register({ email, password, full_name: fullName, phone, role });
      navigate(fromLocation, { replace: true });
    } catch {
      setError('Registration failed. Email may already be taken or inputs are invalid.');
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
      <div className="bg-white rounded-3xl border border-slate-200 shadow-md p-6 sm:p-8 max-w-md w-full mx-auto space-y-5">
        {/* Back */}
        <button
          type="button"
          onClick={() => navigate('/login')}
          className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" /> Back to sign in
        </button>

        <div className="space-y-1">
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Create Account</h1>
          <p className="text-xs sm:text-sm text-slate-500">
            Join Pitchup to book pitches, organize matches, and enter tournaments.
          </p>
        </div>

        <form onSubmit={(e) => void handleSubmit(e)} className="space-y-3.5">
          {error && (
            <div className="flex items-center gap-2.5 bg-red-50 border border-red-200 rounded-xl p-3 text-xs sm:text-sm font-medium text-red-600 animate-in fade-in">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="text-xs font-bold text-slate-700 mb-1 block uppercase tracking-wider">
              Full Name
            </label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
              placeholder="Alex Popescu"
              className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-sm focus:outline-none focus:border-emerald-500 focus:bg-white text-slate-900 transition-all"
            />
          </div>

          <div>
            <label className="text-xs font-bold text-slate-700 mb-1 block uppercase tracking-wider">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              placeholder="alex@example.com"
              className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-sm focus:outline-none focus:border-emerald-500 focus:bg-white text-slate-900 transition-all"
            />
          </div>

          <div>
            <label className="text-xs font-bold text-slate-700 mb-1 block uppercase tracking-wider">
              Phone Number
            </label>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              required
              placeholder="+40 712 345 678"
              className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-sm focus:outline-none focus:border-emerald-500 focus:bg-white text-slate-900 transition-all"
            />
          </div>

          <div>
            <label className="text-xs font-bold text-slate-700 mb-1 block uppercase tracking-wider">
              Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                autoComplete="new-password"
                placeholder="Min. 8 characters"
                className="w-full px-4 py-2.5 pr-12 rounded-xl border border-slate-200 bg-slate-50 text-sm focus:outline-none focus:border-emerald-500 focus:bg-white text-slate-900 transition-all"
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

          <div>
            <label className="text-xs font-bold text-slate-700 mb-1.5 block uppercase tracking-wider">
              Account Role
            </label>
            <div className="grid grid-cols-2 gap-2">
              {(
                [
                  { value: 'PLAYER', label: '⚽ Football Player' },
                  { value: 'VENUE_OWNER', label: '🏟️ Venue Owner' },
                ] as Array<{ value: UserRole; label: string }>
              ).map(({ value, label }) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setRole(value)}
                  className={`py-2 rounded-xl text-xs font-bold border transition-all ${
                    role === value
                      ? 'bg-slate-900 text-white border-slate-900 shadow-sm'
                      : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting || !email || !password || !fullName || !phone}
            className="w-full h-12 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm shadow-md shadow-emerald-600/20 active:scale-[0.99] transition-all disabled:opacity-50 flex items-center justify-center gap-2 mt-2"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" /> Registering…
              </>
            ) : (
              'Create Account'
            )}
          </button>
        </form>

        <div className="pt-3 border-t border-slate-100 text-center">
          <p className="text-xs text-slate-500">
            Already have an account?{' '}
            <button
              type="button"
              onClick={() => navigate('/login')}
              className="font-bold text-emerald-600 hover:text-emerald-700 hover:underline"
            >
              Sign In →
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
