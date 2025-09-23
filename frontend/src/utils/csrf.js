let csrfTokenCache = null;

let inflight = null;

export function getCachedCsrfToken() {
  return csrfTokenCache;
}

export function setCachedCsrfToken(token) {
  if (token) csrfTokenCache = token;
}

/**
 * Guarantees the presence of a CSRF token:
 * - If it's already in the cache, it will return it.
 * - Otherwise, it will retrieve /api/v1/config/ (it will set a cookie on the backend domain
 * and return the token in JSON), store it in the cache, and return it.
 */
export async function ensureCsrf() {
  if (csrfTokenCache) return csrfTokenCache;

  if (inflight) {
    await inflight;
    return csrfTokenCache;
  }

  const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;
  const url = new URL('/api/v1/config/?format=json&lang=en', BACKEND_URL).toString();

  inflight = fetch(url, { credentials: 'include', cache: 'no-store' })
    .then((r) => r.json().catch(() => ({})))
    .then((data) => {
      if (data?.csrfToken) csrfTokenCache = data.csrfToken;
    })
    .finally(() => {
      inflight = null;
    });

  await inflight;
  return csrfTokenCache;
}
