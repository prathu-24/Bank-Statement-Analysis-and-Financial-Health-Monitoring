import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import DashboardLayout from './layouts/DashboardLayout';
import UploadPage from './pages/UploadPage';
import DashboardPage from './pages/DashboardPage';
import TransactionsPage from './pages/TransactionsPage';
import RecurringPage from './pages/RecurringPage';
import ForecastPage from './pages/ForecastPage';

function InsightsPlaceholder() {
  return (
    <div className="max-w-4xl mx-auto py-12 text-center text-slate-400">
      <h2 className="text-xl font-bold text-white mb-2">Financial Health & Explainable AI Insights</h2>
      <p className="text-xs">Phase 5 module: 100-point transparent health scoring, distress signals, and budget recommendations.</p>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DashboardLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="upload" element={<UploadPage />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="transactions" element={<TransactionsPage />} />
          <Route path="recurring" element={<RecurringPage />} />
          <Route path="forecast" element={<ForecastPage />} />
          <Route path="insights" element={<InsightsPlaceholder />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
