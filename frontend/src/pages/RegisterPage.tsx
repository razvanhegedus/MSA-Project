import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, Eye, EyeOff, AlertCircle, ChevronLeft } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { UserRole } from '../types/api';

const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<UserRole>('PLAYER');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      await register({ email, password, full_name: fullName, phone, role });
      navigate('/');
    } catch {
      setError('Registration failed. Email may already be taken.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col flex-1 px-6 py-6">
      {/* Back */}
      <button
        onClick={() => navigate('/login')}
        className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700 mb-6 self-start"
      >
        <ChevronLeft className="w-4 h-4" /> Back to login
      </button>

      <div className="mb-6">
        <h1 className="text-xl font-bold text-slate-900">Create Account</h1>
        <p className="text-sm text-slate-500 mt-0.5">Join Pitchup and start playing</p>
      </div>

      <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
        {error && (
          <div className="flex items-center gap-2 bg-red-50 border border-red-200 rounded-xl p-3 text-sm text-red-600">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            {error}
          </div>
        )}

        <div>
          <label className="text-xs font-semibold text-slate-700 mb-1 block">Full Name</label>
          <input
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
            placeholder="João Silva"
            className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-white text-sm focus:outline-none focus:border-emerald-500 text-slate-900"
          />
        </div>

        <div>
          <label className="text-xs font-semibold text-slate-700 mb-1 block">Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
            placeholder="your@email.com"
            className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-white text-sm focus:outline-none focus:border-emerald-500 text-slate-900"
          />
        </div>

        <div>
          <label className="text-xs font-semibold text-slate-700 mb-1 block">Phone</label>
          <input
            type="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            required
            placeholder="+40 712 345 678"
            className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-white text-sm focus:outline-none focus:border-emerald-500 text-slate-900"
          />
        </div>

        <div>
          <label className="text-xs font-semibold text-slate-700 mb-1 block">Password</label>
          <div className="relative">
            <input
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              autoComplete="new-password"
              placeholder="Min. 8 characters"
              className="w-full px-4 py-3 pr-12 rounded-xl border border-slate-200 bg-white text-sm focus:outline-none focus:border-emerald-500 text-slate-900"
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
          <label className="text-xs font-semibold text-slate-700 mb-2 block">I am a…</label>
          <div className="grid grid-cols-2 gap-2">
            {([
              { value: 'PLAYER', label: '⚽ Player' },
              { value: 'VENUE_OWNER', label: '🏟️ Venue Owner' },
            ] as Array<{ value: UserRole; label: string }>).map(({ value, label }) => (
              <button
                key={value}
                type="button"
                onClick={() => setRole(value)}
                className={`py-2.5 rounded-xl text-xs font-semibold border transition-all ${
                  role === value
                    ? 'bg-slate-900 text-white border-slate-900'
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
          disabled={isLoading || !email || !password || !fullName || !phone}
          className="w-full h-12 rounded-2xl bg-emerald-600 text-white font-bold text-sm shadow-sm hover:bg-emerald-700 active:scale-[0.98] transition-all disabled:opacity-50 flex items-center justify-center gap-2 mt-2"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" /> Creating account…
            </>
          ) : (
            'Create Account'
          )}
        </button>
      </form>
    </div>
  );
};

export default RegisterPage;

