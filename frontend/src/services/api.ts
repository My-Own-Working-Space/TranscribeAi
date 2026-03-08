import axios from 'axios';
import { supabase } from './supabase';

const RENDER_URL = 'https://transcribeai-iwaj.onrender.com';
const baseUrl = import.meta.env.VITE_API_URL
  || (window.location.hostname === 'localhost' ? 'http://localhost:8000' : RENDER_URL);
const API_BASE = baseUrl + '/api/v2';
const api = axios.create({ baseURL: API_BASE });

api.interceptors.request.use(async (config) => {
    const { data: { session } } = await supabase.auth.getSession();
    if (session?.access_token) {
        config.headers.Authorization = `Bearer ${session.access_token}`;
    }
    return config;
});

api.interceptors.response.use(
    (res) => res,
    (err) => {
        if (err.response?.status === 401 && window.location.pathname !== '/login') {
            supabase.auth.signOut();
            window.location.href = '/login';
        }
        return Promise.reject(err);
    }
);

export const jobsApi = {
    create: (file: File, mode: string, language?: string, onProgress?: (p: number) => void) => {
        const fd = new FormData();
        fd.append('file', file);
        fd.append('mode', mode);
        if (language) fd.append('language', language);
        return api.post('/jobs/', fd, {
            headers: { 'Content-Type': 'multipart/form-data' },
            onUploadProgress: (e) => {
                if (onProgress && e.total) onProgress(Math.round((e.loaded * 100) / e.total));
            },
        });
    },
    list: () => api.get('/jobs/'),
    get: (id: string) => api.get(`/jobs/${id}`),
    delete: (id: string) => api.delete(`/jobs/${id}`),
    dashboard: () => api.get('/jobs/dashboard'),
    progress: (id: string) => api.get(`/jobs/${id}/progress`),
};

export const aiApi = {
    getSummary: (jobId: string) => api.get(`/jobs/${jobId}/summary`),
    regenerateSummary: (jobId: string, language?: string) => api.post(`/jobs/${jobId}/summary/regenerate${language ? `?language=${language}` : ''}`),
    chat: (jobId: string, message: string) => api.post(`/jobs/${jobId}/chat`, { message }),
    chatHistory: (jobId: string) => api.get(`/jobs/${jobId}/chat/history`),
    getActions: (jobId: string) => api.get(`/jobs/${jobId}/actions`),
    extractActions: (jobId: string) => api.post(`/jobs/${jobId}/actions/extract`),
    updateAction: (jobId: string, actionId: string, data: { is_completed: boolean }) =>
        api.patch(`/jobs/${jobId}/actions/${actionId}`, data),
};

export const feedbackApi = {
    send: (data: { name?: string; email?: string; feedback_type: string; message: string }) =>
        api.post('/feedback/', data),
};

export default api;
