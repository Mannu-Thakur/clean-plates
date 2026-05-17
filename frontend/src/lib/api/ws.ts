import { browser } from '$app/environment';
import { getAccessToken } from './client';

type WsHandler = (message: Record<string, unknown>) => void;

const WS_BASE_URL =
  (import.meta.env.VITE_WS_BASE_URL as string | undefined) || '/ws';

function wsUrl(path: string) {
  if (!browser) return '';
  const token = getAccessToken();
  const base = path.startsWith('ws')
    ? path
    : `${WS_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
  const url = new URL(base, window.location.origin);
  url.protocol = url.protocol.replace('http', 'ws');
  if (token) url.searchParams.set('token', token);
  return url.toString();
}

export class ReconnectingSocket {
  private socket: WebSocket | null = null;
  private path: string;
  private handler: WsHandler;
  private statusHandler?: (status: string) => void;
  private reconnectTimer: number | null = null;
  private closed = false;
  private attempt = 0;

  constructor(
    path: string,
    handler: WsHandler,
    statusHandler?: (status: string) => void
  ) {
    this.path = path;
    this.handler = handler;
    this.statusHandler = statusHandler;
  }

  connect() {
    if (!browser || this.closed) return;
    this.statusHandler?.('connecting');
    this.socket = new WebSocket(wsUrl(this.path));
    this.socket.onopen = () => {
      this.attempt = 0;
      this.statusHandler?.('connected');
    };
    this.socket.onmessage = (event) => {
      try {
        this.handler(JSON.parse(event.data) as Record<string, unknown>);
      } catch {
        this.handler({ type: 'malformed', raw: event.data });
      }
    };
    this.socket.onerror = () => this.statusHandler?.('error');
    this.socket.onclose = () => {
      if (this.closed) {
        this.statusHandler?.('closed');
        return;
      }
      this.statusHandler?.('reconnecting');
      const delay = Math.min(15000, 1000 * 2 ** this.attempt);
      this.attempt += 1;
      this.reconnectTimer = window.setTimeout(() => this.connect(), delay);
    };
  }

  send(payload: Record<string, unknown>) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(payload));
    }
  }

  pause() {
    this.send({ type: 'pause' });
  }

  resume() {
    this.send({ type: 'resume' });
  }

  filter(filters: Record<string, unknown>) {
    this.send({ type: 'filter', filters });
  }

  close() {
    this.closed = true;
    if (this.reconnectTimer !== null && browser)
      window.clearTimeout(this.reconnectTimer);
    this.socket?.close();
  }
}
