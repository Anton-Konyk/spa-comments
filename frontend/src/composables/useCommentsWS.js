import { ref } from 'vue';
import client from '@/utils/client.js';

/**
 * Priority of choice WS URL:
 * 1) parameter wsUrl, transmitted in useCommentsWS({ wsUrl })
 * 2) VITE_WS_URL (full ws:// или wss://)
 * 3) client.defaults.baseURL + VITE_WS_PATH  (http->ws, https->wss)
 * 4) window.location.host + VITE_WS_PATH
 */
function resolveWsUrl(overrideUrl) {
  if (overrideUrl && overrideUrl.trim()) return overrideUrl.trim();

  const envWs = (import.meta.env.VITE_WS_URL || '').trim();
  if (envWs) return envWs;

  const wsPath = normalizePath(import.meta.env.VITE_WS_PATH || '/ws/comments/');

  const axiosBase = (client.defaults.baseURL || '').trim();
  if (axiosBase) {
    try {
      return buildWsUrlFromBase(axiosBase, wsPath);
    } catch {
      // fallthrough
    }
  }

  if (typeof window !== 'undefined' && window.location) {
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
    return `${proto}://${window.location.host}${wsPath}`;
  }

  throw new Error(
    'WS URL cannot be resolved. Pass wsUrl, or set VITE_WS_URL, or set client baseURL + VITE_WS_PATH.'
  );
}

function normalizePath(p) {
  if (!p) return '/';
  return p.startsWith('/') ? p : `/${p}`;
}

function buildWsUrlFromBase(baseUrl, path) {
  const u = new URL(baseUrl);
  u.protocol = u.protocol === 'https:' ? 'wss:' : 'ws:';
  // origin: protocol+host(+port)
  const origin = u.origin.replace(/\/+$/, '');
  return `${origin}${path}`;
}

export function useCommentsWS({ onEvent, wsUrl } = {}) {
  const isConnected = ref(false);
  let ws = null;
  let heartbeatTimer = null;
  let reconnectTimer = null;
  let reconnectAttempts = 0;

  const WS_URL = resolveWsUrl(wsUrl);

  function startHeartbeat() {
    stopHeartbeat();
    const interval = Number(import.meta.env.VITE_WS_HEARTBEAT_MS || 20000);
    heartbeatTimer = setInterval(() => {
      try {
        if (ws?.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ ping: Date.now() }));
        }
      } catch (_) {}
    }, interval);
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
