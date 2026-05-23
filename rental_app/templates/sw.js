const CACHE_NAME = 'Empire-cache-v2';
const urlsToCache = [
  '/',
  '/static/dist/output.css',
  '/static/images/icon-192x192.png',
  '/static/images/icon-512x512.png',
  '/manifest.json?v=2',
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
    const keys = await caches.keys();
    await Promise.all(keys.map(key => (key === CACHE_NAME ? null : caches.delete(key))));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        return response || fetch(event.request);
      }).catch(() => {
        // Optional: Return a specific offline HTML page here if you build one
        if (event.request.mode === 'navigate') {
          return caches.match('/offline/');
        }
        return caches.match('/');
      })
  );
});
