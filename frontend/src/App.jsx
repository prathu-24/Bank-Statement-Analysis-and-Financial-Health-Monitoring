import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import DashboardLayout from './layouts/DashboardLayout';
import LoginPage from './pages/LoginPage';
import UploadPage from './pages/UploadPage';
import DashboardPage from './pages/DashboardPage';
import TransactionsPage from './pages/TransactionsPage';
import RecurringPage from './pages/RecurringPage';
import ForecastPage from './pages/ForecastPage';
import InsightsPage from './pages/InsightsPage';

export default function App() {
  const getInitialRedirect = () => {
    try {
      const savedUser = localStorage.getItem('finsight_user');
      return savedUser ? '/dashboard' : '/login';
    } catch (e) {
      return '/login';
    }
  };

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<DashboardLayout />}>
          <Route index element={<Navigate to={getInitialRedirect()} replace />} />
          <Route path="upload" element={<UploadPage />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="transactions" element={<TransactionsPage />} />
          <Route path="recurring" element={<RecurringPage />} />
          <Route path="forecast" element={<ForecastPage />} />
          <Route path="insights" element={<InsightsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
