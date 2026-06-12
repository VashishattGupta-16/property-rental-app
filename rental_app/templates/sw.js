// ============================================================
// RentalPro Service Worker — PRODUCTION-READY
// Key fix: Authentication and API routes are NEVER intercepted.
// This prevents session state from being overwritten by duplicate
// requests, which is the root cause of PWA Google OAuth login failures.
// ============================================================

const CACHE_NAME = "rentalpro-v2";
const OFFLINE_URL = "/offline/";

// ─── 1. STATIC ASSETS TO CACHE ON INSTALL ───────────────────
const PRECACHE_ASSETS = [
  "/offline/",
  "/static/images/icon-192x192.png",
  "/static/images/icon-512x512.png",
];

// ─── 2. ROUTES THAT MUST NEVER BE INTERCEPTED ────────────────
// Any path starting with these will go straight to the network,
// ensuring cookie and session integrity.
const BYPASS_PREFIXES = [
  "/accounts/",     // Google OAuth, login, logout, signup
  "/admin/",        // Django admin
  "/api/",          // REST API endpoints
  "/wishlist/",     // Wishlist toggle actions
  "/terms/accept/", // Terms acceptance
];

// ─── 3. FILE EXTENSIONS THAT SHOULD NEVER BE CACHED ──────────
const NO_CACHE_EXTENSIONS = [
  ".json", // manifest.json can change
];

// ─── 4. HELPERS ──────────────────────────────────────────────

/**
 * Returns true if the request URL should bypass the SW entirely.
 * These requests go straight to the network — no caching,
 * no interception, no duplicate fetches.
 */
function shouldBypass(request) {
  // Let non-GET requests (POST, etc.) pass through.
  if (request.method !== "GET") return true;

  const url = new URL(request.url);

  // Skip non-same-origin requests (Google, CDN, Cloudinary etc.)
  if (url.origin !== self.location.origin) return true;

  const path = url.pathname;

  // CRITICAL: Skip auth/admin/api routes for session integrity.
  if (BYPASS_PREFIXES.some((prefix) => path.startsWith(prefix))) return true;

  // Skip file types that should not be cached.
  if (NO_CACHE_EXTENSIONS.some((ext) => path.endsWith(ext))) return true;

  return false;
}

/**
 * Returns true if the response is worth caching.
 */
function isCacheableResponse(response) {
  return (
    response && response.status === 200 && response.type === "basic" // same-origin only
  );
}

// ─── 5. EVENT LISTENERS ──────────────────────────────────────

// INSTALL: Pre-cache essential offline assets.
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

// ACTIVATE: Delete old caches and take control.
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

// FETCH: The main interception logic.

self.addEventListener("fetch", (event) => {
  const { request } = event;

  // --- Bypass Strategy ---
  // If shouldBypass is true, we don't call event.respondWith().
  // This lets the browser handle the request natively, without any
  // SW interference, which is CRITICAL for OAuth redirects.
  if (shouldBypass(request)) {
    return; // Let the browser handle it.
  }

  const url = new URL(request.url);
  const isNavigationRequest = request.mode === "navigate";
  const isStaticAsset = url.pathname.startsWith("/static/");

  if (isStaticAsset) {
    // --- Strategy: Cache-First for Static Assets ---
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
    // --- Strategy: Network-First for Pages ---
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
    // --- Strategy: Network-First for other assets (e.g., API calls not bypassed) ---
    event.respondWith(
      fetch(request).catch(
        () => caches.match(request) // serve from cache if offline
      )
    );
  }
});