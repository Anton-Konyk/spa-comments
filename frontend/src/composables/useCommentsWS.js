import { ref } from 'vue';
/**
 * WS URL resolution priority:
 * 1) VITE_WS_URL (full ws(s)://…)
 * 2) VITE_BACKEND_URL + VITE_WS_PATH (http->ws, https->wss)
 * 3) window.location.host + VITE_WS_PATH (fallback)
 *
 * Recommended set:
 * - VITE_WS_URL  ИЛИ
 * - VITE_BACKEND_URL и VITE_WS_PATH
 */
function resolveWsUrl() {
  const WS_URL_ENV = (import.meta.env.VITE_WS_URL || '').trim();
  const BACKEND_URL = (import.meta.env.VITE_BACKEND_URL || '').trim();
  const WS_PATH = normalizePath((import.meta.env.VITE_WS_PATH || '/ws/comments/').trim());

  if (WS_URL_ENV) return WS_URL_ENV;

  if (BACKEND_URL) {
    try {
      const u = new URL(BACKEND_URL);
      // http -> ws, https -> wss
      u.protocol = u.protocol === 'https:' ? 'wss:' : 'ws:';

      const base = u.toString().replace(/\/+$/, '');
      return `${base}${WS_PATH}`;
    } catch {
      // fallthrough
    }
  }

  if (typeof window !== 'undefined' && window.location) {
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
    return `${proto}://${window.location.host}${WS_PATH}`;
  }

  throw new Error('WS URL cannot be resolved. Set VITE_WS_URL or VITE_BACKEND_URL/VITE_WS_PATH.');
}

function normalizePath(p) {
  if (!p) return '/';
  return p.startsWith('/') ? p : `/${p}`;
}

export function useCommentsWS({ onEvent }) {
  const isConnected = ref(false);
  let ws = null;
  let heartbeatTimer = null;
  let reconnectTimer = null;
  let reconnectAttempts = 0;

  const WS_URL = resolveWsUrl();

  function startHeartbeat() {
    stopHeartbeat();
    // keep-alive ping 20 c
    heartbeatTimer = setInterval(
      () => {
        try {
          if (ws?.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ ping: Date.now() }));
          }
        } catch (_) {}
      },
      Number(import.meta.env.VITE_WS_HEARTBEAT_MS || 20000)
    );
  }

  function stopHeartbeat() {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer);
      heartbeatTimer = null;
    }
  }

  function scheduleReconnect() {
    if (reconnectTimer) return;
    const maxDelay = Number(import.meta.env.VITE_WS_MAX_RECONNECT_MS || 30000);
    const delay = Math.min(maxDelay, 1000 * Math.pow(2, reconnectAttempts)); // 1s, 2s, 4s… до maxDelay
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null;
      reconnectAttempts += 1;
      connect();
    }, delay);
  }

  function clearReconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    reconnectAttempts = 0;
  }

  function connect() {
    try {
      ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        isConnected.value = true;
        clearReconnect();
        startHeartbeat();
        // optional hello
        try {
          ws.send(JSON.stringify({ client: 'frontend', hello: 'comments' }));
        } catch (_) {}
      };

      ws.onmessage = (evt) => {
        try {
          const data = JSON.parse(evt.data);
          if (typeof onEvent === 'function') onEvent(data);
        } catch {
          // ignore non-JSON frames
        }
      };

      ws.onclose = () => {
        isConnected.value = false;
        stopHeartbeat();
        scheduleReconnect();
      };

      ws.onerror = () => {
        try {
          ws.close();
        } catch (_) {}
      };
    } catch {
      scheduleReconnect();
    }
  }

  function disconnect() {
    clearReconnect();
    stopHeartbeat();
    try {
      ws?.close();
    } catch (_) {}
    ws = null;
    isConnected.value = false;
  }

  return { connect, disconnect, isConnected };
}
