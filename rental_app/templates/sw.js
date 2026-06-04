// ============================================================
// RentalPro Service Worker — FIXED
// Key fix: Auth routes (/accounts/, /admin/, /api/) are NEVER
// intercepted or cached. They go straight to the network.
// This prevents session state from being overwritten by duplicate
// requests, which broke Google OAuth login.
// ============================================================

const CACHE_NAME = "rentalpro-v2";
const OFFLINE_URL = "/offline/";

// ─── STATIC ASSETS TO CACHE ON INSTALL ───────────────────────
const PRECACHE_ASSETS = [
  "/offline/",
  "/static/images/icon-192x192.png",
  "/static/images/icon-512x512.png",
];

// ─── ROUTES THAT MUST NEVER BE INTERCEPTED ───────────────────
// Any path starting with these will go straight to the network.
// CRITICAL: /accounts/ must be here — OAuth state lives in the
// Django session. If the SW intercepts or duplicates these
// requests, the session is overwritten and login fails.
const BYPASS_PREFIXES = [
  "/accounts/",   // ← Google OAuth, login, logout, signup
  "/admin/",      // ← Django admin
  "/api/",        // ← REST API
];

// ─── FILE EXTENSIONS THAT SHOULD NEVER BE CACHED ─────────────
const NO_CACHE_EXTENSIONS = [
  ".json",        // manifest.json can change; don't cache
];

// ─── HELPERS ──────────────────────────────────────────────────

/**
 * Returns true if the request URL should bypass the SW entirely.
 * These requests go straight to the network — no caching,
 * no interception, no duplicate fetches.
 */
function shouldBypass(request) {
  // Only handle GET — let POST/PUT/DELETE etc. pass through
  if (request.method !== "GET") return true;

  const url = new URL(request.url);

  // Skip non-same-origin requests (Google, CDN, Cloudinary etc.)
  if (url.origin !== self.location.origin) return true;

  const path = url.pathname;

  // Skip auth/admin/api routes — CRITICAL for OAuth session integrity
  if (BYPASS_PREFIXES.some((prefix) => path.startsWith(prefix))) return true;

  // Skip file types we never want to cache
  if (NO_CACHE_EXTENSIONS.some((ext) => path.endsWith(ext))) return true;

  return false;
}

/**
 * Returns true if the response is worth caching.
 */
function isCacheableResponse(response) {
  return (
    response &&
    response.status === 200 &&
    response.type === "basic" // same-origin only
  );
}

// ─── INSTALL ──────────────────────────────────────────────────
// Pre-cache essential offline assets.
// skipWaiting() activates the new SW immediately on page reload.

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE_ASSETS))
      .then(() => self.skipWaiting())
  );
});

// ─── ACTIVATE ─────────────────────────────────────────────────
// Delete old caches from previous SW versions.
// clients.claim() takes control of open pages immediately.

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((cacheNames) =>
        Promise.all(
          cacheNames
            .filter((name) => name !== CACHE_NAME)
            .map((name) => {
              console.log("[SW] Deleting old cache:", name);
              return caches.delete(name);
            })
        )
      )
      .then(() => self.clients.claim())
  );
});

// ─── FETCH ────────────────────────────────────────────────────
// Strategy:
//   • Bypass routes  → straight to network, no caching
//   • Static assets  → cache-first, fallback to network
//   • Pages          → network-first, fallback to cache, then offline

self.addEventListener("fetch", (event) => {
  const { request } = event;

  // ── Bypass: go straight to network, don't even call respondWith ──
  // Not calling event.respondWith() lets the browser handle it natively.
  // This is important — calling fetch() inside respondWith for auth
  // routes was causing the duplicate requests that broke OAuth.
  if (shouldBypass(request)) {
    return; // ← browser handles it directly, no SW involvement
  }

  const url = new URL(request.url);
  const isNavigationRequest = request.mode === "navigate";
  const isStaticAsset = url.pathname.startsWith("/static/");

  if (isStaticAsset) {
    // ── Static assets: cache-first ──────────────────────────────
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached;

        return fetch(request).then((response) => {
          if (isCacheableResponse(response)) {
            const responseClone = response.clone();
            caches
              .open(CACHE_NAME)
              .then((cache) => cache.put(request, responseClone));
          }
          return response;
        });
      })
    );
  } else if (isNavigationRequest) {
    // ── Page navigations: network-first ─────────────────────────
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (isCacheableResponse(response)) {
            const responseClone = response.clone();
            caches
              .open(CACHE_NAME)
              .then((cache) => cache.put(request, responseClone));
          }
          return response;
        })
        .catch(() =>
          // Network failed → try cache → fall back to offline page
          caches
            .match(request)
            .then((cached) => cached || caches.match(OFFLINE_URL))
        )
    );
  } else {
    // ── Everything else: network-first, no caching ───────────────
    event.respondWith(
      fetch(request).catch(
        () => caches.match(request) // serve from cache if offline
      )
    );
  }
});