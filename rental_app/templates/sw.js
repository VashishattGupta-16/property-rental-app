const CACHE_NAME = 'Empire-cache-v7';
const urlsToCache = [
  '/static/dist/output.css',
  '/static/images/icon-192x192.png',
  '/static/images/icon-512x512.png',
  '/manifest.json?v=4',
  '/offline/',
];

self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    if (self.registration.navigationPreload) {
      await self.registration.navigationPreload.enable();
    }
    const keys = await caches.keys();
    await Promise.all(keys.map(key => (key === CACHE_NAME ? null : caches.delete(key))));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', event => {
  if (
    event.request.method !== 'GET' || 
    event.request.headers.has('HX-Request')
  ) return;

  const url = new URL(event.request.url);
  if (url.pathname.includes('/accounts/') || url.pathname.includes('/admin/')) return;

  // Navigation: Network-Only with Offline Fallback.
  // We NEVER cache dynamic HTML to avoid stale CSRF tokens and layout nesting.
  if (event.request.mode === 'navigate') {
    event.respondWith((async () => {
      try {
        const preloadResponse = await event.preloadResponse;
        if (preloadResponse) return preloadResponse;

        return await fetch(event.request);
      } catch (error) {
        const offline = await caches.match('/offline/');
        return offline || new Response('Offline', { status: 503, headers: { 'Content-Type': 'text/html' } });
      }
    })());
    return;
  }

  // Static Assets: Cache-First
  event.respondWith(
    caches.match(event.request).then(async (cached) => {
      if (cached) return cached;
      try {
        const response = await fetch(event.request);
        if (response.ok && url.origin === self.location.origin && url.pathname.startsWith('/static/')) {
          const cache = await caches.open(CACHE_NAME);
          cache.put(event.request, response.clone());
        }
        return response;
      } catch (e) {
        return new Response('Network error', { status: 408 });
      }
    })
  );
});
