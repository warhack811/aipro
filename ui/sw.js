// =============================================================================
// Service Worker - Network First Strategy
// Cache Version: ui_v18 (Image pending card improvements)
// =============================================================================
const CACHE_NAME = 'mami-ai-ui_v18';

// Install: Pre-cache critical resources
self.addEventListener('install', event => {
  console.log('[SW] Installing ui_v18...');
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll([
        '/ui/chat.html',
        '/ui/css/main.css?v=ui_v18',
        '/ui/css/modern.css?v=ui_v18',
        '/ui/js/main.js?v=ui_v18'
      ]);
    }).then(() => self.skipWaiting()) // Force activation
  );
});

// Activate: Clean old caches
self.addEventListener('activate', event => {
  console.log('[SW] Activating ui_v16...');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.filter(name => name !== CACHE_NAME).map(name => {
          console.log('[SW] Deleting old cache:', name);
          return caches.delete(name);
        })
      );
    }).then(() => self.clients.claim()) // Take control immediately
  );
});

// Fetch: Network-First Strategy (always try network first)
self.addEventListener('fetch', event => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') return;

  // Skip API and WebSocket requests
  const url = new URL(event.request.url);
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/ws')) return;

  event.respondWith(
    fetch(event.request)
      .then(response => {
        // Cache successful responses
        if (response.ok) {
          const clonedResponse = response.clone();
          caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, clonedResponse);
          });
        }
        return response;
      })
      .catch(() => {
        // Fallback to cache on network failure
        return caches.match(event.request);
      })
  );
});