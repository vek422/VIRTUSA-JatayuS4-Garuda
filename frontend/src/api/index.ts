import axios from 'axios';

const BASE_URL = import.meta.env.VITE_BASE_URL || 'http://localhost:8000';

const api = axios.create({
    baseURL: BASE_URL,
    withCredentials: true,
    headers: {
        'Content-Type': 'application/json'
    }
});

let getAuthToken: (() => string | null) | null = null;

export const setAuthTokenGetter = (tokenGetter: () => string | null) => {
    getAuthToken = tokenGetter;
};

api.interceptors.request.use((config) => {
    if (getAuthToken) {
        const token = getAuthToken();
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
    }
    return config;
});

export default api

