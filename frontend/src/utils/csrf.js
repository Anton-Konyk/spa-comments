import Cookies from 'js-cookie';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;
const CSRF_COOKIE = 'csrftoken';

let inflight = null;

export function getCsrfTokenFromCookie() {
  return Cookies.get(CSRF_COOKIE) || null;
}

export async function ensureCsrf() {
  let token = getCsrfTokenFromCookie();

  if (token) return token;

  if (inflight) {
    await inflight;
    return getCsrfTokenFromCookie();
  }

  const url = new URL('/api/v1/config/?format=json', BACKEND_URL).toString();
  inflight = fetch(url, { credentials: 'include', cache: 'no-store' })
    .then((r) => r.json().catch(() => ({})))
    .finally(() => {
      inflight = null;
    });

  try {
    const data = await inflight;
    return getCsrfTokenFromCookie() || data?.csrfToken || null;
  } catch {
    return getCsrfTokenFromCookie();
  }
}
