import axios from 'axios';
import { ensureCsrf } from './csrf';

const BASE_URL = import.meta.env.VITE_BACKEND_URL;
const SAFE = new Set(['get', 'head', 'options', 'trace']);

const client = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
});

client.interceptors.request.use(async (config) => {
  const method = (config.method || 'get').toLowerCase();
  if (!SAFE.has(method)) {
    const token = await ensureCsrf();
    if (token) {
      config.headers = config.headers || {};
      config.headers['X-CSRFToken'] = token;
      config.headers['X-Requested-With'] = 'XMLHttpRequest';
    }
  }
  return config;
});

export default client;
