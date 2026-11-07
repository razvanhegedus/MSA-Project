import React from 'react';
import { useLocation } from 'react-router-dom';
import DesktopHeader from './DesktopHeader';
import BottomNav from './BottomNav';
import { useAuth } from '../../context/AuthContext';

interface MobileShellProps {
  children: React.ReactNode;
}

const AUTH_ROUTES = ['/login', '/register'];

const MobileShell: React.FC<MobileShellProps> = ({ children }) => {
  const location = useLocation();
  const { isAuthenticated, isLoading } = useAuth();
  const isAuthRoute = AUTH_ROUTES.some((r) => location.pathname.startsWith(r));
  const showNav = isAuthenticated && !isAuthRoute && !isLoading;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col">
      {/* Top navigation visible on desktop, hidden on mobile */}
      {showNav && <DesktopHeader className="hidden lg:flex" />}

      <main
        className={`w-full ${
          isAuthRoute || !isAuthenticated
            ? 'max-w-md'
            : 'max-w-md lg:max-w-6xl xl:max-w-7xl'
        } mx-auto px-4 lg:px-8 py-4 lg:py-8 flex-1 flex flex-col`}
      >
        {children}
      </main>

      {/* Bottom mobile navigation visible on mobile, hidden on desktop */}
      {showNav && <BottomNav className="lg:hidden" />}
    </div>
  );
};

export default MobileShell;
