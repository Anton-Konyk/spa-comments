import axios from 'axios';
import { getCachedCsrfToken, ensureCsrf, refreshCsrf, resetCsrfToken } from '@/utils/csrf.js';

const client = axios.create({
  baseURL: import.meta.env.VITE_BACKEND_URL,
  withCredentials: true,
});

const UNSAFE = new Set(['post', 'put', 'patch', 'delete']);

client.interceptors.request.use(async (config) => {
  const method = (config.method || 'get').toLowerCase();
  if (UNSAFE.has(method)) {
    let token = getCachedCsrfToken();
    if (!token) token = await ensureCsrf();

    config.headers = config.headers || {};
    // Django-friendly header
    if (!('X-Requested-With' in config.headers)) {
      config.headers['X-Requested-With'] = 'XMLHttpRequest';
    }
    if (token && !('X-CSRFToken' in config.headers)) {
      config.headers['X-CSRFToken'] = token;
    }
  }
  return config;
});

client.interceptors.response.use(
  (r) => r,
  async (error) => {
    const resp = error?.response;
    const cfg = error?.config || {};
    const is403 = resp?.status === 403;
    const body = typeof resp?.data === 'string' ? resp.data : JSON.stringify(resp?.data || {});
    const looksLikeCsrf = /csrf/i.test(body);

    if (is403 && looksLikeCsrf && !cfg._csrfRetried) {
      // after login/logout
      await refreshCsrf();
      return client({ ...cfg, _csrfRetried: true });
    }
    throw error;
  }
);

export { refreshCsrf, resetCsrfToken };
export default client;
