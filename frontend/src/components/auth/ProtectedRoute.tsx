import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 py-32 gap-3 min-h-[60vh]">
        <Loader2 className="w-10 h-10 animate-spin text-emerald-500" />
        <p className="text-sm font-semibold text-slate-500">Checking credentials…</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Redirect to login page and remember where the user wanted to go
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;

