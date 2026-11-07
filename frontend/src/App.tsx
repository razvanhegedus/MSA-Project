import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import MobileShell from './components/layout/MobileShell';
import BottomNav from './components/layout/BottomNav';
import AIChatDrawer from './components/ai/AIChatDrawer';
import HomePage from './pages/HomePage';
import PitchDetailPage from './pages/PitchDetailPage';
import MatchesPage from './pages/MatchesPage';
import ProfilePage from './pages/ProfilePage';
import AIAssistantPage from './pages/AIAssistantPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';

// Pages that should NOT show the bottom nav or AI FAB
const AUTH_ROUTES = ['/login', '/register'];

const App: React.FC = () => {
  const isAuthRoute = AUTH_ROUTES.some((r) => window.location.pathname.startsWith(r));

  return (
    <MobileShell>
      <Routes>
        {/* Auth routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* App routes */}
        <Route path="/" element={<HomePage />} />
        <Route path="/pitches/:id" element={<PitchDetailPage />} />
        <Route path="/matches" element={<MatchesPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/ai-assistant" element={<AIAssistantPage />} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>

      {/* Global persistent UI — only on app routes */}
      {!isAuthRoute && (
        <>
          <BottomNav />
          <AIChatDrawer />
        </>
      )}
    </MobileShell>
  );
};

export default App;

