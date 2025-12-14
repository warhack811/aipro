// Mami AI - Service Worker
// Provides offline support and caching

const CACHE_NAME = 'mami-ai-v1';
const STATIC_ASSETS = [
    '/new-ui/',
    '/new-ui/index.html',
    '/new-ui/manifest.json',
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('[SW] Installing service worker...');
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('[SW] Caching static assets');
            return cache.addAll(STATIC_ASSETS);
        })
    );
    self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating service worker...');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== CACHE_NAME)
                    .map((name) => {
                        console.log('[SW] Deleting old cache:', name);
                        return caches.delete(name);
                    })
            );
        })
    );
    self.clients.claim();
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') return;

    // Skip API calls - always go to network
    if (url.pathname.startsWith('/api/')) return;

    // Skip WebSocket connections
    if (url.protocol === 'ws:' || url.protocol === 'wss:') return;

    event.respondWith(
        caches.match(request).then((cachedResponse) => {
            // Return cached response if found
            if (cachedResponse) {
                // Fetch in background to update cache
                event.waitUntil(
                    fetch(request).then((response) => {
                        if (response.ok) {
                            caches.open(CACHE_NAME).then((cache) => {
                                cache.put(request, response);
                            });
                        }
                    }).catch(() => { })
                );
                return cachedResponse;
            }

            // Fetch from network
            return fetch(request)
                .then((response) => {
                    // Cache successful responses
                    if (response.ok && url.origin === self.location.origin) {
                        const responseToCache = response.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(request, responseToCache);
                        });
                    }
                    return response;
                })
                .catch(() => {
                    // Return offline fallback for navigation requests
                    if (request.mode === 'navigate') {
                        return caches.match('/new-ui/index.html');
                    }
                    return new Response('Offline', { status: 503 });
                });
        })
    );
});

// Handle push notifications (future)
self.addEventListener('push', (event) => {
    if (!event.data) return;

    const data = event.data.json();
    const options = {
        body: data.body || 'Yeni bildirim',
        icon: '/pwa/icon-192.png',
        badge: '/pwa/badge-72.png',
        vibrate: [100, 50, 100],
        data: {
            url: data.url || '/new-ui/',
        },
    };

    event.waitUntil(
        self.registration.showNotification(data.title || 'Mami AI', options)
    );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const url = event.notification.data?.url || '/new-ui/';

    event.waitUntil(
        clients.matchAll({ type: 'window' }).then((clientList) => {
            // Focus existing window if found
            for (const client of clientList) {
                if (client.url === url && 'focus' in client) {
                    return client.focus();
                }
            }
            // Open new window
            if (clients.openWindow) {
                return clients.openWindow(url);
            }
        })
    );
});

// Handle background sync (for offline messages)
self.addEventListener('sync', (event) => {
    if (event.tag === 'send-message') {
        console.log('[SW] Background sync: send-message');
        // TODO: Implement offline message queue
    }
});
