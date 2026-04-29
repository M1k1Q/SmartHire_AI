// App.jsx — Root router with auth-aware navigation
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './context/AuthContext';

import LoginPage       from './pages/LoginPage';
import RegisterPage    from './pages/RegisterPage';
import HRDashboard     from './pages/HRDashboard';
import JobsPage        from './pages/JobsPage';
import CandidateDashboard   from './pages/CandidateDashboard';
import CandidateRankingPage from './pages/CandidateRankingPage';
import AnalyticsPage   from './pages/AnalyticsPage';
import ProtectedRoute  from './components/ProtectedRoute';

function AppRoutes() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
        <div className="spinner" />
      </div>
    );
  }

  return (
    <Routes>
      {/* Public */}
      <Route path="/login"    element={!user ? <LoginPage />    : <Navigate to="/" replace />} />
      <Route path="/register" element={!user ? <RegisterPage /> : <Navigate to="/" replace />} />

      {/* HR Routes */}
      <Route path="/" element={
        <ProtectedRoute role="hr">
          <HRDashboard />
        </ProtectedRoute>
      } />
      <Route path="/jobs" element={
        <ProtectedRoute role="hr">
          <JobsPage />
        </ProtectedRoute>
      } />
      <Route path="/jobs/:jobId/candidates" element={
        <ProtectedRoute role="hr">
          <CandidateRankingPage />
        </ProtectedRoute>
      } />
      <Route path="/analytics" element={
        <ProtectedRoute role="hr">
          <AnalyticsPage />
        </ProtectedRoute>
      } />

      {/* Candidate Routes */}
      <Route path="/dashboard" element={
        <ProtectedRoute role="candidate">
          <CandidateDashboard />
        </ProtectedRoute>
      } />

      {/* Default redirect */}
      <Route path="*" element={
        user
          ? <Navigate to={user.role === 'hr' ? '/' : '/dashboard'} replace />
          : <Navigate to="/login" replace />
      } />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: 'rgba(13,17,23,0.95)',
              color: '#f1f5f9',
              border: '1px solid rgba(255,255,255,0.1)',
              backdropFilter: 'blur(12px)',
              borderRadius: '12px',
              fontSize: '0.875rem',
            },
            success: { iconTheme: { primary: '#10b981', secondary: '#fff' } },
            error:   { iconTheme: { primary: '#ef4444', secondary: '#fff' } },
          }}
        />
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}
