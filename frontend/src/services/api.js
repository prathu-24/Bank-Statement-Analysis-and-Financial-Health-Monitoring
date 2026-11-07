import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach Authorization Bearer token to all outgoing requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('finsight_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle expired or invalid session tokens
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !error.config.url.includes('/auth/login')) {
      localStorage.removeItem('finsight_token');
      localStorage.removeItem('finsight_user');
      if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const statementApi = {
  uploadStatement: async (file, accountName = null, accountNumber = null) => {
    const formData = new FormData();
    formData.append('file', file);
    if (accountName) formData.append('account_holder_name', accountName);
    if (accountNumber) formData.append('account_number', accountNumber);
    const response = await api.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  loadDemoStatement: async (demoType) => {
    const response = await api.post(`/upload/demo/${demoType}`);
    return response.data;
  },

  uploadWithMapping: async (file, mapping, accountName = null, accountNumber = null) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('mapping', JSON.stringify(mapping));
    if (accountName) formData.append('account_holder_name', accountName);
    if (accountNumber) formData.append('account_number', accountNumber);
    const response = await api.post('/upload/mapped', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  confirmTransactions: async (transactions) => {
    const response = await api.post('/upload/confirm', transactions);
    return response.data;
  },

  getTransactions: async (params = {}) => {
    const response = await api.get('/transactions', { params });
    return response.data;
  },

  updateCategory: async (id, category, applyToAll = false) => {
    const response = await api.patch(`/transactions/${id}/category`, {
      category,
      apply_to_all_merchant: applyToAll,
    });
    return response.data;
  },

  confirmTransaction: async (id) => {
    const response = await api.post(`/transactions/${id}/confirm`);
    return response.data;
  },

  getDashboardSummary: async (month = null) => {
    const response = await api.get('/dashboard/summary', { params: { month } });
    return response.data;
  },

  getRecurringPayments: async () => {
    const response = await api.get('/recurring');
    return response.data;
  },

  getAnomalies: async () => {
    const response = await api.get('/anomalies');
    return response.data;
  },

  dismissAnomaly: async (alertId) => {
    const response = await api.post(`/anomalies/${alertId}/dismiss`);
    return response.data;
  },

  getHealthScore: async () => {
    const response = await api.get('/health/score');
    return response.data;
  },

  getDistressSignals: async () => {
    const response = await api.get('/health/distress');
    return response.data;
  },

  getRiskRadar: async () => {
    const response = await api.get('/health/radar');
    return response.data;
  },

  getCashFlowForecast: async (days = 30) => {
    const response = await api.get('/forecast', { params: { days } });
    return response.data;
  },

  getProbabilisticForecast: async (days = 30, nPaths = 2000, seed = 42) => {
    const response = await api.get('/forecast/probabilistic', { params: { days, n_paths: nPaths, seed } });
    return response.data;
  },

  getForecastBacktest: async (holdoutDays = 30, seed = 42) => {
    const response = await api.get('/forecast/backtest', { params: { holdout_days: holdoutDays, seed } });
    return response.data;
  },

  getCounterfactualActions: async (days = 30, seed = 42) => {
    const response = await api.get('/forecast/actions', { params: { days, seed } });
    return response.data;
  },

  getInsights: async () => {
    const response = await api.get('/insights');
    return response.data;
  },

  getEvidence: async (params = {}) => {
    const response = await api.get('/evidence', { params });
    return response.data;
  },

  deleteAllData: async () => {
    const response = await api.delete('/privacy/delete-all');
    return response.data;
  },

  getPrivacyStatus: async () => {
    const response = await api.get('/privacy/status');
    return response.data;
  },

  getLeakage: async () => {
    const response = await api.get('/leakage');
    return response.data;
  },

  askStatement: async (question) => {
    const response = await api.post('/query/ask', { question });
    return response.data;
  },

  login: async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  },
};

export default api;

