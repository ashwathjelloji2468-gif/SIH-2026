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

// In-Flight GET Request Deduplication Registry
const inFlightGetRequests = new Map<string, Promise<any>>();

// Cache Revalidation Subscribers
type CacheSubscriber = (endpoint: string, freshData: any) => void;
const cacheSubscribers = new Set<CacheSubscriber>();

export function subscribeApiCache(subscriber: CacheSubscriber): () => void {
  cacheSubscribers.add(subscriber);
  return () => {
    cacheSubscribers.delete(subscriber);
  };
}

function notifySubscribers(endpoint: string, freshData: any): void {
  cacheSubscribers.forEach((sub) => {
    try {
      sub(endpoint, freshData);
    } catch (_) {}
  });
}

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
      if (typeof sessionStorage !== 'undefined') {
        const keysToRemove: string[] = [];
        for (let i = 0; i < sessionStorage.length; i++) {
          const k = sessionStorage.key(i);
          if (k && k.startsWith('sentriq_cache_')) keysToRemove.push(k);
        }
        keysToRemove.forEach((k) => sessionStorage.removeItem(k));
      }
    } catch (_) {}
    return;
  }

  const prefixKey = getCacheKey(endpointPrefix);
  memoryCache.forEach((_, k) => {
    if (k.includes(endpointPrefix)) memoryCache.delete(k);
  });
  try {
    if (typeof sessionStorage !== 'undefined') {
      const keysToRemove: string[] = [];
      for (let i = 0; i < sessionStorage.length; i++) {
        const k = sessionStorage.key(i);
        if (k && k.includes(endpointPrefix)) keysToRemove.push(k);
      }
      keysToRemove.forEach((k) => sessionStorage.removeItem(k));
    }
  } catch (_) {}
}

export function invalidateTargetedCache(endpoint: string): void {
  const lower = endpoint.toLowerCase();
  if (lower.includes('/scans')) {
    clearApiCache('/scans');
  } else if (lower.includes('/risk')) {
    clearApiCache('/risk');
  } else if (lower.includes('/migration')) {
    clearApiCache('/migration');
  } else if (lower.includes('/qars')) {
    clearApiCache('/qars');
  } else if (lower.includes('/assets') || lower.includes('/inventory')) {
    clearApiCache('/inventory');
    clearApiCache('/coverage');
    clearApiCache('/unknowns');
    clearApiCache('/assets');
  } else if (lower.includes('/projects')) {
    clearApiCache('/projects');
  } else {
    clearApiCache(endpoint.split('?')[0]);
  }
}

async function request<T>(endpoint: string, options: RequestInit & { timeoutMs?: number } = {}, defaultTimeout = 60000): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  const effectiveTimeout = options.timeoutMs || defaultTimeout;
  
  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  headers.set('Accept', 'application/json');

  const controller = new AbortController();
  if (options.signal) {
    if (options.signal.aborted) {
      controller.abort();
    } else {
      options.signal.addEventListener('abort', () => controller.abort(), { once: true });
    }
  }
  const timeoutId = setTimeout(() => controller.abort(), effectiveTimeout);

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

export type ApiRequestOptions = RequestInit & { skipCache?: boolean; timeoutMs?: number };

export const api = {
  /**
   * Fast SWR GET Request with in-flight deduplication:
   * Returns cached snapshot immediately if available (0ms delay),
   * while revalidating in background.
   */
  get: async <T>(endpoint: string, options?: ApiRequestOptions): Promise<T> => {
    const skipCache = (options as any)?.skipCache;
    
    if (!skipCache) {
      const cached = readCache<T>(endpoint);
      if (cached) {
        if (!inFlightGetRequests.has(endpoint)) {
          const revalPromise = request<T>(endpoint, { ...options, method: 'GET' })
            .then((fresh) => {
              writeCache(endpoint, fresh);
              notifySubscribers(endpoint, fresh);
              return fresh;
            })
            .catch(() => {})
            .finally(() => {
              inFlightGetRequests.delete(endpoint);
            });
          inFlightGetRequests.set(endpoint, revalPromise);
        }
        return cached;
      }
    } else {
      clearApiCache(endpoint);
    }

    if (inFlightGetRequests.has(endpoint)) {
      return inFlightGetRequests.get(endpoint) as Promise<T>;
    }

    const fetchPromise = (async () => {
      try {
        const fresh = await request<T>(endpoint, { ...options, method: 'GET' });
        writeCache(endpoint, fresh);
        notifySubscribers(endpoint, fresh);
        return fresh;
      } catch (err) {
        const staleKey = getCacheKey(endpoint);
        const stale = memoryCache.get(staleKey);
        if (stale) return stale.data as T;
        throw err;
      }
    })();

    inFlightGetRequests.set(endpoint, fetchPromise);
    try {
      return await fetchPromise;
    } finally {
      inFlightGetRequests.delete(endpoint);
    }
  },

  post: async <T>(endpoint: string, body?: any, options?: ApiRequestOptions): Promise<T> => {
    invalidateTargetedCache(endpoint);
    return request<T>(endpoint, { 
      ...options, 
      method: 'POST', 
      body: body ? JSON.stringify(body) : undefined 
    });
  },

  patch: async <T>(endpoint: string, body?: any, options?: ApiRequestOptions): Promise<T> => {
    invalidateTargetedCache(endpoint);
    return request<T>(endpoint, { 
      ...options, 
      method: 'PATCH', 
      body: body ? JSON.stringify(body) : undefined 
    });
  },

  put: async <T>(endpoint: string, body?: any, options?: ApiRequestOptions): Promise<T> => {
    invalidateTargetedCache(endpoint);
    return request<T>(endpoint, { 
      ...options, 
      method: 'PUT', 
      body: body ? JSON.stringify(body) : undefined 
    });
  },

  delete: async <T>(endpoint: string, options?: ApiRequestOptions): Promise<T> => {
    invalidateTargetedCache(endpoint);
    return request<T>(endpoint, { ...options, method: 'DELETE' });
  },

  getBaseUrl: (): string => BASE_URL,
};
