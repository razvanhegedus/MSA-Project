import React from 'react';
import { NavLink } from 'react-router-dom';
import { Home, Users, User, Sparkles } from 'lucide-react';

const NAV_ITEMS = [
  { to: '/', icon: Home, label: 'Pitches' },
  { to: '/matches', icon: Users, label: 'Lobbies' },
  { to: '/ai-assistant', icon: Sparkles, label: 'AI Scout' },
  { to: '/profile', icon: User, label: 'Profile' },
] as const;

const BottomNav: React.FC = () => {
  return (
    <nav className="fixed bottom-0 max-w-md mx-auto inset-x-0 bg-white/95 backdrop-blur-md border-t border-slate-200 px-6 py-3 flex justify-around items-center z-40">
      {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
        <NavLink
          key={to}
          to={to}
          end={to === '/'}
          className={({ isActive }) =>
            `flex flex-col items-center gap-0.5 min-w-[44px] transition-colors ${
              isActive ? 'text-emerald-600' : 'text-slate-400 hover:text-slate-600'
            }`
          }
        >
          {({ isActive }) => (
            <>
              <div
                className={`flex items-center justify-center w-10 h-10 rounded-xl transition-all ${
                  isActive ? 'bg-emerald-50' : 'hover:bg-slate-50'
                }`}
              >
                <Icon className="w-5 h-5" />
              </div>
              <span className="text-[10px] font-semibold">{label}</span>
            </>
          )}
        </NavLink>
      ))}
    </nav>
  );
};

export default BottomNav;

