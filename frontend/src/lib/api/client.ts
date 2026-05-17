import { browser } from '$app/environment';
import type { Dict, StoredSession, TokenPair, User } from './types';

const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) || '/api/v1';
const SESSION_KEY = 'cleanplates.session';

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

type QueryValue = string | number | boolean | Date | null | undefined;
type RequestOptions = Omit<RequestInit, 'body'> & {
  query?: Record<string, QueryValue>;
  body?: unknown;
  skipAuth?: boolean;
  retryOnUnauthorized?: boolean;
};

function storageCandidates(): Storage[] {
  if (!browser) return [];
  return [window.localStorage, window.sessionStorage];
}

function emitSessionChange() {
  if (browser)
    window.dispatchEvent(new CustomEvent('cleanplates:session-change'));
}

export function readStoredSession(): StoredSession | null {
  for (const storage of storageCandidates()) {
    const raw = storage.getItem(SESSION_KEY);
    if (!raw) continue;
    try {
      return JSON.parse(raw) as StoredSession;
    } catch {
      storage.removeItem(SESSION_KEY);
    }
  }
  return null;
}

export function persistSession(
  tokens: TokenPair,
  user: User,
  remember: boolean
) {
  if (!browser) return;
  const payload: StoredSession = {
    tokens,
    user,
    remember,
    savedAt: Date.now()
  };
  const target = remember ? window.localStorage : window.sessionStorage;
  const other = remember ? window.sessionStorage : window.localStorage;
  target.setItem(SESSION_KEY, JSON.stringify(payload));
  other.removeItem(SESSION_KEY);
  emitSessionChange();
}

export function updateStoredUser(user: User) {
  const session = readStoredSession();
  if (!session) return;
  persistSession(session.tokens, user, session.remember);
}

export function clearStoredSession() {
  for (const storage of storageCandidates()) storage.removeItem(SESSION_KEY);
  emitSessionChange();
}

export function getAccessToken(): string | null {
  return readStoredSession()?.tokens.access_token ?? null;
}

function buildUrl(path: string, query?: Record<string, QueryValue>) {
  const base = path.startsWith('http')
    ? path
    : `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
  const url = new URL(
    base,
    browser ? window.location.origin : 'http://localhost'
  );
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value === null || value === undefined || value === '') continue;
    url.searchParams.set(
      key,
      value instanceof Date ? value.toISOString() : String(value)
    );
  }
  return url.toString();
}

function bodyPayload(body: unknown): BodyInit | undefined {
  if (body === undefined || body === null) return undefined;
  if (
    body instanceof FormData ||
    body instanceof Blob ||
    typeof body === 'string'
  )
    return body;
  return JSON.stringify(body);
}

function contentHeaders(body: unknown): Dict<string> {
  if (
    body === undefined ||
    body === null ||
    body instanceof FormData ||
    body instanceof Blob
  )
    return {};
  return { 'Content-Type': 'application/json' };
}

async function parseResponse(response: Response) {
  if (response.status === 204) return null;
  const type = response.headers.get('content-type') ?? '';
  if (type.includes('application/json')) return response.json();
  return response.text();
}

async function refreshStoredSession(): Promise<boolean> {
  const session = readStoredSession();
  if (!session?.tokens.refresh_token) return false;
  const response = await fetch(buildUrl('/auth/refresh'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: session.tokens.refresh_token })
  });
  if (!response.ok) {
    clearStoredSession();
    return false;
  }
  const tokens = (await response.json()) as TokenPair;
  persistSession(tokens, session.user, session.remember);
  return true;
}

async function request<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const {
    query,
    body,
    skipAuth = false,
    retryOnUnauthorized = true,
    headers: incomingHeaders,
    ...rest
  } = options;
  const headers = new Headers(incomingHeaders);
  for (const [key, value] of Object.entries(contentHeaders(body)))
    headers.set(key, value);

  const token = getAccessToken();
  if (!skipAuth && token) headers.set('Authorization', `Bearer ${token}`);

  const response = await fetch(buildUrl(path, query), {
    ...rest,
    method: rest.method ?? (body === undefined ? 'GET' : 'POST'),
    headers,
    body: bodyPayload(body)
  });

  if (response.status === 401 && !skipAuth && retryOnUnauthorized) {
    const refreshed = await refreshStoredSession();
    if (refreshed)
      return request<T>(path, { ...options, retryOnUnauthorized: false });
  }

  const parsed = await parseResponse(response);
  if (!response.ok) {
    const detail =
      typeof parsed === 'object' && parsed !== null && 'detail' in parsed
        ? (parsed as Dict).detail
        : parsed;
    const message =
      typeof detail === 'string'
        ? detail
        : `Request failed with status ${response.status}`;
    throw new ApiError(response.status, message, parsed);
  }

  return parsed as T;
}

export const api = {
  get: <T>(
    path: string,
    query?: Record<string, QueryValue>,
    options?: RequestOptions
  ) => request<T>(path, { ...options, query, method: 'GET' }),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, body, method: 'POST' }),
  patch: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, body, method: 'PATCH' }),
  put: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, body, method: 'PUT' }),
  delete: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'DELETE' }),
  upload: <T>(
    path: string,
    fieldName: string,
    file: File,
    extra?: Record<string, string>
  ) => {
    const form = new FormData();
    form.set(fieldName, file);
    for (const [key, value] of Object.entries(extra ?? {}))
      form.set(key, value);
    return request<T>(path, { body: form, method: 'POST' });
  },
  async download(
    path: string,
    filename: string,
    query?: Record<string, QueryValue>
  ) {
    const doFetch = (token: string | null) => {
      const headers = new Headers();
      if (token) headers.set('Authorization', `Bearer ${token}`);
      return fetch(buildUrl(path, query), { headers });
    };

    let response = await doFetch(getAccessToken());

    if (response.status === 401) {
      const refreshed = await refreshStoredSession();
      if (refreshed) response = await doFetch(getAccessToken());
    }

    if (!response.ok) {
      const parsed = await parseResponse(response);
      const message =
        typeof parsed === 'object' && parsed !== null && 'detail' in parsed
          ? String((parsed as Dict).detail)
          : `Download failed with status ${response.status}`;
      throw new ApiError(response.status, message, parsed);
    }
    const blob = await response.blob();
    const disposition = response.headers.get('content-disposition') ?? '';
    const match = disposition.match(/filename="?([^"]+)"?/i);
    saveBlob(blob, match?.[1] ?? filename);
  }
};

export function saveBlob(blob: Blob, filename: string) {
  if (!browser) return;
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
