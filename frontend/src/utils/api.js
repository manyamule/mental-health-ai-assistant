import axios from 'axios';
import { API_BASE_URL } from '../config';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth APIs
export const authAPI = {
  login: (credentials) => api.post('/api/auth/login', credentials),
  signup: (userData) => api.post('/api/auth/signup', userData),
  getMe: () => api.get('/api/auth/me'),
};

// Session APIs
export const sessionAPI = {
  startSession: (sessionId, documentContext) => 
    api.post('/api/sessions/start', { session_id: sessionId, document_context: documentContext }),
  getMySessions: (limit = 10) => 
    api.get('/api/sessions/my-sessions', { params: { limit } }),
  getConversations: (sessionId) => 
    api.get(`/api/sessions/${sessionId}/conversations`),
  endSession: (sessionId, sentiment) => 
    api.post(`/api/sessions/${sessionId}/end`, { overall_sentiment: sentiment }),
};

// Appointment APIs
export const appointmentAPI = {
  getCounselors: () => api.get('/api/appointments/counselors'),
  bookAppointment: (appointmentData) => 
    api.post('/api/appointments/book', appointmentData),
  getMyAppointments: () => api.get('/api/appointments/my-appointments'),
};

// Admin APIs
export const adminAPI = {
  getStats: () => api.get('/api/admin/stats'),
  getUsers: (skip = 0, limit = 50) => 
    api.get('/api/admin/users', { params: { skip, limit } }),
  getCounselors: () => api.get('/api/admin/counselors'),
  addCounselor: (counselorData) => 
    api.post('/api/admin/counselors', counselorData),
  updateCounselor: (counselorId, data) => 
    api.put(`/api/admin/counselors/${counselorId}`, data),
  deleteCounselor: (counselorId) => 
    api.delete(`/api/admin/counselors/${counselorId}`),
};

export default api;