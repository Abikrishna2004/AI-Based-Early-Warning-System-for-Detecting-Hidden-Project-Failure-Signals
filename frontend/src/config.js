// Centralized API Base URL configuration

// 1. Localhost Backend (FastAPI running locally on your computer)
export const LOCAL_API_URL = 'http://localhost:8000';

// 2. Render Cloud Backend (FastAPI running live on Render)
export const RENDER_API_URL = 'https://compilepulse.onrender.com';

// Active Backend Selection:
// - If VITE_API_URL is set in environment (or .env / .env.local), use that URL.
// - In local development (npm run dev), defaults to '/api' (proxied by Vite to http://localhost:8000).
// - In production build, defaults to the live Render cloud backend.
export const API_BASE_URL = 
  import.meta.env.VITE_API_URL || 
  (import.meta.env.DEV ? '/api' : RENDER_API_URL);
