const getBaseUrl = () => {
  let envUrl = import.meta.env.VITE_API_URL || '';
  if (!envUrl) return '/api/v1';
  envUrl = envUrl.replace(/\/+$/, '');
  if (envUrl.endsWith('/api/v1')) return envUrl;
  return `${envUrl}/api/v1`;
};

const BASE_URL = getBaseUrl();

// Immediate fire-and-forget warmup ping to wake up Render backend instance
try {
  fetch(`${BASE_URL}/health`, { method: 'GET', mode: 'cors' }).catch(() => {});
} catch (_) {}

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

// In-Memory & SessionStorage SWR Cache Layer for Sub-100ms Perceived Speed
const memoryCache = new Map<string, { data: any; timestamp: number }>();
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes TTL

function getCacheKey(endpoint: string): string {
  return `sentriq_cache_${endpoint}`;
}

function readCache<T>(endpoint: string): T | null {
  const key = getCacheKey(endpoint);
  
  // 1. Check memory cache first
  const mem = memoryCache.get(key);
  if (mem && Date.now() - mem.timestamp < CACHE_TTL_MS) {
    return mem.data as T;
  }

  // 2. Check sessionStorage
  try {
    const raw = sessionStorage.getItem(key);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Date.now() - parsed.timestamp < CACHE_TTL_MS) {
        memoryCache.set(key, parsed);
        return parsed.data as T;
      }
    }
  } catch (_) {}

  return null;
}

function writeCache(endpoint: string, data: any): void {
  if (!data) return;
  const key = getCacheKey(endpoint);
  const entry = { data, timestamp: Date.now() };
  memoryCache.set(key, entry);
  try {
    sessionStorage.setItem(key, JSON.stringify(entry));
  } catch (_) {}
}

export function clearApiCache(endpointPrefix?: string): void {
  if (!endpointPrefix) {
    memoryCache.clear();
    try {
      Object.keys(sessionStorage).forEach((k) => {
        if (k.startsWith('sentriq_cache_')) sessionStorage.removeItem(k);
      });
    } catch (_) {}
    return;
  }

  const prefixKey = getCacheKey(endpointPrefix);
  memoryCache.forEach((_, k) => {
    if (k.includes(endpointPrefix)) memoryCache.delete(k);
  });
  try {
    Object.keys(sessionStorage).forEach((k) => {
      if (k.includes(endpointPrefix)) sessionStorage.removeItem(k);
    });
  } catch (_) {}
}

async function request<T>(endpoint: string, options: RequestInit = {}, timeoutMs = 4000): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  
  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  headers.set('Accept', 'application/json');

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const config: RequestInit = {
    ...options,
    headers,
    signal: controller.signal,
  };

  try {
    const response = await fetch(url, config);
    clearTimeout(timeoutId);

    if (response.status === 204) {
      return null as unknown as T;
    }

    const contentType = response.headers.get('content-type');
    let data: any = null;
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    if (!response.ok) {
      const errorMessage = (data && data.detail) 
        ? (typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail))
        : `API request failed with status ${response.status}: ${response.statusText}`;
      throw new ApiError(errorMessage, response.status, data);
    }

    return data as T;
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err instanceof ApiError) {
      throw err;
    }
    if (err.name === 'AbortError') {
      throw new ApiError('Request timed out while connecting to backend', 408);
    }
    throw new ApiError(err.message || 'Network request failed', 0, err);
  }
}

export const api = {
  /**
   * Fast SWR GET Request:
   * Returns cached snapshot immediately if available (0ms delay),
   * while revalidating in background.
   */
  get: async <T>(endpoint: string, options?: RequestInit): Promise<T> => {
    const cached = readCache<T>(endpoint);
    
    // If cached response exists, return instantly while triggering background update
    if (cached) {
      // Background revalidation
      request<T>(endpoint, { ...options, method: 'GET' })
        .then((fresh) => writeCache(endpoint, fresh))
        .catch(() => {});
      return cached;
    }

    // No cache: perform fast fetch with fallback handling
    try {
      const fresh = await request<T>(endpoint, { ...options, method: 'GET' }, 3500);
      writeCache(endpoint, fresh);
      return fresh;
    } catch (err) {
      // If network fails or times out, check if any stale cache exists as last resort
      const staleKey = getCacheKey(endpoint);
      const stale = memoryCache.get(staleKey);
      if (stale) return stale.data as T;
      throw err;
    }
  },

  post: async <T>(endpoint: string, body?: any, options?: RequestInit): Promise<T> => {
    clearApiCache();
    return request<T>(endpoint, { 
      ...options, 
      method: 'POST', 
      body: body ? JSON.stringify(body) : undefined 
    });
  },

  patch: async <T>(endpoint: string, body?: any, options?: RequestInit): Promise<T> => {
    clearApiCache();
    return request<T>(endpoint, { 
      ...options, 
      method: 'PATCH', 
      body: body ? JSON.stringify(body) : undefined 
    });
  },

  delete: async <T>(endpoint: string, options?: RequestInit): Promise<T> => {
    clearApiCache();
    return request<T>(endpoint, { ...options, method: 'DELETE' });
  },
};
