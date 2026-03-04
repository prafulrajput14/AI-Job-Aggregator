import axios from 'axios';

// When deployed on Vercel, VITE_API_URL will be populated with the Render Backend URL.
// When running locally, it falls back to the local Vite proxy (which goes to localhost:8000).
const API_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
    baseURL: API_URL,
});

export default api;
