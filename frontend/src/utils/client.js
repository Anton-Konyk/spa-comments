import axios from 'axios';
import { getCachedCsrfToken, ensureCsrf } from '@/utils/csrf.js';

const client = axios.create({
  baseURL: import.meta.env.VITE_BACKEND_URL,
  withCredentials: true,
});

client.interceptors.request.use(async (config) => {
  const method = (config.method || 'get').toLowerCase();
  const needsCsrf = ['post', 'put', 'patch', 'delete'].includes(method);

  if (needsCsrf) {
    let token = getCachedCsrfToken();
    if (!token) token = await ensureCsrf();

    if (token) {
      config.headers = config.headers || {};
      if (!('X-CSRFToken' in config.headers)) {
        config.headers['X-CSRFToken'] = token;
      }
      if (!('X-Requested-With' in config.headers)) {
        config.headers['X-Requested-With'] = 'XMLHttpRequest';
      }
    }
  }

  return config;
});

export default client;
