import Cookies from 'js-cookie';
import axios from 'axios';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

export async function ensureCsrf() {
  let token = Cookies.get('csrftoken');

  if (!token) {
    const res = await axios.get(`${BACKEND_URL}/api/v1/config/?format=json&lang=en`, {
      withCredentials: true,
    });
    token = res.data?.csrfToken || Cookies.get('csrftoken');
  }

  if (token) {
    axios.defaults.withCredentials = true;
    axios.defaults.headers.common['X-CSRFToken'] = token;
  }

  return token;
}
