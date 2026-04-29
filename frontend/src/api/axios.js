// api/axios.js — Configured Axios instance with JWT interceptors
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://127.0.0.1:5000/api',
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
});

// Request interceptor: attach JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log(`[API] Attaching token to ${config.method.toUpperCase()} ${config.url}`);
    } else {
      console.warn(`[API] No token found for ${config.method.toUpperCase()} ${config.url}`);
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: handle 401 (token expiration/invalid)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.warn('[API] 401 Error detected. Session will NOT be cleared automatically to prevent redirect loops.');
      console.error('[API] Error details:', error.response.data);
    } else if (error.response?.status === 403) {
      console.error('[API] 403 Forbidden:', error.response.data);
    }
    return Promise.reject(error);
  }
);

export default api;
