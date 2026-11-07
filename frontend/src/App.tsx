import React from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import MobileShell from './components/layout/MobileShell';
import ProtectedRoute from './components/auth/ProtectedRoute';
import AIChatDrawer from './components/ai/AIChatDrawer';
import HomePage from './pages/HomePage';
import PitchDetailPage from './pages/PitchDetailPage';
import MatchesPage from './pages/MatchesPage';
import ProfilePage from './pages/ProfilePage';
import AIAssistantPage from './pages/AIAssistantPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import { useAuth } from './context/AuthContext';

const AUTH_ROUTES = ['/login', '/register'];

const App: React.FC = () => {
  const location = useLocation();
  const { isAuthenticated, isLoading } = useAuth();
  const isAuthRoute = AUTH_ROUTES.some((r) => location.pathname.startsWith(r));

  return (
    <MobileShell>
      <Routes>
        {/* Auth routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Protected App routes: User must be signed in */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <HomePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/pitches/:id"
          element={
            <ProtectedRoute>
              <PitchDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/matches"
          element={
            <ProtectedRoute>
              <MatchesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <ProfilePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/ai-assistant"
          element={
            <ProtectedRoute>
              <AIAssistantPage />
            </ProtectedRoute>
          }
        />

        {/* Fallback: Unauthenticated goes to /login, Authenticated goes to / */}
        <Route
          path="*"
          element={<Navigate to={isAuthenticated ? '/' : '/login'} replace />}
        />
      </Routes>

      {/* Global AI Assistant Floating Drawer — only when signed in */}
      {isAuthenticated && !isAuthRoute && !isLoading && <AIChatDrawer />}
    </MobileShell>
  );
};

export default App;
