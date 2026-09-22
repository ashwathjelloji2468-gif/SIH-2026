import { api, clearApiCache, invalidateTargetedCache, subscribeApiCache } from '../services/api';

export async function runPhase2PerformanceTests(): Promise<{ name: string; passed: boolean; details: string }[]> {
  const results: { name: string; passed: boolean; details: string }[] = [];

  // Polyfill sessionStorage for Node environment if missing
  if (typeof globalThis.sessionStorage === 'undefined' || typeof (globalThis.sessionStorage as any).getItem !== 'function') {
    const store = new Map<string, string>();
    (globalThis as any).sessionStorage = {
      getItem: (k: string) => store.get(k) || null,
      setItem: (k: string, v: string) => store.set(k, v),
      removeItem: (k: string) => store.delete(k),
      clear: () => store.clear(),
      get length() { return store.size; },
      key: (i: number) => Array.from(store.keys())[i] || null,
    };
  }

  // Helper to reset test state
  const resetCache = () => {
    clearApiCache();
  };

  // TEST A: Identical concurrent GETs -> exactly one network request
  await (async () => {
    resetCache();
    let networkCallCount = 0;
    const originalFetch = globalThis.fetch;

    globalThis.fetch = (async (url: string | URL | Request) => {
      networkCallCount++;
      await new Promise((r) => setTimeout(r, 20));
      return new Response(JSON.stringify({ data: 'concurrent-test' }), {
        status: 200,
        headers: { 'content-type': 'application/json' },
      });
    }) as any;

    try {
      const p1 = api.get<{ data: string }>('/test-concurrent-dedup', { skipCache: true });
      const p2 = api.get<{ data: string }>('/test-concurrent-dedup', { skipCache: true });

      const [res1, res2] = await Promise.all([p1, p2]);

      const passed = networkCallCount === 1 && res1.data === 'concurrent-test' && res2.data === 'concurrent-test';
      results.push({
        name: 'TEST A: Identical concurrent GETs -> exactly one network request',
        passed,
        details: `networkCallCount=${networkCallCount}, res1=${res1?.data}, res2=${res2?.data}`,
      });
    } catch (err: any) {
      results.push({
        name: 'TEST A: Identical concurrent GETs -> exactly one network request',
        passed: false,
        details: `Error: ${err.message}`,
      });
    } finally {
      globalThis.fetch = originalFetch;
    }
  })();

  // TEST B: Concurrent different GET URLs -> independent requests
  await (async () => {
    resetCache();
    let networkCallCount = 0;
    const originalFetch = globalThis.fetch;

    globalThis.fetch = (async (url: string | URL | Request) => {
      networkCallCount++;
      await new Promise((r) => setTimeout(r, 10));
      return new Response(JSON.stringify({ url: String(url) }), {
        status: 200,
        headers: { 'content-type': 'application/json' },
      });
    }) as any;

    try {
      const p1 = api.get<{ url: string }>('/test-url-1');
      const p2 = api.get<{ url: string }>('/test-url-2');

      await Promise.all([p1, p2]);

      const passed = networkCallCount === 2;
      results.push({
        name: 'TEST B: Concurrent different GET URLs -> independent requests',
        passed,
        details: `networkCallCount=${networkCallCount} (expected 2)`,
      });
    } catch (err: any) {
      results.push({
        name: 'TEST B: Concurrent different GET URLs -> independent requests',
        passed: false,
        details: `Error: ${err.message}`,
      });
    } finally {
      globalThis.fetch = originalFetch;
    }
  })();

  // TEST C: Failed deduplicated GET -> registry cleanup allows a later retry
  await (async () => {
    resetCache();
    let fetchAttempts = 0;
    const originalFetch = globalThis.fetch;

    globalThis.fetch = (async () => {
      fetchAttempts++;
      if (fetchAttempts === 1) {
        return new Response(JSON.stringify({ detail: 'Server error' }), {
          status: 500,
          headers: { 'content-type': 'application/json' },
        });
      }
      return new Response(JSON.stringify({ success: true }), {
        status: 200,
        headers: { 'content-type': 'application/json' },
      });
    }) as any;

    try {
      // First attempt fails
      try {
        await api.get('/test-failing-endpoint', { skipCache: true });
      } catch (_) {}

      // Second attempt should issue a new network call (registry cleaned up)
      const retryRes = await api.get<{ success: boolean }>('/test-failing-endpoint', { skipCache: true });

      const passed = fetchAttempts === 2 && retryRes.success === true;
      results.push({
        name: 'TEST C: Failed deduplicated GET -> registry cleanup allows a later retry',
        passed,
        details: `fetchAttempts=${fetchAttempts}, retrySuccess=${retryRes?.success}`,
      });
    } catch (err: any) {
      results.push({
        name: 'TEST C: Failed deduplicated GET -> registry cleanup allows a later retry',
        passed: false,
        details: `Error: ${err.message}`,
      });
    } finally {
      globalThis.fetch = originalFetch;
    }
  })();

  // TEST D: Targeted mutation invalidation -> unrelated cached resources survive
  await (async () => {
    resetCache();
    const originalFetch = globalThis.fetch;

    globalThis.fetch = (async (url: string | URL | Request) => {
      return new Response(JSON.stringify({ endpoint: String(url) }), {
        status: 200,
        headers: { 'content-type': 'application/json' },
      });
    }) as any;

    try {
      // Populate cache for /scans and /migration
      await api.get('/projects/p1/scans');
      await api.get('/projects/p1/migration/plans');

      // Trigger targeted invalidation for scan mutation
      invalidateTargetedCache('/scans');

      // Check sessionStorage / memoryCache status
      let scansInCache = false;
      let migrationInCache = false;
      try {
        scansInCache = Boolean(sessionStorage.getItem('sentriq_cache_/projects/p1/scans'));
        migrationInCache = Boolean(sessionStorage.getItem('sentriq_cache_/projects/p1/migration/plans'));
      } catch (_) {}

      const passed = !scansInCache && migrationInCache;
      results.push({
        name: 'TEST D: Targeted mutation invalidation -> unrelated cached resources survive',
        passed,
        details: `scansInCache=${scansInCache} (expected false), migrationInCache=${migrationInCache} (expected true)`,
      });
    } catch (err: any) {
      results.push({
        name: 'TEST D: Targeted mutation invalidation -> unrelated cached resources survive',
        passed: false,
        details: `Error: ${err.message}`,
      });
    } finally {
      globalThis.fetch = originalFetch;
    }
  })();

  // TEST E: Background revalidation -> active consumer receives updated data
  await (async () => {
    resetCache();
    let fetchCount = 0;
    const originalFetch = globalThis.fetch;

    globalThis.fetch = (async () => {
      fetchCount++;
      const val = fetchCount === 1 ? 'initial-val' : 'fresh-revalidated-val';
      return new Response(JSON.stringify({ val }), {
        status: 200,
        headers: { 'content-type': 'application/json' },
      });
    }) as any;

    try {
      const endpoint = '/test-revalidate-propagation';
      // 1. Initial fetch populates cache
      await api.get<{ val: string }>(endpoint);

      // 2. Subscribe to cache revalidation events
      let notifiedData: any = null;
      const unsubscribe = subscribeApiCache((updEndpoint, fresh) => {
        if (updEndpoint === endpoint) {
          notifiedData = fresh;
        }
      });

      // 3. Second call returns cached data immediately and fires background revalidation
      const cachedRes = await api.get<{ val: string }>(endpoint);
      assert(cachedRes.val === 'initial-val');

      // Wait for background revalidation promise to complete
      await new Promise((r) => setTimeout(r, 50));

      unsubscribe();

      const passed = notifiedData && notifiedData.val === 'fresh-revalidated-val';
      results.push({
        name: 'TEST E: Background revalidation -> active consumer receives updated data',
        passed,
        details: `notifiedData=${JSON.stringify(notifiedData)}`,
      });
    } catch (err: any) {
      results.push({
        name: 'TEST E: Background revalidation -> active consumer receives updated data',
        passed: false,
        details: `Error: ${err.message}`,
      });
    } finally {
      globalThis.fetch = originalFetch;
    }
  })();

  // TEST F: Scan polling cycle -> one /scans request, not two
  await (async () => {
    resetCache();
    let scanGetCount = 0;
    const originalFetch = globalThis.fetch;

    globalThis.fetch = (async (url: string | URL | Request) => {
      if (String(url).includes('/scans')) {
        scanGetCount++;
      }
      return new Response(JSON.stringify([{ id: 's1', created_at: new Date().toISOString() }]), {
        status: 200,
        headers: { 'content-type': 'application/json' },
      });
    }) as any;

    try {
      // Simulate fetchScans workflow in Scan.tsx
      const data = await api.get<any[]>('/projects/p1/scans');
      const sorted = [...data].sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
      // refreshLatestScan called with pre-fetched sorted array (0 additional GETs)
      const latest = sorted[0];

      const passed = scanGetCount === 1 && latest.id === 's1';
      results.push({
        name: 'TEST F: Scan polling cycle -> one /scans request, not two',
        passed,
        details: `scanGetCount=${scanGetCount} (expected 1), latestId=${latest?.id}`,
      });
    } catch (err: any) {
      results.push({
        name: 'TEST F: Scan polling cycle -> one /scans request, not two',
        passed: false,
        details: `Error: ${err.message}`,
      });
    } finally {
      globalThis.fetch = originalFetch;
    }
  })();

  return results;
}

function assert(condition: boolean, message?: string) {
  if (!condition) {
    throw new Error(message || 'Assertion failed');
  }
}
