/**
 * LibSys Service Worker - Aggressive Caching & Offline Capabilities
 * OOG BOOG! CAVEMAN SERVICE WORKER CACHE ALL THE DATA FOR INSTANT LOAD TIMES!
 */
const CACHE_NAME = 'libsys-cache-v1';
const ASSETS_TO_CACHE = [
    '/',
    '/stock/',
    '/members/',
    '/contacts/',
    '/static/style.css',
    '/static/js/preload.js',
    'https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap'
];

// Install: Cache all core assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('[SW] OOG BOOG! Pre-caching core assets for LibSys!');
            return cache.addAll(ASSETS_TO_CACHE);
        })
    );
    self.skipWaiting();
});

// Activate: Clean up old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cache) => {
                    if (cache !== CACHE_NAME) {
                        console.log('[SW] Cleaning up legacy cache:', cache);
                        return caches.delete(cache);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// Fetch: Stale-While-Revalidate strategy for static resources, Network-First for HTML
self.addEventListener('fetch', (event) => {
    const request = event.request;
    const url = new URL(request.url);

    // Skip non-GET, Django admin panel, Django authentication, and REST APIs
    if (request.method !== 'GET' || 
        url.pathname.startsWith('/admin') || 
        url.pathname.startsWith('/api') || 
        url.pathname.startsWith('/users') ||
        url.pathname.startsWith('/register') || 
        url.pathname.startsWith('/dashboard') ||
        url.pathname.startsWith('/books')) {
        return;
    }

    // Network-First strategy for HTML pages (books, members, contacts, home)
    if (request.headers.get('accept').includes('text/html')) {
        event.respondWith(
            fetch(request)
                .then((response) => {
                    // Update cache dynamically
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(request, responseClone);
                    });
                    return response;
                })
                .catch(() => {
                    // Fallback to cache if network fails
                    return caches.match(request);
                })
        );
        return;
    }

    // Stale-While-Revalidate strategy for CSS, JS, Fonts, and Images
    event.respondWith(
        caches.match(request).then((cachedResponse) => {
            if (cachedResponse) {
                // Fetch in background to update cache
                fetch(request).then((networkResponse) => {
                    if (networkResponse.status === 200) {
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(request, networkResponse);
                        });
                    }
                });
                return cachedResponse;
            }

            return fetch(request).then((networkResponse) => {
                if (networkResponse.status === 200) {
                    const responseClone = networkResponse.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(request, responseClone);
                    });
                }
                return networkResponse;
            });
        })
    );
});
