import axios from 'axios';
import Cookies from 'js-cookie';
// import { ensureCsrf } from './csrf.js';

// const BASE_URL = import.meta.env.VITE_BACKEND_URL;
// const SAFE = new Set(['get', 'head', 'options', 'trace']);
//
// const client = axios.create({
//   baseURL: BASE_URL,
//   withCredentials: true,
// });
//
// client.interceptors.request.use(async (config) => {
//   const method = (config.method || 'get').toLowerCase();
//   if (!SAFE.has(method)) {
//     const token = await ensureCsrf();
//     if (token) {
//       config.headers = config.headers || {};
//       config.headers['X-CSRFToken'] = token;
//       config.headers['X-Requested-With'] = 'XMLHttpRequest';
//     }
//   }
//   return config;
// });

// export default client;

const client = axios.create({
  baseURL: import.meta.env.VITE_BACKEND_URL,
  withCredentials: true,
});

client.interceptors.request.use((config) => {
  const t = Cookies.get('csrftoken');
  if (t) config.headers['X-CSRFToken'] = t;
  return config;
});

export default client;
