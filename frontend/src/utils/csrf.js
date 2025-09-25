let csrfTokenCache = null;
let inflight = null;

export function getCachedCsrfToken() {
  return csrfTokenCache;
}

export function setCachedCsrfToken(token) {
  csrfTokenCache = token || null;
}

export function resetCsrfToken() {
  csrfTokenCache = null;
}

export async function refreshCsrf() {
  const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;
  const url = new URL('/api/v1/config/', BACKEND_URL);
  url.searchParams.set('t', Date.now().toString()); // анти-кэш

  const res = await fetch(url.toString(), {
    credentials: 'include',
    cache: 'no-store',
  });

  let data = {};
  try {
    data = await res.json();
  } catch {}

  csrfTokenCache = data?.csrfToken || null;
  return csrfTokenCache;
}

export async function ensureCsrf() {
  if (csrfTokenCache) return csrfTokenCache;
  if (inflight) {
    await inflight;
    return csrfTokenCache;
  }
  inflight = refreshCsrf().finally(() => (inflight = null));
  await inflight;
  return csrfTokenCache;
}
